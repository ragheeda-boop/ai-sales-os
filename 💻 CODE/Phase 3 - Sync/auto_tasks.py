#!/usr/bin/env python3
"""
AI Sales OS — Action Engine (auto_tasks.py)

Creates tasks in Notion for Action Ready contacts based on Lead Tier.
Prevents duplicates, respects DNC, enforces SLA deadlines.

Usage:
    python auto_tasks.py                    # create tasks for all Action Ready contacts
    python auto_tasks.py --dry-run          # show what would be created without writing
    python auto_tasks.py --limit 20         # limit to first N contacts (for testing)
    python auto_tasks.py --mark-overdue     # only mark existing overdue tasks
"""
import os
import sys
import json
import logging
import time
import argparse
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Set
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.dirname(__file__))
from notion_helpers import (
    NOTION_DATABASE_ID_CONTACTS,
    rate_limiter,
    notion_request,
    NOTION_BASE_URL,
)
from constants import (
    FIELD_LEAD_SCORE, FIELD_LEAD_TIER, FIELD_ACTION_READY,
    FIELD_DO_NOT_CALL, FIELD_OUTREACH_STATUS, FIELD_SENIORITY,
    FIELD_COUNTRY, FIELD_FULL_NAME, FIELD_APOLLO_CONTACT_ID,
    FIELD_TASK_TITLE, FIELD_TASK_PRIORITY, FIELD_TASK_STATUS,
    FIELD_TASK_DUE_DATE, FIELD_TASK_TYPE, FIELD_TASK_CONTACT,
    FIELD_TASK_COMPANY, FIELD_TASK_CONTEXT, FIELD_TASK_DESCRIPTION,
    FIELD_TASK_EXPECTED_OUTCOME, FIELD_TASK_AUTO_CREATED,
    FIELD_TASK_AUTOMATION_TYPE, FIELD_TASK_TRIGGER_RULE,
    TIER_HOT, TIER_WARM, TIER_COLD,
    SCORE_HOT, SCORE_WARM,
    SLA_HOT_HOURS, SLA_WARM_HIGH_HOURS, SLA_WARM_HOURS,
    OUTREACH_BLOCKED,
)

# ─── Config ──────────────────────────────────────────────────────────────────

NOTION_DATABASE_ID_TASKS = os.getenv("NOTION_DATABASE_ID_TASKS")
MAX_WORKERS = 3

# ─── Logging ─────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("auto_tasks.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)

# ─── Priority Rules ──────────────────────────────────────────────────────────

PRIORITY_RULES = [
    {
        "tier": TIER_HOT,
        "min_score": SCORE_HOT,
        "priority": "Critical",
        "task_type": "Follow-up",
        "action": "CALL",
        "channel": "Phone",
        "sla_hours": SLA_HOT_HOURS,
        "title_template": "CALL: {name} — {company}",
        "expected_outcome": "Schedule a meeting or demo within 24 hours",
    },
    {
        "tier": TIER_WARM,
        "min_score": SCORE_WARM,
        "priority": "High",
        "task_type": "Follow-up",
        "action": "FOLLOW-UP",
        "channel": "Email",
        "sla_hours": SLA_WARM_HIGH_HOURS,
        "title_template": "FOLLOW-UP: {name} — {company}",
        "expected_outcome": "Get a reply or schedule a call within 48 hours",
    },
]


def get_rule(score: float) -> Optional[Dict]:
    for rule in PRIORITY_RULES:
        if score >= rule["min_score"]:
            return rule
    return None


# ─── Fetch Action Ready Contacts ─────────────────────────────────────────────

