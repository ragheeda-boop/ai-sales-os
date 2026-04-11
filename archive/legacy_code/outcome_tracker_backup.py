"""
outcome_tracker.py — AI Sales OS
===================================
Closes the Task → Contact → Result loop.

For every completed Task in the Tasks DB:
  1. Finds the linked Contact
  2. Sets Contact Responded = True
  3. Sets Last Contacted = task completion date (or today)
  4. If task title contains meeting keywords → sets Meeting Booked = True

Idempotent: skips contacts already updated, unless --force is passed.

Usage:
    python outcome_tracker.py              # dry-run
    python outcome_tracker.py --execute    # apply changes
    python outcome_tracker.py --execute --force     # re-process already-updated
    python outcome_tracker.py --execute --limit 20  # test with 20 tasks first

Env vars required (.env or environment):
    NOTION_API_KEY
    NOTION_DATABASE_ID_TASKS     = 5644e28ae9c9422b90e210df500ad607
    NOTION_DATABASE_ID_CONTACTS  = 9ca842d20aa9460bbdd958d0aa940d9c
"""

import argparse
import json
import logging
import os
import time
from datetime import datetime, timezone

import requests
from dotenv import load_dotenv

load_dotenv()

# ── Config ───────────────────────────────────────────────────────────────────
NOTION_API_KEY   = os.environ["NOTION_API_KEY"]
TASKS_DB_ID      = os.getenv("NOTION_DATABASE_ID_TASKS", "5644e28ae9c9422b90e210df500ad607")
CONTACTS_DB_ID   = os.getenv("NOTION_DATABASE_ID_CONTACTS", "9ca842d20aa9460bbdd958d0aa940d9c")
NOTION_VERSION   = "2022-06-28"
RATE_LIMIT_DELAY = 0.35
MAX_RETRIES      = 3

# Keywords in task title that imply a meeting happened
MEETING_KEYWORDS = {"meeting", "demo", "discovery", "presentation", "call scheduled"}

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f"outcome_tracker_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
    ],
)
log = logging.getLogger(__name__)

HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": NOTION_VERSION,
}


def notion_request(method: str, url: str, **kwargs) -> dict:
    for attempt in range(1, MAX_RETRIES + 1):
        resp = requests.request(method, url, headers=HEADERS, **kwargs)
        if resp.status_code == 429:
            retry_after = int(resp.headers.get("Retry-After", 2))
            log.warning(f"Rate limited — waiting {retry_after}s (attempt {attempt})")
            time.sleep(retry_after)
            continue
        resp.raise_for_status()
        return resp.json()
    raise RuntimeError(f"Failed after {MAX_RETRIES} retries: {url}")


def fetch_completed_tasks(limit: int | None = None) -> list[dict]:
    """Fetch all tasks with Status = Completed from Tasks DB."""
    url = f"https://api.notion.com/v1/databases/{TASKS_DB_ID}/query"
    # Tasks DB uses status type — filter uses {"status": {"equals": ...}}
    payload = {
        "filter": {
            "property": "Status",
            "status": {"equals": "Completed"},
        },
        "page_size": 100,
    }
    results = []
    cursor = None
    page_num = 0

    while True:
        page_num += 1
        if cursor:
            payload["start_cursor"] = cursor
        data = notion_request("POST", url, json=payload)
        batch = data.get("results", [])
        results.extend(batch)
        log.info(f"  Tasks page {page_num}: {len(batch)} records (total: {len(results)})")

        if limit and len(results) >= limit:
            results = results[:limit]
            log.info(f"  Limit={limit} reached — stopping fetch")
            break

        if not data.get("has_more"):
            break
        cursor = data.get("next_cursor")

    log.info(f"Total completed tasks: {len(results)}")
    return results


def extract_task_info(task: dict) -> dict:
    props = task.get("properties", {})

    # Title
    title_parts = props.get("Task Title", {}).get("title", [])
    title = title_parts[0]["plain_text"] if title_parts else ""

    # Contact relation
    contact_relations = props.get("Contact", {}).get("relation", [])
    contact_id = contact_relations[0]["id"] if contact_relations else None

    # Completed At date → fallback to last_edited_time → fallback to today
    completed_at = props.get("Completed At", {}).get("date", {}) or {}
    completed_date = completed_at.get("start")
    if not completed_date:
        completed_date = task.get("last_edited_time", datetime.now(timezone.utc).isoformat())
    # Keep only date portion YYYY-MM-DD
    completed_date = completed_date[:10]

    # Call Outcome field — if "Meeting Scheduled" → also flag meeting
    call_outcome_obj = props.get("Call Outcome", {}).get("select") or {}
    call_outcome = call_outcome_obj.get("name", "").lower()

    # Meeting detection: title keywords OR Call Outcome = Meeting Scheduled
    title_lower = title.lower()
    is_meeting = (
        any(kw in title_lower for kw in MEETING_KEYWORDS)
        or call_outcome == "meeting scheduled"
    )

    return {
        "task_id":        task["id"],
        "title":          title,
        "contact_id":     contact_id,
        "completed_date": completed_date,
        "is_meeting":     is_meeting,
        "call_outcome":   call_outcome,
    }


