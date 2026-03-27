#!/usr/bin/env python3
"""
AI Sales OS — Action Ready Updater

Calculates and writes `Action Ready` (checkbox) for all scored contacts.
A contact is Action Ready ONLY if ALL conditions are met:
  1. Lead Score >= 50
  2. Do Not Call = False
  3. Outreach Status NOT in blocked set (Bounced, Do Not Contact, Bad Data)
  4. Stage is NOT "Customer" or "Churned"
  5. Has at least one contact method (email or phone)

Run after lead_score.py, before auto_tasks.py.

Usage:
    python action_ready_updater.py              # update all scored contacts
    python action_ready_updater.py --dry-run    # show what would change without writing
"""
import os
import sys
import logging
import time
import argparse
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.dirname(__file__))
from notion_helpers import (
    NOTION_DATABASE_ID_CONTACTS,
    update_page,
    rate_limiter,
    notion_request,
    NOTION_BASE_URL,
)
from constants import (
    FIELD_LEAD_SCORE, FIELD_ACTION_READY, FIELD_DO_NOT_CALL,
    FIELD_OUTREACH_STATUS, FIELD_STAGE, FIELD_EMAIL,
    FIELD_WORK_PHONE, FIELD_MOBILE_PHONE, FIELD_CORPORATE_PHONE,
    SCORE_WARM, OUTREACH_BLOCKED,
)

# ─── Config ──────────────────────────────────────────────────────────────────

MAX_WORKERS = 3
BLOCKED_STAGES = {"customer", "churned"}

# ─── Logging ─────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("action_ready.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


# ─── Fetch Scored Contacts ───────────────────────────────────────────────────

def fetch_scored_contacts() -> List[Dict]:
    """Fetch all contacts with Lead Score >= SCORE_WARM."""
    results = []
    cursor = None

    while True:
        body = {
            "page_size": 100,
            "filter": {
                "property": FIELD_LEAD_SCORE,
                "number": {"greater_than_or_equal_to": SCORE_WARM},
            },
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

        if len(results) % 500 == 0:
            logger.info(f"  Fetched {len(results)} contacts so far...")

    logger.info(f"Fetched {len(results)} scored contacts")
    return results


# ─── Evaluate Action Ready ───────────────────────────────────────────────────

def is_action_ready(props: Dict) -> bool:
    """Evaluate whether a contact should be Action Ready = True."""

    # 1. Score check (already filtered in query, but double-check)
    score = props.get(FIELD_LEAD_SCORE, {}).get("number", 0) or 0
    if score < SCORE_WARM:
        return False

    # 2. Do Not Call check
    dnc = props.get(FIELD_DO_NOT_CALL, {}).get("checkbox", False)
    if dnc:
        return False

    # 3. Outreach Status check
    outreach_sel = props.get(FIELD_OUTREACH_STATUS, {}).get("select")
    outreach = outreach_sel.get("name", "") if outreach_sel else ""
    if outreach in OUTREACH_BLOCKED:
        return False

    # 4. Stage check
    stage_sel = props.get(FIELD_STAGE, {}).get("select")
    stage = (stage_sel.get("name", "") if stage_sel else "").lower()
    if stage in BLOCKED_STAGES:
        return False

    # 5. Has contact method (email exists)
    email = props.get(FIELD_EMAIL, {}).get("email")
    has_phone = False
    for phone_field in [FIELD_WORK_PHONE, FIELD_MOBILE_PHONE, FIELD_CORPORATE_PHONE]:
        phone_val = props.get(phone_field, {}).get("phone_number")
        if phone_val:
            has_phone = True
            break
    if not email and not has_phone:
        return False

    return True


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="AI Sales OS — Action Ready Updater")
    parser.add_argument("--dry-run", action="store_true", help="Show changes without writing")
    args = parser.parse_args()

    logger.info("=" * 70)
    logger.info(f"ACTION READY UPDATER | Dry Run: {args.dry_run}")
    logger.info("=" * 70)

    start_time = time.time()

    contacts = fetch_scored_contacts()
    if not contacts:
        logger.info("No scored contacts found. Done!")
        return

    stats = {"set_true": 0, "set_false": 0, "unchanged": 0, "errors": 0}

    def process(page):
        props = page.get("properties", {})
        page_id = page["id"]

        should_be_ready = is_action_ready(props)
        current_ready = props.get(FIELD_ACTION_READY, {}).get("checkbox", False)

        if current_ready == should_be_ready:
            return "unchanged"

        if args.dry_run:
            name_items = props.get("Full Name", {}).get("title", [])
            name = name_items[0]["text"]["content"] if name_items else "?"
            score = props.get(FIELD_LEAD_SCORE, {}).get("number", 0)
            logger.info(f"  [DRY RUN] {name} (score={score:.0f}): Action Ready {current_ready} → {should_be_ready}")
            return "set_true" if should_be_ready else "set_false"

        try:
            update_page(page_id, {
                FIELD_ACTION_READY: {"checkbox": should_be_ready},
            })
            return "set_true" if should_be_ready else "set_false"
        except Exception as e:
            logger.error(f"Error updating {page_id}: {e}")
            return "error"

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(process, p): p for p in contacts}
        for i, fut in enumerate(as_completed(futures), 1):
            result = fut.result()
            stats[result] = stats.get(result, 0) + 1
            if i % 200 == 0:
                logger.info(f"  Progress: {i}/{len(contacts)}")

    elapsed = time.time() - start_time

    logger.info("=" * 70)
    logger.info(f"ACTION READY UPDATE COMPLETE")
    logger.info(f"  Set True:  {stats['set_true']}")
    logger.info(f"  Set False: {stats['set_false']}")
    logger.info(f"  Unchanged: {stats['unchanged']}")
    logger.info(f"  Errors:    {stats['errors']}")
    logger.info(f"  Time: {elapsed:.1f}s")
    logger.info("=" * 70)


if __name__ == "__main__":
    main()
