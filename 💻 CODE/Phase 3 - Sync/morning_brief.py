#!/usr/bin/env python3
"""
AI Sales OS — Morning Brief Generator

Daily intelligence report: What happened overnight, what needs attention today.

Sections:
  1. Urgent Calls: HOT leads not yet contacted
  2. Today's Tasks: Due today or overdue
  3. New HOT Leads: Recently scored HOT
  4. Recent Replies: Contacts that responded
  5. Pipeline Summary: HOT/WARM/COLD counts
  6. Quick Stats: Emails sent, reply rate from Apollo

Usage:
    python morning_brief.py                 # generate today's brief
    python morning_brief.py --output file   # save to markdown file
    python morning_brief.py --days 1        # look back N days for new activity
"""
import os
import sys
import json
import logging
import time
import argparse
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
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
    FIELD_FULL_NAME, FIELD_SENIORITY, FIELD_EMAIL,
    FIELD_OUTREACH_STATUS, FIELD_LAST_CONTACTED,
    FIELD_REPLIED, FIELD_MEETING_BOOKED, FIELD_CONTACT_RESPONDED,
    FIELD_TASK_TITLE, FIELD_TASK_PRIORITY, FIELD_TASK_STATUS,
    FIELD_TASK_DUE_DATE, FIELD_TASK_CONTACT,
    TIER_HOT, TIER_WARM, TIER_COLD,
    SCORE_HOT, SCORE_WARM,
)

# ─── Config ──────────────────────────────────────────────────────────────────

NOTION_DATABASE_ID_TASKS = os.getenv("NOTION_DATABASE_ID_TASKS")
APOLLO_API_KEY = os.getenv("APOLLO_API_KEY")
APOLLO_BASE_URL = "https://api.apollo.io/api/v1"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# ─── Logging ─────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("morning_brief.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


# ─── Data Collection ─────────────────────────────────────────────────────────