def fetch_contact(contact_id: str) -> dict:
    return notion_request("GET", f"https://api.notion.com/v1/pages/{contact_id}")


def contact_already_updated(contact: dict) -> bool:
    props = contact.get("properties", {})
    responded = props.get("Contact Responded", {}).get("checkbox", False)
    last_contacted = props.get("Last Contacted", {}).get("date")
    return responded and last_contacted is not None


def get_contact_name(contact: dict) -> str:
    try:
        parts = contact["properties"]["Full Name"]["title"]
        return parts[0]["plain_text"] if parts else contact["id"]
    except Exception:
        return contact.get("id", "unknown")


def update_contact(contact_id: str, completed_date: str, is_meeting: bool) -> None:
    properties = {
        "Contact Responded": {"checkbox": True},
        "Last Contacted": {"date": {"start": completed_date}},
    }
    if is_meeting:
        properties["Meeting Booked"] = {"checkbox": True}
    notion_request("PATCH", f"https://api.notion.com/v1/pages/{contact_id}",
                   json={"properties": properties})


def run(execute: bool, force: bool, limit: int | None) -> dict:
    log.info("=" * 60)
    log.info("outcome_tracker.py — Task → Contact → Result")
    log.info(f"Mode:  {'EXECUTE' if execute else 'DRY RUN'}")
    log.info(f"Force: {force} | Limit: {limit or 'all'}")
    log.info(f"Tasks DB:    {TASKS_DB_ID}")
    log.info(f"Contacts DB: {CONTACTS_DB_ID}")
    log.info("=" * 60)

    tasks = fetch_completed_tasks(limit=limit)

    stats = dict(tasks_fetched=len(tasks), tasks_processed=0,
                 contacts_updated=0, meetings_flagged=0,
                 skipped_no_contact=0, skipped_already=0, errors=0)

    for i, task in enumerate(tasks, 1):
        info = extract_task_info(task)
        prefix = f"[{i}/{stats['tasks_fetched']}]"

        if not info["contact_id"]:
            log.debug(f"{prefix} SKIP no-contact — {info['title']!r}")
            stats["skipped_no_contact"] += 1
            continue

        log.info(f"{prefix} \"{info['title']}\" | contact={info['contact_id']} | meeting={info['is_meeting']}")

        if not execute:
            action = f"Contact Responded=True, Last Contacted={info['completed_date']}"
            if info["is_meeting"]:
                action += ", Meeting Booked=True"
            log.info(f"  [DRY RUN] Would: {action}")
            stats["contacts_updated"] += 1
            if info["is_meeting"]:
                stats["meetings_flagged"] += 1
            stats["tasks_processed"] += 1
            continue

        # Fetch contact for idempotency check
        try:
            contact = fetch_contact(info["contact_id"])
        except Exception as e:
            log.error(f"  ❌ fetch failed: {e}")
            stats["errors"] += 1
            continue

        if not force and contact_already_updated(contact):
            log.info(f"  ↩️  already updated: {get_contact_name(contact)}")
            stats["skipped_already"] += 1
            time.sleep(0.1)
            continue

        try:
            update_contact(info["contact_id"], info["completed_date"], info["is_meeting"])
            log.info(f"  ✅ updated: {get_contact_name(contact)}")
            stats["contacts_updated"] += 1
            if info["is_meeting"]:
                stats["meetings_flagged"] += 1
            stats["tasks_processed"] += 1
        except Exception as e:
            log.error(f"  ❌ update failed: {e}")
            stats["errors"] += 1

        time.sleep(RATE_LIMIT_DELAY)

    stats["executed"] = execute
    stats["timestamp"] = datetime.now(timezone.utc).isoformat()

    log.info("\n" + "=" * 60)
    log.info("COMPLETE")
    for k, v in stats.items():
        log.info(f"  {k}: {v}")
    if not execute:
        log.info("  ⚠️  DRY RUN — re-run with --execute to apply")
    log.info("=" * 60)

    with open("last_outcome_stats.json", "w") as f:
        json.dump(stats, f, indent=2)

    return stats


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--execute", action="store_true")
    ap.add_argument("--force",   action="store_true")
    ap.add_argument("--limit",   type=int, default=None)
    args = ap.parse_args()
    result = run(execute=args.execute, force=args.force, limit=args.limit)
    exit(0 if result["errors"] == 0 else 1)
