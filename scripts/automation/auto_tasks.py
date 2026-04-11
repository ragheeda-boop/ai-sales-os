#!/usr/bin/env python3
"""
AI Sales OS — Action Engine v2.0 (Company-Centric)

Creates tasks in Notion at the COMPANY level, not the Contact level.
One task per company per tier. Assigns to Primary Company Owner.

v2.0 Changes (Company-Centric):
- Groups contacts by company before task creation
- Creates ONE task per company (using highest-scored contact as representative)
- Deduplicates by Company + Task Type (not Contact)
- Assigns Task Owner = Primary Company Owner
- Tracks Owner Source for audit trail

Usage:
    python auto_tasks.py                    # create tasks for all eligible companies
    python auto_tasks.py --dry-run          # show what would be created without writing
    python auto_tasks.py --limit 20         # limit to first N companies (for testing)
    python auto_tasks.py --mark-overdue     # only check and log overdue tasks
"""
import sys as _sys, os as _os; _sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
import os
import sys
import json
import logging
import time
import argparse
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Set, Tuple
from collections import defaultdict
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.dirname(__file__))
from core.notion_helpers import (
    NOTION_DATABASE_ID_CONTACTS,
    rate_limiter,
    notion_request,
    NOTION_BASE_URL,
)
from core.constants import (
    FIELD_LEAD_SCORE, FIELD_LEAD_TIER, FIELD_ACTION_READY,
    FIELD_DO_NOT_CALL, FIELD_OUTREACH_STATUS, FIELD_SENIORITY,
    FIELD_COUNTRY, FIELD_FULL_NAME, FIELD_APOLLO_CONTACT_ID,
    FIELD_CONTACT_OWNER,
    FIELD_TASK_TITLE, FIELD_TASK_PRIORITY, FIELD_TASK_STATUS,
    FIELD_TASK_DUE_DATE, FIELD_TASK_TYPE, FIELD_TASK_CONTACT,
    FIELD_TASK_COMPANY, FIELD_TASK_CONTEXT, FIELD_TASK_DESCRIPTION,
    FIELD_TASK_EXPECTED_OUTCOME, FIELD_TASK_AUTO_CREATED,
    FIELD_TASK_AUTOMATION_TYPE, FIELD_TASK_TRIGGER_RULE,
    FIELD_TASK_OWNER, FIELD_OWNER_SOURCE, FIELD_COMPANY_STAGE_AT_CREATION,
    FIELD_PRIMARY_COMPANY_OWNER,
    TIER_HOT, TIER_WARM, TIER_COLD,
    SCORE_HOT, SCORE_WARM,
    SLA_HOT_HOURS, SLA_WARM_HIGH_HOURS, SLA_WARM_HOURS,
    OUTREACH_BLOCKED,
    # AI Sales Actions (Apollo-driven overrides)
    FIELD_AI_ACTION_TYPE, FIELD_AI_PRIORITY, FIELD_AI_URGENCY,
    FIELD_AI_SIGNAL, FIELD_AI_PAIN_SUMMARY, FIELD_AI_TARGET_ROLE,
    FIELD_AI_CALL_HOOK,
    AI_ACTION_CALL, AI_ACTION_EMAIL, AI_ACTION_SEQUENCE, AI_ACTION_NONE,
    AI_PRIORITY_P1, AI_PRIORITY_P2, AI_PRIORITY_P3,
)

# ── AI Priority → Task Priority map ──
AI_PRIORITY_TO_TASK_PRIORITY = {
    AI_PRIORITY_P1: "Critical",
    AI_PRIORITY_P2: "High",
    AI_PRIORITY_P3: "Medium",
}

# ─── Config ──────────────────────────────────────────────────────────────────

NOTION_DATABASE_ID_TASKS = os.getenv("NOTION_DATABASE_ID_TASKS")
NOTION_DATABASE_ID_COMPANIES = os.getenv("NOTION_DATABASE_ID_COMPANIES")
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
        # FIX C-03: "Urgent Call" is distinct from WARM's "Follow-up" so company-level
        # dedup doesn't block HOT tasks when a WARM task already exists for the same company.
        "task_type": "Urgent Call",
        "action": "CALL",
        "channel": "Phone",
        "sla_hours": SLA_HOT_HOURS,
        "title_template": "🔥 URGENT CALL: {company} — {name}",
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
        "title_template": "FOLLOW-UP: {company} — {name}",
        "expected_outcome": "Get a reply or schedule a call within 48 hours",
    },
]