def fetch_actionable_contacts(limit: Optional[int] = None) -> List[Dict]:
    """Fetch contacts where Action Ready = True, sorted by Lead Score descending."""
    results = []
    cursor = None

    while True:
        body = {
            "page_size": 100,
            "filter": {
                "and": [
                    {"property": FIELD_ACTION_READY, "checkbox": {"equals": True}},
                    {"property": FIELD_LEAD_SCORE, "number": {"greater_than_or_equal_to": SCORE_WARM}},
                ]
            },
            "sorts": [{"property": FIELD_LEAD_SCORE, "direction": "descending"}],
        }
        if cursor:
            body["start_cursor"] = cursor

        rate_limiter.wait()
        try:
            resp = notion_request("POST", f"{NOTION_BASE_URL}/databases/{NOTION_DATABASE_ID_CONTACTS}/query", json=body)
            data = resp.json()
        except Exception as e:
            logger.error(f"Error fetching contacts: {e}")
            break

        results.extend(data.get("results", []))

        if limit and len(results) >= limit:
            results = results[:limit]
            break

        if not data.get("has_more"):
            break
        cursor = data.get("next_cursor")

    logger.info(f"Found {len(results)} Action Ready contacts")
    return results


# ─── Get Contacts With Open Tasks ─────────────────────────────────────────────

def get_contacts_with_open_tasks() -> Set[str]:
    """Return set of Contact page IDs that already have an open task."""
    if not NOTION_DATABASE_ID_TASKS:
        logger.warning("NOTION_DATABASE_ID_TASKS not set — skipping duplicate check")
        return set()

    open_ids = set()
    cursor = None

    while True:
        body = {
            "page_size": 100,
            "filter": {
                "property": FIELD_TASK_STATUS,
                "status": {"does_not_equal": "Completed"},
            },
        }
        if cursor:
            body["start_cursor"] = cursor

        rate_limiter.wait()
        try:
            resp = notion_request("POST", f"{NOTION_BASE_URL}/databases/{NOTION_DATABASE_ID_TASKS}/query", json=body)
            data = resp.json()
        except Exception as e:
            logger.error(f"Error fetching tasks: {e}")
            break

        for page in data.get("results", []):
            contact_rel = page.get("properties", {}).get(FIELD_TASK_CONTACT, {}).get("relation", [])
            for rel in contact_rel:
                if rel.get("id"):
                    open_ids.add(rel["id"])

        if not data.get("has_more"):
            break
        cursor = data.get("next_cursor")

    logger.info(f"Found {len(open_ids)} contacts with open tasks (will skip)")
    return open_ids


# ─── Extract Contact Fields ──────────────────────────────────────────────────

def extract_contact_info(page: Dict) -> Dict:
    """Extract relevant fields from a Notion contact page."""
    props = page.get("properties", {})

    def get_title(p):
        items = props.get(p, {}).get("title", [])
        return items[0]["text"]["content"] if items else ""

    def get_text(p):
        items = props.get(p, {}).get("rich_text", [])
        return items[0]["text"]["content"] if items else ""

    def get_select(p):
        sel = props.get(p, {}).get("select")
        return sel.get("name") if sel else ""

    def get_number(p):
        return props.get(p, {}).get("number", 0) or 0

    def get_checkbox(p):
        return props.get(p, {}).get("checkbox", False)

    def get_relation_ids(p):
        return [r["id"] for r in props.get(p, {}).get("relation", []) if r.get("id")]

    return {
        "page_id": page["id"],
        "name": get_title(FIELD_FULL_NAME),
        "score": get_number(FIELD_LEAD_SCORE),
        "tier": get_select(FIELD_LEAD_TIER),
        "seniority": get_select(FIELD_SENIORITY),
        "country": get_text(FIELD_COUNTRY) if props.get(FIELD_COUNTRY, {}).get("type") == "rich_text" else get_select(FIELD_COUNTRY),
        "outreach_status": get_select(FIELD_OUTREACH_STATUS),
        "dnc": get_checkbox(FIELD_DO_NOT_CALL),
        "company_ids": get_relation_ids("Company"),
        "company_name": get_text("Company Name for Emails"),
    }


# ─── Build Task Context ──────────────────────────────────────────────────────

