"""
outcome_tracker.py — AI Sales OS v1.0
========================================
Closes the Task → Contact → Result loop.

For every REAL completed Task (not auto-closed bulk tasks):
  1. Finds the linked Contact
  2. Sets Contact Responded = True
  3. Sets Last Contacted = task completion date (or today)
  4. If Call Outcome = "Meeting Scheduled" → sets Meeting Booked = True

Idempotent: skips contacts already updated, unless --force is passed.

Usage:
    python outcome_tracker.py                    # dry-run (safe, no writes)
    python outcome_tracker.py --execute          # apply changes
    python outcome_tracker.py --execute --force  # re-process already-updated
    python outcome_tracker.py --execute --limit 20          # test first 20
    python outcome_tracker.py --execute --include-auto-closed  # include bulk-closed

Env vars required (.env or environment):
    NOTION_API_KEY
    NOTION_DATABASE_ID_TASKS     (default: 5644e28ae9c9422b90e210df500ad607)
    NOTION_DATABASE_ID_CONTACTS  (default: 9ca842d20aa9460bbdd958d0aa940d9c)
"""

import argparse
import json
import logging
import os
import time
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler

import requests
from dotenv import load_dotenv

load_dotenv()


# ── Config ─────────────────────────────────────────────────────────────────

def _require_env(name: str) -> str:
    """Fail loudly if a required env var is missing (FIX C-05: no hardcoded fallbacks)."""
    val = os.getenv(name)
    if not val:
        raise EnvironmentError(
            f"Required env var {name!r} is not set. "
            f"Add it to your .env file or GitHub Secrets."
        )
    return val


NOTION_API_KEY   = _require_env("NOTION_API_KEY")
TASKS_DB_ID      = _require_env("NOTION_DATABASE_ID_TASKS")
CONTACTS_DB_ID   = _require_env("NOTION_DATABASE_ID_CONTACTS")
NOTION_VERSION   = "2022-06-28"
RATE_LIMIT_DELAY = 0.35   # seconds between API writes
MAX_RETRIES      = 3

# Marker used by bulk auto-close script
AUTO_CLOSE_MARKER = "auto-closed"

HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": NOTION_VERSION,
}

# ── Logging (FIX C-06: RotatingFileHandler instead of timestamped files) ────
# Previously a new timestamped log was created on every run (outcome_tracker_YYYYMMDD_HHMMSS.log),
# causing unbounded file accumulation. Now a fixed file with rotation is used.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        RotatingFileHandler(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "outcome_tracker.log"),
            maxBytes=5 * 1024 * 1024,  # 5 MB per file
            backupCount=3,              # keep .log, .log.1, .log.2, .log.3
            encoding="utf-8",
        ),
    ],
)
log = logging.getLogger(__name__)


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


def fetch_completed_tasks(limit: int | None = None, include_auto_closed: bool = False) -> list[dict]:
    """Fetch completed tasks. By default skips auto-closed bulk tasks."""
    url = f"https://api.notion.com/v1/databases/{TASKS_DB_ID}/query"
    payload = {
        "filter": {
            "property": "Status",
            "status": {"equals": "Completed"},
        },
        "page_size": 100,
    }
    all_results = []
    cursor = None
    page_num = 0

    while True:
        page_num += 1
        if cursor:
            payload["start_cursor"] = cursor
        data = notion_request("POST", url, json=payload)
        batch = data.get("results", [])

        # Filter out auto-closed tasks unless explicitly included
        if not include_auto_closed:
            real_batch = []
            for t in batch:
                outcome_notes = t.get("properties", {}).get("Outcome Notes", {}).get("rich_text", [])
                notes_text = outcome_notes[0]["plain_text"] if outcome_notes else ""
                if AUTO_CLOSE_MARKER.lower() not in notes_text.lower():
                    real_batch.append(t)
            filtered = len(batch) - len(real_batch)
            if filtered > 0:
                log.info(f"  Page {page_num}: {len(batch)} total, {filtered} auto-closed skipped, {len(real_batch)} real")
            batch = real_batch
        else:
            log.info(f"  Page {page_num}: {len(batch)} tasks (including auto-closed)")

        all_results.extend(batch)

        if limit and len(all_results) >= limit:
            all_results = all_results[:limit]
            break

        if not data.get("has_more"):
            break
        cursor = data.get("next_cursor")

    log.info(f"Fetched {len(all_results)} tasks to process")
    return all_results