def get_rule(score: float) -> Optional[Dict]:
    for rule in PRIORITY_RULES:
        if score >= rule["min_score"]:
            return rule
    return None


# ─── Fetch Action Ready Contacts ─────────────────────────────────────────────

def fetch_actionable_contacts() -> List[Dict]:
    """Fetch ALL contacts where Action Ready = True, sorted by Lead Score descending."""
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

        if not data.get("has_more"):
            break
        cursor = data.get("next_cursor")

    logger.info(f"Found {len(results)} Action Ready contacts")
    return results


# ─── Get Companies With Open Tasks (Company-Level Dedup) ─────────────────────

def get_companies_with_open_tasks() -> Dict[str, Set[str]]:
    """Return mapping of Company page ID → set of open Task Types.

    v2.0: Deduplicates at the COMPANY level, not contact level.
    A company that already has an open "Follow-up" task won't get another one.
    """
    if not NOTION_DATABASE_ID_TASKS:
        logger.warning("NOTION_DATABASE_ID_TASKS not set — skipping duplicate check")
        return {}

    # { company_page_id: set(task_type_1, task_type_2, ...) }
    company_tasks: Dict[str, Set[str]] = defaultdict(set)
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
            props = page.get("properties", {})

            # Get company relation
            company_rel = props.get(FIELD_TASK_COMPANY, {}).get("relation", [])
            for rel in company_rel:
                cid = rel.get("id")
                if cid:
                    # Get task type
                    task_type_sel = props.get(FIELD_TASK_TYPE, {}).get("select")
                    task_type = task_type_sel.get("name", "Unknown") if task_type_sel else "Unknown"
                    company_tasks[cid].add(task_type)

        if not data.get("has_more"):
            break
        cursor = data.get("next_cursor")

    total_companies = len(company_tasks)
    logger.info(f"Found {total_companies} companies with open tasks (will skip)")
    return dict(company_tasks)


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
        "contact_owner": get_text(FIELD_CONTACT_OWNER),
    }


# ─── Group Contacts by Company ──────────────────────────────────────────────

def group_contacts_by_company(contacts_info: List[Dict]) -> Dict[str, List[Dict]]:
    """Group contacts by their Company page ID.

    v2.0: This is the core of company-centric task creation.
    Returns: { company_page_id: [contact_info_1, contact_info_2, ...] }
    Contacts without a company are grouped under "NO_COMPANY".
    Each group is sorted by score descending (highest first).
    """
    groups: Dict[str, List[Dict]] = defaultdict(list)

    for info in contacts_info:
        company_id = info["company_ids"][0] if info["company_ids"] else "NO_COMPANY"
        groups[company_id].append(info)

    # Sort each group by score descending
    for company_id in groups:
        groups[company_id].sort(key=lambda x: x["score"], reverse=True)

    return dict(groups)


# ─── Preload Company Owners (FIX L-01: eliminates N+1 API calls) ────────────

def preload_company_owners(company_ids: Set[str]) -> Dict[str, Optional[str]]:
    """Preload Primary Company Owner for all relevant companies in ONE query pass.

    FIX L-01: Previously this was called per-company (N+1 pattern).
    Now we query the Companies DB once and build a lookup dict.

    Returns: { company_page_id: owner_name_or_None }
    """
    if not NOTION_DATABASE_ID_COMPANIES:
        logger.warning("NOTION_DATABASE_ID_COMPANIES not set — cannot preload owners")
        return {}

    owner_map: Dict[str, Optional[str]] = {}
    cursor = None
    loaded = 0

    logger.info("Preloading company owners from Notion Companies DB...")

    while True:
        body = {"page_size": 100}
        if cursor:
            body["start_cursor"] = cursor

        rate_limiter.wait()
        try:
            resp = notion_request(
                "POST",
                f"{NOTION_BASE_URL}/databases/{NOTION_DATABASE_ID_COMPANIES}/query",
                json=body,
            )
            data = resp.json()
        except Exception as e:
            logger.error(f"Error preloading company owners: {e}")
            break

        for page in data.get("results", []):
            page_id = page["id"]
            props = page.get("properties", {})
            owner_sel = props.get(FIELD_PRIMARY_COMPANY_OWNER, {}).get("select")
            owner_map[page_id] = owner_sel.get("name") if owner_sel else None
            loaded += 1

        if not data.get("has_more"):
            break
        cursor = data.get("next_cursor")

    logger.info(f"  Preloaded {loaded} company owner records")
    return owner_map


