#!/usr/bin/env python3
"""
cleanup_overdue_tasks.py — Bulk complete overdue auto-created tasks.

These are legacy tasks from the pre-v5.0 contact-level Action Engine.
They were never acted on and are now replaced by company-level tasks.

Usage:
    python cleanup_overdue_tasks.py --dry-run    # preview only
    python cleanup_overdue_tasks.py              # execute cleanup
    python cleanup_overdue_tasks.py --limit 100  # limit batch size
"""

import os
import sys
import json
import time
import logging
import argparse
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
log = logging.getLogger(__name__)

NOTION_API_KEY = os.getenv("NOTION_API_KEY")
TASKS_DB = os.getenv("NOTION_DATABASE_ID_TASKS")

HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json",
}

TODAY = datetime.now().strftime("%Y-%m-%d")


def fetch_overdue_tasks(limit=None):
    """Fetch all overdue, non-completed, auto-created tasks."""
    body = {
        "filter": {
            "and": [
                {"property": "Status", "status": {"does_not_equal": "Completed"}},
                {"property": "Due Date", "date": {"before": TODAY}},
                {"property": "Auto Created", "checkbox": {"equals": True}},
            ]
        },
        "sorts": [{"property": "Due Date", "direction": "ascending"}],
        "page_size": 100,
    }

    all_tasks = []
    has_more = True
    start_cursor = None
    page = 0

    while has_more:
        if start_cursor:
            body["start_cursor"] = start_cursor

        resp = requests.post(
            f"https://api.notion.com/v1/databases/{TASKS_DB}/query",
            headers=HEADERS,
            json=body,
        )

        if resp.status_code == 429:
            retry = int(resp.headers.get("Retry-After", 2))
            log.warning(f"Rate limited, waiting {retry}s...")
            time.sleep(retry)
            continue

        resp.raise_for_status()
        data = resp.json()
        results = data.get("results", [])
        all_tasks.extend(results)
        has_more = data.get("has_more", False)
        start_cursor = data.get("next_cursor")
        page += 1

        if page % 10 == 0:
            log.info(f"  Fetched {len(all_tasks)} tasks so far...")

        if limit and len(all_tasks) >= limit:
            all_tasks = all_tasks[:limit]
            break

        time.sleep(0.34)

    return all_tasks


def complete_task(task_id, retries=3):
    """Mark a single task as Completed with today's completion date."""
    body = {
        "properties": {
            "Status": {"status": {"name": "Completed"}},
            "Completed At": {"date": {"start": TODAY}},
            "Outcome Notes": {
                "rich_text": [
                    {
                        "text": {
                            "content": "Auto-closed: legacy pre-v5.0 overdue task"
                        }
                    }
                ]
            },
        }
    }

    for attempt in range(retries):
        resp = requests.patch(
            f"https://api.notion.com/v1/pages/{task_id}",
            headers=HEADERS,
            json=body,
        )

        if resp.status_code == 200:
            return True
        elif resp.status_code == 429:
            retry = int(resp.headers.get("Retry-After", 2))
            time.sleep(retry)
        else:
            log.error(f"Failed to update {task_id}: {resp.status_code} {resp.text[:200]}")
            if attempt < retries - 1:
                time.sleep(1)

    return False


def main():
    parser = argparse.ArgumentParser(description="Cleanup overdue auto-created tasks")
    parser.add_argument("--dry-run", action="store_true", help="Preview only, no changes")
    parser.add_argument("--limit", type=int, default=None, help="Max tasks to process")
    args = parser.parse_args()

    log.info("=" * 60)
    log.info(f"OVERDUE TASK CLEANUP | Dry Run: {args.dry_run} | Limit: {args.limit or 'ALL'}")
    log.info("=" * 60)

    log.info("Fetching overdue auto-created tasks...")
    tasks = fetch_overdue_tasks(limit=args.limit)
    log.info(f"Found {len(tasks)} overdue auto-created tasks")

    if not tasks:
        log.info("Nothing to clean up!")
        return

    # Summarize
    priorities = {}
    months = {}
    for t in tasks:
        props = t["properties"]
        p = props.get("Priority", {}).get("select")
        pname = p["name"] if p else "None"
        priorities[pname] = priorities.get(pname, 0) + 1

        dd = props.get("Due Date", {}).get("date")
        if dd and dd.get("start"):
            m = dd["start"][:7]
            months[m] = months.get(m, 0) + 1

    log.info(f"\n--- Breakdown ---")
    log.info(f"  Priority: {priorities}")
    log.info(f"  Months: {dict(sorted(months.items()))}")

    if args.dry_run:
        log.info(f"\n[DRY RUN] Would mark {len(tasks)} tasks as Completed.")
        log.info("Run without --dry-run to execute.")
        return

    # Execute cleanup
    log.info(f"\nMarking {len(tasks)} tasks as Completed...")
    completed = 0
    failed = 0
    start_time = time.time()

    for i, task in enumerate(tasks):
        task_id = task["id"]
        title_parts = task["properties"].get("Task Title", {}).get("title", [])
        title = title_parts[0]["plain_text"] if title_parts else "Untitled"

        success = complete_task(task_id)
        if success:
            completed += 1
        else:
            failed += 1

        if (i + 1) % 100 == 0:
            elapsed = time.time() - start_time
            rate = (i + 1) / elapsed * 60
            log.info(f"  Progress: {i + 1}/{len(tasks)} ({completed} completed, {failed} failed) | {rate:.0f}/min")

        time.sleep(0.34)  # Rate limit: ~3 req/sec

    elapsed = time.time() - start_time
    log.info("=" * 60)
    log.info(f"CLEANUP COMPLETE")
    log.info(f"  Completed: {completed}")
    log.info(f"  Failed:    {failed}")
    log.info(f"  Time:      {elapsed:.0f}s ({elapsed/60:.1f}min)")
    log.info("=" * 60)

    # Save stats
    stats = {
        "date": TODAY,
        "total_found": len(tasks),
        "completed": completed,
        "failed": failed,
        "elapsed_seconds": round(elapsed),
    }
    with open("cleanup_stats.json", "w") as f:
        json.dump(stats, f, indent=2)
    log.info(f"Stats saved to cleanup_stats.json")


if __name__ == "__main__":
    main()