def extract_task_info(task: dict) -> dict:
    props = task.get("properties", {})

    # Title
    title_parts = props.get("Task Title", {}).get("title", [])
    title = title_parts[0]["plain_text"] if title_parts else ""

    # Contact
    contacts = props.get("Contact", {}).get("relation", [])
    contact_id = contacts[0]["id"] if contacts else None

    # Completion date
    completed_at = props.get("Completed At", {}).get("date") or {}
    completed_date = completed_at.get("start")
    if not completed_date:
        completed_date = task.get("last_edited_time", datetime.now(timezone.utc).isoformat())
    completed_date = completed_date[:10]

    # Call Outcome
    call_outcome_sel = props.get("Call Outcome", {}).get("select") or {}
    call_outcome = call_outcome_sel.get("name", "")

    # Meeting flag: Call Outcome = Meeting Scheduled
    is_meeting = call_outcome == "Meeting Scheduled"

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
        "Last Contacted":    {"date": {"start": completed_date}},
    }
    if is_meeting:
        properties["Meeting Booked"] = {"checkbox": True}
    notion_request("PATCH", f"https://api.notion.com/v1/pages/{contact_id}",
                   json={"properties": properties})


def run(execute: bool, force: bool, limit: int | None, include_auto_closed: bool) -> dict:
    log.info("=" * 60)
    log.info("outcome_tracker.py — Task → Contact → Result")
    log.info(f"Mode:              {'EXECUTE' if execute else 'DRY RUN'}")
    log.info(f"Force:             {force}")
    log.info(f"Limit:             {limit or 'all'}")
    log.info(f"Include auto-closed: {include_auto_closed}")
    log.info(f"Tasks DB:    {TASKS_DB_ID}")
    log.info(f"Contacts DB: {CONTACTS_DB_ID}")
    log.info("=" * 60)

    tasks = fetch_completed_tasks(limit=limit, include_auto_closed=include_auto_closed)

    stats = {
        "tasks_fetched": len(tasks),
        "tasks_processed": 0,
        "contacts_updated": 0,
        "meetings_flagged": 0,
        "skipped_no_contact": 0,
        "skipped_already_done": 0,
        "errors": 0,
    }

    for i, task in enumerate(tasks, 1):
        info = extract_task_info(task)
        pfx  = f"[{i}/{stats['tasks_fetched']}]"

        if not info["contact_id"]:
            log.debug(f"{pfx} SKIP no-contact: {info['title']!r}")
            stats["skipped_no_contact"] += 1
            continue

        log.info(f"{pfx} \"{info['title']}\" | call_outcome={info['call_outcome']!r} | meeting={info['is_meeting']}")

        if not execute:
            action = f"Contact Responded=True, Last Contacted={info['completed_date']}"
            if info["is_meeting"]:
                action += ", Meeting Booked=True"
            log.info(f"  [DRY RUN] Would set: {action}")
            stats["contacts_updated"] += 1
            if info["is_meeting"]:
                stats["meetings_flagged"] += 1
            stats["tasks_processed"] += 1
            continue

        # Idempotency
        try:
            contact = fetch_contact(info["contact_id"])
        except Exception as e:
            log.error(f"  ❌ fetch contact failed: {e}")
            stats["errors"] += 1
            continue

        if not force and contact_already_updated(contact):
            log.info(f"  ↩️  already updated: {get_contact_name(contact)}")
            stats["skipped_already_done"] += 1
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

    stats["executed"]  = execute
    stats["timestamp"] = datetime.now(timezone.utc).isoformat()

    log.info("\n" + "=" * 60)
    log.info("OUTCOME TRACKER COMPLETE")
    for k, v in stats.items():
        log.info(f"  {k}: {v}")
    if not execute:
        log.info("  ⚠️  DRY RUN — no writes. Add --execute to apply.")
    log.info("=" * 60)

    # Write stats file next to this script (scripts/automation/), not CWD.
    # Bare relative path caused the file to land wherever the process was
    # launched from, so the workflow upload step (expecting
    # scripts/automation/last_outcome_stats.json) never found it — which in
    # turn broke the v6.1 freshness guard in data_governor (Decision #29).
    stats_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "last_outcome_stats.json",
    )
    with open(stats_path, "w") as f:
        json.dump(stats, f, indent=2)
    log.info(f"Stats → {stats_path}")

    return stats


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Outcome Tracker — closes Task→Contact loop")
    ap.add_argument("--execute",              action="store_true", help="Apply changes (default: dry-run)")
    ap.add_argument("--force",                action="store_true", help="Re-process already-updated contacts")
    ap.add_argument("--limit",                type=int, default=None, help="Max tasks to process")
    ap.add_argument("--include-auto-closed",  action="store_true", help="Include bulk auto-closed tasks")
    args = ap.parse_args()

    result = run(
        execute=args.execute,
        force=args.force,
        limit=args.limit,
        include_auto_closed=args.include_auto_closed,
    )
    exit(0 if result["errors"] == 0 else 1)