def preload_company_ai_fields(company_ids: Set[str]) -> Dict[str, Dict]:
    """Preload parsed AI Sales Actions fields for all relevant companies.

    Returns { company_page_id: {
        "ai_action_type": str,   # Call/Email/Sequence/None/""
        "ai_priority":    str,   # P1/P2/P3/""
        "ai_urgency":     str,
        "ai_signal":      str,
        "ai_pain":        str,
        "ai_target_role": str,
        "ai_call_hook":   str,
    } }

    Only includes companies that have at least one AI field populated.
    Bulk-queries the Companies DB once. Safe to call with an empty set.
    """
    ai_map: Dict[str, Dict] = {}
    if not company_ids or not NOTION_DATABASE_ID_COMPANIES:
        return ai_map

    def _select_val(props: Dict, field: str) -> str:
        sel = props.get(field, {}).get("select")
        return sel.get("name") if sel else ""

    def _rt_val(props: Dict, field: str) -> str:
        rt = props.get(field, {}).get("rich_text") or []
        return "".join(seg.get("plain_text", "") for seg in rt).strip()

    cursor = None
    loaded = 0
    logger.info("Preloading AI Sales Actions fields from Companies DB...")

    while True:
        body = {"page_size": 100}
        if cursor:
            body["start_cursor"] = cursor
        rate_limiter.wait()
        try:
            resp = notion_request(
                "POST",
                f"{NOTION_BASE_URL}/databases/{NOTION_DATABASE_ID_COMPANIES}/query",
                json=body,
            )
            data = resp.json()
        except Exception as e:
            logger.error(f"Error preloading AI fields: {e}")
            break

        for page in data.get("results", []):
            pid = page["id"]
            if pid not in company_ids:
                continue
            props = page.get("properties", {})
            entry = {
                "ai_action_type": _select_val(props, FIELD_AI_ACTION_TYPE),
                "ai_priority": _select_val(props, FIELD_AI_PRIORITY),
                "ai_urgency": _select_val(props, FIELD_AI_URGENCY),
                "ai_signal": _rt_val(props, FIELD_AI_SIGNAL),
                "ai_pain": _rt_val(props, FIELD_AI_PAIN_SUMMARY),
                "ai_target_role": _rt_val(props, FIELD_AI_TARGET_ROLE),
                "ai_call_hook": _rt_val(props, FIELD_AI_CALL_HOOK),
            }
            # Only keep if at least one field is populated
            if any(entry.values()):
                ai_map[pid] = entry
                loaded += 1

        if not data.get("has_more"):
            break
        cursor = data.get("next_cursor")

    logger.info(f"  Preloaded AI fields for {loaded} companies")
    return ai_map


def fetch_company_primary_owner(company_page_id: str) -> Optional[str]:
    """Fetch Primary Company Owner from a Company page in Notion.

    NOTE: This is the per-page fallback. Prefer preload_company_owners()
    in batch operations to avoid N+1 API calls.
    """
    if company_page_id == "NO_COMPANY":
        return None

    rate_limiter.wait()
    try:
        resp = notion_request("GET", f"{NOTION_BASE_URL}/pages/{company_page_id}")
        props = resp.json().get("properties", {})
        owner_sel = props.get(FIELD_PRIMARY_COMPANY_OWNER, {}).get("select")
        return owner_sel.get("name") if owner_sel else None
    except Exception as e:
        logger.warning(f"Could not fetch company owner for {company_page_id}: {e}")
        return None


# ─── Build Task Context ──────────────────────────────────────────────────────