def build_context(info: Dict, rule: Dict) -> str:
    """Build a human-readable explanation of why this task was created."""
    parts = [
        f"Lead Score: {info['score']:.0f}/100",
        f"Tier: {info['tier'] or rule['tier']}",
    ]
    if info["seniority"]:
        parts.append(f"Seniority: {info['seniority']}")
    if info["country"]:
        parts.append(f"Country: {info['country']}")
    if info["outreach_status"]:
        parts.append(f"Outreach: {info['outreach_status']}")
    parts.append(f"Action: {rule['action']} via {rule['channel']}")
    return " | ".join(parts)


# ─── Create Task ─────────────────────────────────────────────────────────────

def create_task(info: Dict, rule: Dict) -> Optional[str]:
    """Create a task in Notion Tasks DB. Returns page_id or None."""
    if not NOTION_DATABASE_ID_TASKS:
        logger.error("NOTION_DATABASE_ID_TASKS not set!")
        return None

    due_date = (datetime.now(timezone.utc) + timedelta(hours=rule["sla_hours"])).strftime("%Y-%m-%d")
    company_name = info["company_name"] or "Unknown"
    title = rule["title_template"].format(name=info["name"], company=company_name)
    context = build_context(info, rule)

    props = {
        FIELD_TASK_TITLE: {"title": [{"text": {"content": title[:300]}}]},
        FIELD_TASK_PRIORITY: {"select": {"name": rule["priority"]}},
        FIELD_TASK_STATUS: {"status": {"name": "Not Started"}},
        FIELD_TASK_DUE_DATE: {"date": {"start": due_date}},
        FIELD_TASK_TYPE: {"select": {"name": rule["task_type"]}},
        FIELD_TASK_CONTEXT: {"rich_text": [{"text": {"content": context[:2000]}}]},
        FIELD_TASK_DESCRIPTION: {"rich_text": [{"text": {"content": f"Auto-generated task for {info['tier'] or rule['tier']} lead. Action: {rule['action']} via {rule['channel']}."}}]},
        FIELD_TASK_EXPECTED_OUTCOME: {"rich_text": [{"text": {"content": rule["expected_outcome"]}}]},
        FIELD_TASK_AUTO_CREATED: {"checkbox": True},
        FIELD_TASK_AUTOMATION_TYPE: {"select": {"name": "Lead Scoring"}},
        FIELD_TASK_TRIGGER_RULE: {"rich_text": [{"text": {"content": f"Score >= {rule['min_score']} AND Action Ready = True"}}]},
        FIELD_TASK_CONTACT: {"relation": [{"id": info["page_id"]}]},
    }

    # Link to company if available
    if info["company_ids"]:
        props[FIELD_TASK_COMPANY] = {"relation": [{"id": info["company_ids"][0]}]}

    rate_limiter.wait()
    try:
        resp = notion_request(
            "POST",
            f"{NOTION_BASE_URL}/pages",
            json={"parent": {"database_id": NOTION_DATABASE_ID_TASKS}, "properties": props},
        )
        result = resp.json()
        return result.get("id")
    except Exception as e:
        logger.error(f"Error creating task for {info['name']}: {e}")
        return None


# ─── Mark Overdue Tasks ──────────────────────────────────────────────────────

