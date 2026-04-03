#!/usr/bin/env python3
"""
Archive Unqualified Contacts — AI Sales OS

One-time (or periodic) script to archive contacts in Notion that do not meet
the qualification criteria:
  1. Must have a Contact Owner
  2. Must have been sent at least one email (Email Sent = true in Notion)

Contacts that fail either condition get Stage → "Archived".

Usage:
    python archive_unqualified.py              # archive all unqualified contacts
    python archive_unqualified.py --dry-run    # show what would be archived
    python archive_unqualified.py --limit 50   # limit to first N contacts
"""
import os
import sys
import json
import logging
import argparse
import time
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.dirname(__file__))
from notion_helpers import (
    NOTION_DATABASE_ID_CONTACTS,
    notion_request,
    update_page,
    rate_limiter,
    NOTION_BASE_URL,
)
from constants import FIELD_CONTACT_OWNER, FIELD_EMAIL_SENT, FIELD_STAGE

# ─── Logging ────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("archive_unqualified.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


# ─── Helpers ────────────────────────────────────────────────────────────────

def get_prop_text(page: dict, prop_name: str) -> str:
    """Extract text value from a Notion page property."""
    prop = page.get("properties", {}).get(prop_name, {})
    prop_type = prop.get("type", "")

    if prop_type == "select":
        sel = prop.get("select")
        return sel.get("name", "") if sel else ""
    elif prop_type == "rich_text":
        parts = prop.get("rich_text", [])
        return parts[0].get("plain_text", "") if parts else ""
    elif prop_type == "title":
        parts = prop.get("title", [])
        return parts[0].get("plain_text", "") if parts else ""
    return ""


def get_prop_checkbox(page: dict, prop_name: str) -> bool:
    """Extract checkbox value from a Notion page property."""
    prop = page.get("properties", {}).get(prop_name, {})
    return prop.get("checkbox", False)


def fetch_all_contacts_from_notion() -> list:
    """Fetch all contacts from Notion Contacts DB (paginated)."""
    all_pages = []
    has_more = True
    start_cursor = None

    while has_more:
        body = {"page_size": 100}
        if start_cursor:
            body["start_cursor"] = start_cursor

        rate_limiter.wait()
        resp = notion_request(
            "POST",
            f"{NOTION_BASE_URL}/databases/{NOTION_DATABASE_ID_CONTACTS}/query",
            json=body,
        )

        if resp and resp.status_code == 200:
            data = resp.json()
            all_pages.extend(data.get("results", []))
            has_more = data.get("has_more", False)
            start_cursor = data.get("next_cursor")
        else:
            logger.error(f"Notion query failed: {resp.status_code if resp else 'No response'}")
            break

        if len(all_pages) % 1000 == 0:
            logger.info(f"  Fetched {len(all_pages)} contacts so far...")

    logger.info(f"Total contacts fetched from Notion: {len(all_pages)}")
    return all_pages


# ─── Main Logic ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Archive unqualified contacts in Notion")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be archived without making changes")
    parser.add_argument("--limit", type=int, default=None, help="Limit to first N contacts to archive")
    args = parser.parse_args()

    logger.info("=" * 70)
    logger.info("ARCHIVE UNQUALIFIED CONTACTS")
    logger.info(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE'}")
    logger.info("=" * 70)

    # Fetch all contacts
    logger.info("Step 1: Fetching all contacts from Notion...")
    contacts = fetch_all_contacts_from_notion()

    # Identify unqualified contacts
    logger.info("Step 2: Evaluating qualification criteria...")
    to_archive = []
    already_archived = 0
    qualified = 0

    for page in contacts:
        stage = get_prop_text(page, FIELD_STAGE)

        # Skip already archived
        if stage.lower() == "archived":
            already_archived += 1
            continue

        owner = get_prop_text(page, FIELD_CONTACT_OWNER)
        email_sent = get_prop_checkbox(page, FIELD_EMAIL_SENT)

        has_owner = bool(owner and owner.strip())
        has_email = email_sent

        if has_owner and has_email:
            qualified += 1
        else:
            name = get_prop_text(page, "Full Name")
            reason = []
            if not has_owner:
                reason.append("no owner")
            if not has_email:
                reason.append("no email sent")

            to_archive.append({
                "page_id": page["id"],
                "name": name,
                "reason": ", ".join(reason),
                "current_stage": stage,
            })

    logger.info(f"\n📊 RESULTS:")
    logger.info(f"  Total contacts:     {len(contacts)}")
    logger.info(f"  Already archived:   {already_archived}")
    logger.info(f"  Qualified (keep):   {qualified}")
    logger.info(f"  To archive:         {len(to_archive)}")

    if not to_archive:
        logger.info("Nothing to archive. Done!")
        return

    # Apply limit
    if args.limit:
        to_archive = to_archive[:args.limit]
        logger.info(f"  Limited to first {args.limit} contacts")

    # Show breakdown by reason
    from collections import Counter
    reasons = Counter(c["reason"] for c in to_archive)
    logger.info(f"\n  Breakdown:")
    for reason, count in reasons.most_common():
        logger.info(f"    {reason}: {count}")

    if args.dry_run:
        logger.info(f"\n🔍 DRY RUN — showing first 20 contacts that would be archived:")
        for c in to_archive[:20]:
            logger.info(f"  [{c['current_stage'] or 'no stage'}] {c['name']} — {c['reason']}")
        logger.info(f"\nTotal: {len(to_archive)} contacts would be archived")
        return

    # Archive contacts
    logger.info(f"\nStep 3: Archiving {len(to_archive)} contacts (Stage → Archived)...")
    archived = 0
    errors = 0

    for i, c in enumerate(to_archive, 1):
        try:
            update_page(c["page_id"], {
                FIELD_STAGE: {"select": {"name": "Archived"}},
            })
            archived += 1
        except Exception as e:
            logger.error(f"Error archiving {c['name']}: {e}")
            errors += 1

        if i % 100 == 0:
            logger.info(f"  Progress: {i}/{len(to_archive)} (archived: {archived}, errors: {errors})")

    logger.info(f"\n✅ DONE: {archived} contacts archived, {errors} errors")

    # Save stats
    stats = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_contacts": len(contacts),
        "already_archived": already_archived,
        "qualified": qualified,
        "newly_archived": archived,
        "errors": errors,
    }
    stats_file = os.path.join(os.path.dirname(__file__), "archive_stats.json")
    with open(stats_file, "w") as f:
        json.dump(stats, f, indent=2)
    logger.info(f"Stats saved to {stats_file}")


if __name__ == "__main__":
    main()