def build_company_context(best_contact: Dict, all_contacts: List[Dict], rule: Dict) -> str:
    """Build context showing company-level information."""
    parts = [
        f"Best Contact: {best_contact['name']} (Score: {best_contact['score']:.0f})",
        f"Tier: {best_contact['tier'] or rule['tier']}",
        f"Total Contacts at Company: {len(all_contacts)}",
    ]
    if best_contact["seniority"]:
        parts.append(f"Seniority: {best_contact['seniority']}")
    parts.append(f"Action: {rule['action']} via {rule['channel']}")

    # List other contacts at same company
    if len(all_contacts) > 1:
        others = [f"{c['name']} ({c['score']:.0f})" for c in all_contacts[1:4]]
        parts.append(f"Other contacts: {', '.join(others)}")
        if len(all_contacts) > 4:
            parts.append(f"  (+{len(all_contacts) - 4} more)")

    return " | ".join(parts)


# ─── Create Task (Company-Centric) ──────────────────────────────────────────

def create_company_task(
    company_id: str,
    best_contact: Dict,
    all_contacts: List[Dict],
    rule: Dict,
    company_owner: Optional[str],
    ai_data: Optional[Dict] = None,
) -> Optional[str]:
    """Create a single task for a company, linked to the best contact.

    v2.0: Task is company-level. One task per company per tier.
    Task Owner = Primary Company Owner (or Contact Owner fallback).
    """
    if not NOTION_DATABASE_ID_TASKS:
        logger.error("NOTION_DATABASE_ID_TASKS not set!")
        return None

    due_date = (datetime.now(timezone.utc) + timedelta(hours=rule["sla_hours"])).strftime("%Y-%m-%d")
    company_name = best_contact["company_name"] or "Unknown"
    title = rule["title_template"].format(name=best_contact["name"], company=company_name)
    context = build_company_context(best_contact, all_contacts, rule)

    # Determine task owner: Primary Company Owner → Contact Owner → fallback
    task_owner = company_owner or best_contact.get("contact_owner") or None
    owner_source = "Company Primary" if company_owner else "Contact Owner"

    # ── AI Sales Actions override ──
    # AI Priority wins over score-based priority when present.
    # AI Call Hook / Signal / Pain / Target Role are appended to the task description
    # so the rep sees Apollo's reasoning alongside the scoring context.
    task_priority = rule["priority"]
    ai_desc_block = ""
    automation_type_value = "Lead Scoring"

    if ai_data:
        ai_priority = (ai_data.get("ai_priority") or "").strip()
        if ai_priority in AI_PRIORITY_TO_TASK_PRIORITY:
            task_priority = AI_PRIORITY_TO_TASK_PRIORITY[ai_priority]
            automation_type_value = "AI Sales Actions"

        # Build Apollo AI addendum for the description
        ai_lines: List[str] = []
        if ai_data.get("ai_action_type"):
            ai_lines.append(f"Apollo Action: {ai_data['ai_action_type']}")
        if ai_priority:
            ai_lines.append(f"Apollo Priority: {ai_priority}")
        if ai_data.get("ai_urgency"):
            ai_lines.append(f"Urgency: {ai_data['ai_urgency']}")
        if ai_data.get("ai_target_role"):
            ai_lines.append(f"Target Role: {ai_data['ai_target_role']}")
        if ai_data.get("ai_signal"):
            ai_lines.append(f"Signal: {ai_data['ai_signal']}")
        if ai_data.get("ai_pain"):
            ai_lines.append(f"Pain: {ai_data['ai_pain']}")
        if ai_data.get("ai_call_hook"):
            ai_lines.append("Call Hooks:\n" + ai_data["ai_call_hook"])
        if ai_lines:
            ai_desc_block = "\n\n── Apollo AI Sales Actions ──\n" + "\n".join(ai_lines)

    description_body = (
        f"Company-level task for {company_name}. "
        f"{len(all_contacts)} contact(s) qualify. "
        f"Best contact: {best_contact['name']} (Score: {best_contact['score']:.0f}, "
        f"Tier: {best_contact['tier'] or rule['tier']}). "
        f"Action: {rule['action']} via {rule['channel']}."
        f"{ai_desc_block}"
    )[:1990]

    props = {
        FIELD_TASK_TITLE: {"title": [{"text": {"content": title[:300]}}]},
        FIELD_TASK_PRIORITY: {"select": {"name": task_priority}},
        FIELD_TASK_STATUS: {"status": {"name": "Not Started"}},
        FIELD_TASK_DUE_DATE: {"date": {"start": due_date}},
        FIELD_TASK_TYPE: {"select": {"name": rule["task_type"]}},
        FIELD_TASK_CONTEXT: {"rich_text": [{"text": {"content": context[:2000]}}]},
        FIELD_TASK_DESCRIPTION: {"rich_text": [{"text": {"content": description_body}}]},
        FIELD_TASK_EXPECTED_OUTCOME: {"rich_text": [{"text": {"content": rule["expected_outcome"]}}]},
        FIELD_TASK_AUTO_CREATED: {"checkbox": True},
        FIELD_TASK_AUTOMATION_TYPE: {"select": {"name": automation_type_value}},
        FIELD_TASK_TRIGGER_RULE: {"rich_text": [{"text": {"content":
            f"Company-Centric v2.0: Best score >= {rule['min_score']} AND Action Ready = True"
        }}]},
        # Link to BEST contact (representative, not sole target)
        FIELD_TASK_CONTACT: {"relation": [{"id": best_contact["page_id"]}]},
    }

    # REQUIRED: Link to company
    if company_id and company_id != "NO_COMPANY":
        props[FIELD_TASK_COMPANY] = {"relation": [{"id": company_id}]}

    # Task Owner (v5.0)
    if task_owner:
        props[FIELD_TASK_OWNER] = {"select": {"name": task_owner}}
    if owner_source:
        props[FIELD_OWNER_SOURCE] = {"select": {"name": owner_source}}

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
        logger.error(f"Error creating task for company {company_name}: {e}")
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
    parser = argparse.ArgumentParser(description="AI Sales OS — Action Engine v2.0 (Company-Centric)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be created without writing")
    parser.add_argument("--limit", type=int, default=None, help="Limit to first N companies")
    parser.add_argument("--mark-overdue", action="store_true", help="Only check and mark overdue tasks")
    args = parser.parse_args()

    logger.info("=" * 70)
    logger.info(f"ACTION ENGINE v2.0 (Company-Centric) | Dry Run: {args.dry_run} | Limit: {args.limit or 'ALL'}")
    logger.info("=" * 70)

    start_time = time.time()

    # Step 0: Mark overdue tasks
    logger.info("Step 0: Checking overdue tasks...")
    mark_overdue_tasks()

    if args.mark_overdue:
        logger.info("--mark-overdue flag set, done.")
        return

    # Step 1: Fetch ALL actionable contacts
    logger.info("Step 1: Fetching Action Ready contacts...")
    raw_contacts = fetch_actionable_contacts()

    if not raw_contacts:
        logger.info("No Action Ready contacts found. Done!")
        return

    # Step 2: Extract info and filter
    logger.info("Step 2: Extracting contact info and filtering...")
    contacts_info = []
    filtered_blocked = 0

    for page in raw_contacts:
        info = extract_contact_info(page)

        # Skip DNC or blocked outreach
        if info["dnc"] or info["outreach_status"] in OUTREACH_BLOCKED:
            filtered_blocked += 1
            continue

        # Skip if no scoring rule applies
        rule = get_rule(info["score"])
        if not rule:
            continue

        contacts_info.append(info)

    logger.info(f"  {len(contacts_info)} contacts eligible ({filtered_blocked} blocked)")

    # Step 3: Group by company
    logger.info("Step 3: Grouping contacts by company...")
    company_groups = group_contacts_by_company(contacts_info)
    logger.info(f"  {len(company_groups)} unique companies")

    # Step 4: Get companies with existing open tasks (company-level dedup)
    logger.info("Step 4: Checking existing open tasks (company-level dedup)...")
    open_company_tasks = get_companies_with_open_tasks()

    # Step 4b: Preload ALL company owners in ONE query (FIX L-01: eliminates N+1)
    logger.info("Step 4b: Preloading company owners (single-pass bulk fetch)...")
    all_company_ids = {cid for cid in company_groups.keys() if cid != "NO_COMPANY"}
    company_owner_cache: Dict[str, Optional[str]] = {}
    company_ai_cache: Dict[str, Dict] = {}
    if not args.dry_run and all_company_ids:
        company_owner_cache = preload_company_owners(all_company_ids)
        logger.info(f"  Owner cache: {sum(1 for v in company_owner_cache.values() if v)} assigned, "
                    f"{sum(1 for v in company_owner_cache.values() if not v)} unassigned")
        # Step 4c: Preload parsed AI Sales Actions fields
        company_ai_cache = preload_company_ai_fields(all_company_ids)

    # Step 5: Create ONE task per company
    logger.info("Step 5: Creating company-level tasks...")
    stats = {
        "companies_processed": 0,
        "tasks_created": 0,
        "skipped_open_task": 0,
        "skipped_no_company": 0,
        "skipped_ai_action_none": 0,
        "ai_overrides_applied": 0,
        "errors": 0,
        "contacts_covered": 0,
    }

    companies_processed = 0
    for company_id, company_contacts in company_groups.items():
        if args.limit and companies_processed >= args.limit:
            break

        # Best contact = highest score in this company (already sorted)
        best = company_contacts[0]
        rule = get_rule(best["score"])
        if not rule:
            continue

        # Company-level dedup: check if company already has open task of this type
        if company_id in open_company_tasks:
            existing_types = open_company_tasks[company_id]
            if rule["task_type"] in existing_types:
                stats["skipped_open_task"] += 1
                continue

        # Skip contacts with no company link
        if company_id == "NO_COMPANY":
            stats["skipped_no_company"] += len(company_contacts)
            continue

        # ── AI Sales Actions gating ──
        # If Apollo's AI has explicitly set Action Type = None for this company,
        # respect that and skip task creation entirely. Non-Call actions (Email /
        # Sequence) are routed through auto_sequence.py — not the call-task engine —
        # so auto_tasks only creates tasks when: (a) no AI data, OR (b) AI says Call.
        ai_data = company_ai_cache.get(company_id)
        if ai_data:
            ai_action = (ai_data.get("ai_action_type") or "").strip()
            if ai_action == AI_ACTION_NONE:
                stats["skipped_ai_action_none"] += 1
                continue
            # Email/Sequence → auto_sequence handles it. auto_tasks only fires on Call
            # or when no AI direction is given (fall back to score-tier rule).
            if ai_action in (AI_ACTION_EMAIL, AI_ACTION_SEQUENCE) and rule["tier"] != TIER_HOT:
                # HOT score still gets a call task regardless (high-urgency override)
                stats["skipped_ai_action_none"] += 1
                continue
            if ai_data.get("ai_priority"):
                stats["ai_overrides_applied"] += 1

        companies_processed += 1
        stats["companies_processed"] += 1
        stats["contacts_covered"] += len(company_contacts)

        # Resolve Primary Company Owner from preloaded cache (FIX L-01: O(1) lookup, not N API calls)
        company_owner = company_owner_cache.get(company_id) if not args.dry_run else None

        if args.dry_run:
            company_name = best["company_name"] or "Unknown"
            title = rule["title_template"].format(name=best["name"], company=company_name)
            logger.info(
                f"  [DRY RUN] Would create: {title} | "
                f"Score: {best['score']:.0f} | Priority: {rule['priority']} | "
                f"Contacts at company: {len(company_contacts)}"
            )
            stats["tasks_created"] += 1
            continue

        page_id = create_company_task(
            company_id, best, company_contacts, rule, company_owner,
            ai_data=company_ai_cache.get(company_id),
        )
        if page_id:
            stats["tasks_created"] += 1
            logger.info(
                f"  Task created: {best['company_name'] or 'Unknown'} | "
                f"Best: {best['name']} ({best['score']:.0f}) | "
                f"{rule['tier']} | {len(company_contacts)} contacts"
            )
        else:
            stats["errors"] += 1

    elapsed = time.time() - start_time

    logger.info("=" * 70)
    logger.info(f"ACTION ENGINE v2.0 COMPLETE (Company-Centric)")
    logger.info(f"  Companies processed:   {stats['companies_processed']}")
    logger.info(f"  Tasks created:         {stats['tasks_created']}")
    logger.info(f"  Contacts covered:      {stats['contacts_covered']}")
    logger.info(f"  Skipped (open task):   {stats['skipped_open_task']}")
    logger.info(f"  Skipped (no company):  {stats['skipped_no_company']}")
    logger.info(f"  Skipped (AI=None/Email/Seq): {stats['skipped_ai_action_none']}")
    logger.info(f"  AI priority overrides: {stats['ai_overrides_applied']}")
    logger.info(f"  Errors:                {stats['errors']}")
    logger.info(f"  Time:                  {elapsed:.1f}s")
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
