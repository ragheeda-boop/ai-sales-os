"""
fix_seniority.py — AI Sales OS
================================
One-time migration: "C suite" → "C-Suite" across all Contacts.

Usage:
    python fix_seniority.py              # dry-run (shows what would change)
    python fix_seniority.py --execute    # apply changes
    python fix_seniority.py --execute --batch-size 25  # custom batch size

Requirements:
    pip install requests python-dotenv
    NOTION_API_KEY and NOTION_DATABASE_ID_CONTACTS in env or .env
"""

import argparse
import logging
import os
import time
from datetime import datetime

import requests
from dotenv import load_dotenv

load_dotenv()

# ── Config ─────────────────────────────────────────────────────────────────
NOTION_API_KEY          = os.environ["NOTION_API_KEY"]
CONTACTS_DB_ID          = os.environ["NOTION_DATABASE_ID_CONTACTS"]
NOTION_VERSION          = "2022-06-28"
OLD_VALUE               = "C suite"
NEW_VALUE               = "C-Suite"
DEFAULT_BATCH_SIZE      = 50
RATE_LIMIT_DELAY        = 0.35   # seconds between Notion API writes
MAX_RETRIES             = 3

# ── Logging (fixed: use static filename instead of timestamped to prevent accumulation)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("fix_seniority.log"),
    ],
)
log = logging.getLogger(__name__)

HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": NOTION_VERSION,
}


def notion_request(method: str, url: str, **kwargs) -> dict:
    """Wrapper with retry + rate-limit handling."""
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


def fetch_c_suite_contacts() -> list[dict]:
    """Query Notion for all contacts with Seniority = 'C suite'."""
    url = f"https://api.notion.com/v1/databases/{CONTACTS_DB_ID}/query"
    payload = {
        "filter": {
            "property": "Seniority",
            "select": {"equals": OLD_VALUE},
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
        log.info(f"  Page {page_num}: fetched {len(batch)} records (total so far: {len(results)})")

        if not data.get("has_more"):
            break
        cursor = data.get("next_cursor")

    log.info(f"Total contacts with Seniority='{OLD_VALUE}': {len(results)}")
    return results


def update_seniority(page_id: str, name: str) -> bool:
    """Update a single contact's Seniority to C-Suite."""
    url = f"https://api.notion.com/v1/pages/{page_id}"
    payload = {
        "properties": {
            "Seniority": {"select": {"name": NEW_VALUE}}
        }
    }
    notion_request("PATCH", url, json=payload)
    return True


def run_migration(execute: bool, batch_size: int) -> dict:
    log.info("=" * 60)
    log.info(f"Seniority Migration: '{OLD_VALUE}' → '{NEW_VALUE}'")
    log.info(f"Mode: {'EXECUTE' if execute else 'DRY RUN'}")
    log.info("=" * 60)

    contacts = fetch_c_suite_contacts()
    total    = len(contacts)
    updated  = 0
    errors   = 0
    skipped  = 0

    if total == 0:
        log.info("✅ Nothing to do — no 'C suite' records found.")
        return {"total": 0, "updated": 0, "errors": 0}

    log.info(f"\nProcessing {total} records in batches of {batch_size}...")

    for i, contact in enumerate(contacts, 1):
        page_id = contact["id"]
        # Extract name safely
        title_prop = contact.get("properties", {}).get("Full Name", {})
        name_parts = title_prop.get("title", [])
        name = name_parts[0]["plain_text"] if name_parts else page_id

        if not execute:
            log.info(f"  [DRY RUN {i}/{total}] Would update: {name} ({page_id})")
            updated += 1
            continue

        try:
            update_seniority(page_id, name)
            log.info(f"  ✅ [{i}/{total}] Updated: {name}")
            updated += 1
        except Exception as e:
            log.error(f"  ❌ [{i}/{total}] FAILED: {name} ({page_id}) — {e}")
            errors += 1

        # Rate limiting: pause between writes, extra pause every batch_size
        time.sleep(RATE_LIMIT_DELAY)
        if i % batch_size == 0:
            log.info(f"  Batch pause after {i} records...")
            time.sleep(1.0)

    log.info("\n" + "=" * 60)
    log.info("MIGRATION COMPLETE")
    log.info(f"  Total found:   {total}")
    log.info(f"  Updated:       {updated}")
    log.info(f"  Errors:        {errors}")
    log.info(f"  Skipped:       {skipped}")
    if not execute:
        log.info("  ⚠️  DRY RUN — no changes written. Re-run with --execute to apply.")
    log.info("=" * 60)

    return {"total": total, "updated": updated, "errors": errors}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fix Seniority normalization in Notion Contacts DB")
    parser.add_argument("--execute",    action="store_true", help="Apply changes (default: dry-run)")
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE, help=f"Batch size (default: {DEFAULT_BATCH_SIZE})")
    args = parser.parse_args()

    result = run_migration(execute=args.execute, batch_size=args.batch_size)
    exit(0 if result["errors"] == 0 else 1)