def mark_overdue_tasks():
    """Find tasks past due date and log them as overdue."""
    if not NOTION_DATABASE_ID_TASKS:
        return

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    cursor = None
    overdue_count = 0

    while True:
        body = {
            "page_size": 100,
            "filter": {
                "and": [
                    {"property": FIELD_TASK_STATUS, "status": {"does_not_equal": "Completed"}},
                    {"property": FIELD_TASK_DUE_DATE, "date": {"before": today}},
                ]
            },
        }
        if cursor:
            body["start_cursor"] = cursor

        rate_limiter.wait()
        try:
            resp = notion_request("POST", f"{NOTION_BASE_URL}/databases/{NOTION_DATABASE_ID_TASKS}/query", json=body)
            data = resp.json()
        except Exception as e:
            logger.error(f"Error checking overdue tasks: {e}")
            break

        overdue_count += len(data.get("results", []))

        if not data.get("has_more"):
            break
        cursor = data.get("next_cursor")

    if overdue_count > 0:
        logger.warning(f"  {overdue_count} overdue tasks found (past due date, not completed)")
    else:
        logger.info("  No overdue tasks")


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="AI Sales OS — Action Engine")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be created without writing")
    parser.add_argument("--limit", type=int, default=None, help="Limit to first N contacts")
    parser.add_argument("--mark-overdue", action="store_true", help="Only check and mark overdue tasks")
    args = parser.parse_args()

    logger.info("=" * 70)
    logger.info(f"ACTION ENGINE | Dry Run: {args.dry_run} | Limit: {args.limit or 'ALL'}")
    logger.info("=" * 70)

    start_time = time.time()

    # Mark overdue tasks
    logger.info("Step 0: Checking overdue tasks...")
    mark_overdue_tasks()

    if args.mark_overdue:
        logger.info("--mark-overdue flag set, done.")
        return

    # Step 1: Fetch actionable contacts
    logger.info("Step 1: Fetching Action Ready contacts...")
    contacts = fetch_actionable_contacts(limit=args.limit)

    if not contacts:
        logger.info("No Action Ready contacts found. Done!")
        return

    # Step 2: Get contacts with open tasks (to prevent duplicates)
    logger.info("Step 2: Checking for existing open tasks...")
    open_task_contacts = get_contacts_with_open_tasks()

    # Step 3: Create tasks
    logger.info("Step 3: Creating tasks...")
    stats = {"created": 0, "skipped_open_task": 0, "skipped_blocked": 0, "skipped_no_rule": 0, "errors": 0}

    for contact_page in contacts:
        info = extract_contact_info(contact_page)

        # Skip if DNC
        if info["dnc"]:
            stats["skipped_blocked"] += 1
            continue

        # Skip if outreach status is blocked
        if info["outreach_status"] in OUTREACH_BLOCKED:
            stats["skipped_blocked"] += 1
            continue

        # Skip if already has open task
        if info["page_id"] in open_task_contacts:
            stats["skipped_open_task"] += 1
            continue

        # Get priority rule
        rule = get_rule(info["score"])
        if not rule:
            stats["skipped_no_rule"] += 1
            continue

        if args.dry_run:
            company = info["company_name"] or "Unknown"
            title = rule["title_template"].format(name=info["name"], company=company)
            logger.info(f"  [DRY RUN] Would create: {title} | Score: {info['score']:.0f} | Priority: {rule['priority']}")
            stats["created"] += 1
            continue

        page_id = create_task(info, rule)
        if page_id:
            stats["created"] += 1
            logger.info(f"  Task created: {info['name']} | Score: {info['score']:.0f} | {rule['tier']}")
        else:
            stats["errors"] += 1

    elapsed = time.time() - start_time

    logger.info("=" * 70)
    logger.info(f"ACTION ENGINE COMPLETE")
    logger.info(f"  Created: {stats['created']}")
    logger.info(f"  Skipped (open task): {stats['skipped_open_task']}")
    logger.info(f"  Skipped (blocked/DNC): {stats['skipped_blocked']}")
    logger.info(f"  Skipped (no rule): {stats['skipped_no_rule']}")
    logger.info(f"  Errors: {stats['errors']}")
    logger.info(f"  Time: {elapsed:.1f}s")
    logger.info("=" * 70)

    # Save stats for health_check
    stats_file = os.path.join(os.path.dirname(__file__), "last_action_stats.json")
    try:
        with open(stats_file, "w") as f:
            json.dump(stats, f, indent=2)
    except Exception:
        pass


if __name__ == "__main__":
    main()