def fetch_hot_leads_not_contacted() -> List[Dict]:
    """HOT leads that haven't been contacted yet — urgent calls."""
    results = []
    cursor = None

    while True:
        body = {
            "page_size": 100,
            "filter": {
                "and": [
                    {"property": FIELD_LEAD_TIER, "select": {"equals": TIER_HOT}},
                    {"property": FIELD_ACTION_READY, "checkbox": {"equals": True}},
                    {"property": FIELD_OUTREACH_STATUS, "select": {"is_empty": True}},
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
            logger.error(f"Error: {e}")
            break

        for page in data.get("results", []):
            props = page.get("properties", {})
            name_items = props.get(FIELD_FULL_NAME, {}).get("title", [])
            name = name_items[0]["text"]["content"] if name_items else "Unknown"
            score = props.get(FIELD_LEAD_SCORE, {}).get("number", 0) or 0
            seniority_sel = props.get(FIELD_SENIORITY, {}).get("select")
            seniority = seniority_sel.get("name", "") if seniority_sel else ""

            results.append({"name": name, "score": score, "seniority": seniority})

        if not data.get("has_more"):
            break
        cursor = data.get("next_cursor")

        if len(results) >= 50:  # Cap for the brief
            break

    return results


def fetch_todays_tasks() -> Dict:
    """Tasks due today or overdue."""
    if not NOTION_DATABASE_ID_TASKS:
        return {"due_today": [], "overdue": []}

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    due_today = []
    overdue = []
    cursor = None

    while True:
        body = {
            "page_size": 100,
            "filter": {
                "and": [
                    {"property": FIELD_TASK_STATUS, "status": {"does_not_equal": "Completed"}},
                    {"property": FIELD_TASK_DUE_DATE, "date": {"on_or_before": today}},
                ]
            },
            "sorts": [{"property": FIELD_TASK_PRIORITY, "direction": "ascending"}],
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
            title_items = props.get(FIELD_TASK_TITLE, {}).get("title", [])
            title = title_items[0]["text"]["content"] if title_items else "Unknown"
            priority_sel = props.get(FIELD_TASK_PRIORITY, {}).get("select")
            priority = priority_sel.get("name", "") if priority_sel else ""
            due_date_prop = props.get(FIELD_TASK_DUE_DATE, {}).get("date")
            due_date = due_date_prop.get("start", "") if due_date_prop else ""

            task = {"title": title, "priority": priority, "due_date": due_date}

            if due_date < today:
                overdue.append(task)
            else:
                due_today.append(task)

        if not data.get("has_more"):
            break
        cursor = data.get("next_cursor")

    return {"due_today": due_today, "overdue": overdue}


def fetch_recent_replies(days: int = 1) -> List[Dict]:
    """Contacts that replied recently."""
    results = []
    cursor = None

    while True:
        body = {
            "page_size": 100,
            "filter": {
                "and": [
                    {"property": FIELD_REPLIED, "checkbox": {"equals": True}},
                    {"property": FIELD_CONTACT_RESPONDED, "checkbox": {"equals": True}},
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
            logger.error(f"Error: {e}")
            break

        for page in data.get("results", []):
            props = page.get("properties", {})
            name_items = props.get(FIELD_FULL_NAME, {}).get("title", [])
            name = name_items[0]["text"]["content"] if name_items else "Unknown"
            score = props.get(FIELD_LEAD_SCORE, {}).get("number", 0) or 0
            tier_sel = props.get(FIELD_LEAD_TIER, {}).get("select")
            tier = tier_sel.get("name", "") if tier_sel else ""

            results.append({"name": name, "score": score, "tier": tier})

        if not data.get("has_more"):
            break
        cursor = data.get("next_cursor")

        if len(results) >= 30:
            break

    return results


def fetch_pipeline_counts() -> Dict[str, int]:
    """Count contacts by Lead Tier."""
    counts = {"HOT": 0, "WARM": 0, "COLD": 0, "total_scored": 0}

    for tier_name in [TIER_HOT, TIER_WARM, TIER_COLD]:
        cursor = None
        tier_count = 0

        while True:
            body = {
                "page_size": 100,
                "filter": {"property": FIELD_LEAD_TIER, "select": {"equals": tier_name}},
            }
            if cursor:
                body["start_cursor"] = cursor

            rate_limiter.wait()
            try:
                resp = notion_request("POST", f"{NOTION_BASE_URL}/databases/{NOTION_DATABASE_ID_CONTACTS}/query", json=body)
                data = resp.json()
            except Exception:
                break

            tier_count += len(data.get("results", []))

            if not data.get("has_more"):
                break
            cursor = data.get("next_cursor")

        counts[tier_name] = tier_count
        counts["total_scored"] += tier_count

    return counts


def fetch_apollo_quick_stats() -> Dict:
    """Quick email stats from Apollo."""
    import requests

    try:
        resp = requests.post(
            f"{APOLLO_BASE_URL}/analytics/sync_report",
            json={
                "api_key": APOLLO_API_KEY,
                "metrics": [
                    "num_emails_sent", "num_emails_replied",
                    "percent_emails_replied", "num_contacts_replied",
                ],
                "date_range": {"modality": "last_7_days"},
            },
            timeout=30,
        )
        data = resp.json()
        rows = data.get("rows", [])
        if rows:
            return {
                "emails_sent_7d": rows[0].get("num_emails_sent", 0),
                "emails_replied_7d": rows[0].get("num_emails_replied", 0),
                "reply_rate_7d": rows[0].get("percent_emails_replied", 0),
                "contacts_replied_7d": rows[0].get("num_contacts_replied", 0),
            }
    except Exception as e:
        logger.warning(f"Could not fetch Apollo stats: {e}")

    return {"emails_sent_7d": 0, "emails_replied_7d": 0, "reply_rate_7d": 0, "contacts_replied_7d": 0}


# ─── Brief Generation ────────────────────────────────────────────────────────

def generate_brief(days: int = 1) -> str:
    """Generate the morning brief markdown."""
    now = datetime.now()
    brief = []

    brief.append(f"# AI Sales OS — Morning Brief")
    brief.append(f"**{now.strftime('%A, %B %d, %Y')}** | Generated at {now.strftime('%H:%M')}")
    brief.append("")

    # 1. Urgent Calls
    logger.info("Collecting urgent calls...")
    hot_not_contacted = fetch_hot_leads_not_contacted()
    brief.append(f"## Urgent Calls ({len(hot_not_contacted)})")
    if hot_not_contacted:
        brief.append("HOT leads that haven't been contacted yet:")
        brief.append("")
        for lead in hot_not_contacted[:15]:
            brief.append(f"- **{lead['name']}** — Score: {lead['score']:.0f} | {lead['seniority']}")
    else:
        brief.append("All HOT leads have been contacted.")
    brief.append("")

    # 2. Today's Tasks
    logger.info("Collecting today's tasks...")
    tasks = fetch_todays_tasks()
    overdue = tasks["overdue"]
    due_today = tasks["due_today"]
    brief.append(f"## Today's Tasks ({len(due_today)} due today, {len(overdue)} overdue)")
    if overdue:
        brief.append("**OVERDUE:**")
        for t in overdue[:10]:
            brief.append(f"- [{t['priority']}] {t['title']} (due: {t['due_date']})")
    if due_today:
        brief.append("**Due Today:**")
        for t in due_today[:10]:
            brief.append(f"- [{t['priority']}] {t['title']}")
    if not overdue and not due_today:
        brief.append("No tasks due today.")
    brief.append("")

    # 3. Recent Replies
    logger.info("Collecting recent replies...")
    replies = fetch_recent_replies(days=days)
    brief.append(f"## Recent Replies ({len(replies)})")
    if replies:
        for r in replies[:10]:
            brief.append(f"- **{r['name']}** — {r['tier']} | Score: {r['score']:.0f}")
    else:
        brief.append("No new replies detected.")
    brief.append("")

    # 4. Pipeline Summary
    logger.info("Collecting pipeline counts...")
    counts = fetch_pipeline_counts()
    brief.append(f"## Pipeline Summary")
    brief.append(f"- **HOT:** {counts['HOT']} contacts")
    brief.append(f"- **WARM:** {counts['WARM']} contacts")
    brief.append(f"- **COLD:** {counts['COLD']} contacts")
    brief.append(f"- **Total Scored:** {counts['total_scored']}")
    brief.append("")

    # 5. Apollo Stats (last 7 days)
    logger.info("Collecting Apollo stats...")
    stats = fetch_apollo_quick_stats()
    brief.append(f"## Email Performance (Last 7 Days)")
    brief.append(f"- **Emails Sent:** {stats['emails_sent_7d']}")
    brief.append(f"- **Replies:** {stats['emails_replied_7d']}")
    brief.append(f"- **Reply Rate:** {stats['reply_rate_7d']:.1f}%")
    brief.append(f"- **Unique Contacts Replied:** {stats['contacts_replied_7d']}")
    brief.append("")

    brief.append("---")
    brief.append(f"*Generated by AI Sales OS Morning Brief v1.0*")

    return "\n".join(brief)


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="AI Sales OS — Morning Brief")
    parser.add_argument("--output", choices=["file", "stdout"], default="stdout", help="Output destination")
    parser.add_argument("--days", type=int, default=1, help="Look back N days for activity")
    args = parser.parse_args()

    logger.info("=" * 70)
    logger.info(f"MORNING BRIEF GENERATOR | Days: {args.days}")
    logger.info("=" * 70)

    start_time = time.time()

    brief = generate_brief(days=args.days)

    if args.output == "file":
        filename = f"morning_brief_{datetime.now().strftime('%Y%m%d')}.md"
        filepath = os.path.join(SCRIPT_DIR, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(brief)
        logger.info(f"Brief saved to {filepath}")
    else:
        # Print to stdout
        print("\n" + brief)

    elapsed = time.time() - start_time
    logger.info(f"Morning Brief generated in {elapsed:.1f}s")


if __name__ == "__main__":
    main()
