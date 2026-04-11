#!/usr/bin/env python3
"""
notion_engineering_sync.py
==========================
Phase 2: Sync cleaned engineering offices to Notion DB

Reads:   cleaned_offices.json (output of clean_engineering_offices.py)
Writes:  Notion DB "مكاتب هندسية - وزارة الاسكان"
         ID: b85c24be6aa941a395dc33fd1c5f566a

Logic:
  1. Pre-load all existing Notion pages (by CR, Email, Name)
  2. For each record: UPDATE if exists, CREATE if new
  3. Skip records already in Notion with no data change
  4. Rate-limit safe: exponential backoff on 429s

Run:
    python notion_engineering_sync.py
    python notion_engineering_sync.py --dry-run
    python notion_engineering_sync.py --limit 50
    python notion_engineering_sync.py --force-update   # update even if unchanged
"""

import json, os, sys, time, argparse, logging
from pathlib import Path
from datetime import datetime

import requests
from dotenv import load_dotenv

from constants_eng import (
    NOTION_DB_ID,
    F_NAME, F_REGION, F_CITY, F_CR, F_EMAIL, F_MOBILE, F_WA,
    F_SOURCE, F_COMPLETENESS, F_STATUS, F_MANUAL_NOTE,
    F_MISS_EMAIL, F_MISS_MOBILE, F_DUP_SUSPECTED, F_MANUAL_REVIEW, F_READY,
    F_FOLLOWUP_STAGE, F_PRIORITY,
)

# ───────────────────────────────────────────────
# Logging
# ───────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("notion_engineering_sync.log", encoding="utf-8"),
    ],
)
log = logging.getLogger(__name__)

# ───────────────────────────────────────────────
# Load env
# ───────────────────────────────────────────────

load_dotenv(Path(__file__).parent / ".env")
NOTION_TOKEN = os.getenv("NOTION_API_KEY") or os.getenv("NOTION_TOKEN")
if not NOTION_TOKEN:
    sys.exit("❌  NOTION_API_KEY not set in .env")

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json",
}

# ───────────────────────────────────────────────
# Notion API helpers
# ───────────────────────────────────────────────

def _request(method: str, url: str, **kwargs) -> dict:
    """Make a Notion API request with exponential backoff."""
    for attempt in range(6):
        resp = requests.request(method, url, headers=HEADERS, **kwargs)
        if resp.status_code == 429:
            wait = 2 ** attempt
            log.warning(f"Rate limited — waiting {wait}s (attempt {attempt+1})")
            time.sleep(wait)
            continue
        if resp.status_code >= 500:
            wait = 2 ** attempt
            log.warning(f"Server error {resp.status_code} — waiting {wait}s")
            time.sleep(wait)
            continue
        resp.raise_for_status()
        return resp.json()
    raise RuntimeError(f"Failed after 6 attempts: {url}")


def query_all(database_id: str, filter_payload: dict = None) -> list[dict]:
    """Paginate through all pages in a Notion database."""
    pages, cursor = [], None
    while True:
        body = {"page_size": 100}
        if cursor:
            body["start_cursor"] = cursor
        if filter_payload:
            body["filter"] = filter_payload
        data = _request("POST", f"https://api.notion.com/v1/databases/{database_id}/query", json=body)
        pages.extend(data.get("results", []))
        if not data.get("has_more"):
            break
        cursor = data["next_cursor"]
    return pages


# ───────────────────────────────────────────────
# Property builders
# ───────────────────────────────────────────────

def _title(val: str) -> dict:
    return {"title": [{"text": {"content": val[:2000] if val else ""}}]}

def _text(val: str) -> dict:
    return {"rich_text": [{"text": {"content": val[:2000] if val else ""}}]}

def _select(val: str) -> dict:
    if not val:
        return {"select": None}
    return {"select": {"name": val}}

def _number(val) -> dict:
    return {"number": int(val) if val is not None else None}

def _checkbox(val: bool) -> dict:
    return {"checkbox": bool(val)}

def _email(val: str) -> dict:
    return {"email": val if val else None}

def _phone(val: str) -> dict:
    return {"phone_number": val if val else None}

def _url(val: str) -> dict:
    return {"url": val if val else None}


def build_properties(rec: dict) -> dict:
    """Build Notion properties payload from a cleaned record."""
    props = {
        F_NAME:         _title(rec.get("name", "")),
        F_CR:           _text(rec.get("cr", "")),
        F_EMAIL:        _email(rec.get("email", "")),
        F_MOBILE:       _phone(rec.get("mobile", "")),
        F_WA:           _url(rec.get("whatsapp", "")),
        F_REGION:       _select(rec.get("region", "")),
        F_CITY:         _text(rec.get("city", "")),
        F_SOURCE:       _select(rec.get("source", "Sheet1")),
        F_COMPLETENESS: _number(rec.get("completeness", 0)),
        F_MISS_EMAIL:   _checkbox(rec.get("missing_email", False)),
        F_MISS_MOBILE:  _checkbox(rec.get("missing_mobile", False)),
        F_DUP_SUSPECTED: _checkbox(rec.get("duplicate_suspected", False)),
        F_MANUAL_REVIEW: _checkbox(rec.get("needs_review", False)),
        F_READY:        _checkbox(rec.get("ready_for_outreach", False)),
        F_STATUS:       _select("Prospect"),          # default on create
        F_FOLLOWUP_STAGE: _select("Not Started"),     # default on create
        F_PRIORITY:     _select("Medium"),            # default on create
    }
    # Only add manual note if it has content
    note = rec.get("manual_note", "").strip()
    if note:
        props[F_MANUAL_NOTE] = _text(note)

    return props


def build_update_properties(rec: dict) -> dict:
    """Build update payload — excludes status/stage fields so manual edits survive."""
    props = {
        F_NAME:         _title(rec.get("name", "")),
        F_CR:           _text(rec.get("cr", "")),
        F_EMAIL:        _email(rec.get("email", "")),
        F_MOBILE:       _phone(rec.get("mobile", "")),
        F_WA:           _url(rec.get("whatsapp", "")),
        F_REGION:       _select(rec.get("region", "")),
        F_CITY:         _text(rec.get("city", "")),
        F_SOURCE:       _select(rec.get("source", "Sheet1")),
        F_COMPLETENESS: _number(rec.get("completeness", 0)),
        F_MISS_EMAIL:   _checkbox(rec.get("missing_email", False)),
        F_MISS_MOBILE:  _checkbox(rec.get("missing_mobile", False)),
        F_DUP_SUSPECTED: _checkbox(rec.get("duplicate_suspected", False)),
        F_MANUAL_REVIEW: _checkbox(rec.get("needs_review", False)),
        F_READY:        _checkbox(rec.get("ready_for_outreach", False)),
        # NOTE: Do NOT overwrite Status, Follow-up Stage, Priority — these may be manually edited
    }
    note = rec.get("manual_note", "").strip()
    if note:
        props[F_MANUAL_NOTE] = _text(note)

    return props


# ───────────────────────────────────────────────
# Pre-loader
# ───────────────────────────────────────────────

def preload_existing(db_id: str) -> tuple[dict, dict, dict]:
    """
    Load all existing Notion pages and index them by:
      - CR Number → page_id
      - Email      → page_id
      - Company Name (normalized) → page_id
    Returns (by_cr, by_email, by_name)
    """
    log.info("🔄  Pre-loading existing Notion records...")
    pages = query_all(db_id)
    log.info(f"   → {len(pages)} existing pages found")

    by_cr, by_email, by_name = {}, {}, {}

    for page in pages:
        pid = page["id"]
        props = page.get("properties", {})

        # CR Number (rich_text)
        cr_blocks = props.get(F_CR, {}).get("rich_text", [])
        cr = cr_blocks[0]["plain_text"].strip() if cr_blocks else ""
        if cr:
            by_cr[cr] = pid

        # Email (email)
        email = props.get(F_EMAIL, {}).get("email", "") or ""
        if email:
            by_email[email.lower()] = pid

        # Name (title)
        name_blocks = props.get(F_NAME, {}).get("title", [])
        name = name_blocks[0]["plain_text"].strip() if name_blocks else ""
        if name:
            # Normalize for loose matching
            norm = name.strip().rstrip("'").strip().lower()
            by_name[norm] = pid

    log.info(f"   → Indexed: {len(by_cr)} by CR, {len(by_email)} by email, {len(by_name)} by name")
    return by_cr, by_email, by_name


def find_existing(rec: dict, by_cr: dict, by_email: dict, by_name: dict) -> str | None:
    """Return existing page_id if a match is found, else None."""
    if rec.get("cr") and rec["cr"] in by_cr:
        return by_cr[rec["cr"]]
    if rec.get("email") and rec["email"].lower() in by_email:
        return by_email[rec["email"].lower()]
    # Loose name match
    norm = rec.get("normalized_name", rec.get("name", "")).strip().rstrip("'").strip().lower()
    if norm and norm in by_name:
        return by_name[norm]
    return None


# ───────────────────────────────────────────────
# Create / Update
# ───────────────────────────────────────────────

def create_page(db_id: str, props: dict) -> dict:
    return _request("POST", "https://api.notion.com/v1/pages", json={
        "parent": {"database_id": db_id},
        "properties": props,
    })


def update_page(page_id: str, props: dict) -> dict:
    return _request("PATCH", f"https://api.notion.com/v1/pages/{page_id}", json={
        "properties": props,
    })


# ───────────────────────────────────────────────
# Main
# ───────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Show what would happen, no writes")
    parser.add_argument("--limit", type=int, default=0, help="Max records to process (0 = all)")
    parser.add_argument("--force-update", action="store_true", help="Update even records that already exist")
    parser.add_argument("--input", default="cleaned_offices.json", help="Input JSON file")
    args = parser.parse_args()

    # Load cleaned data
    input_path = Path(__file__).parent / args.input
    if not input_path.exists():
        sys.exit(f"❌  Input file not found: {input_path}\n   Run clean_engineering_offices.py first.")

    with open(input_path, encoding="utf-8") as f:
        records = json.load(f)

    log.info(f"📂  Loaded {len(records)} records from {args.input}")

    if args.limit:
        records = records[:args.limit]
        log.info(f"   → Limited to {args.limit} records")

    # Pre-load existing pages
    by_cr, by_email, by_name = preload_existing(NOTION_DB_ID)

    # Counters
    stats = {"created": 0, "updated": 0, "skipped": 0, "errors": 0}

    for i, rec in enumerate(records, 1):
        name = rec.get("name", f"[Row {rec.get('source_row', i)}]")
        log.info(f"[{i}/{len(records)}] {name}")

        existing_id = find_existing(rec, by_cr, by_email, by_name)

        try:
            if existing_id and not args.force_update:
                log.info(f"   → EXISTS (page {existing_id[:8]}…) — skipping")
                stats["skipped"] += 1
                continue

            if existing_id and args.force_update:
                log.info(f"   → EXISTS — updating (force-update)")
                if not args.dry_run:
                    props = build_update_properties(rec)
                    update_page(existing_id, props)
                stats["updated"] += 1

            else:
                log.info(f"   → NEW — creating page")
                if not args.dry_run:
                    props = build_properties(rec)
                    new_page = create_page(NOTION_DB_ID, props)
                    new_id = new_page["id"]
                    # Update lookup maps so subsequent dupes don't re-create
                    if rec.get("cr"):
                        by_cr[rec["cr"]] = new_id
                    if rec.get("email"):
                        by_email[rec["email"].lower()] = new_id
                    norm = rec.get("normalized_name", rec.get("name", "")).strip().rstrip("'").strip().lower()
                    if norm:
                        by_name[norm] = new_id
                stats["created"] += 1

        except Exception as e:
            log.error(f"   → ERROR: {e}")
            stats["errors"] += 1

    # ── Summary ──────────────────────────────────
    print("\n" + "═"*55)
    print("   SYNC COMPLETE — مكاتب هندسية - وزارة الاسكان")
    print("═"*55)
    print(f"  Total processed:   {len(records)}")
    print(f"  Created (new):     {stats['created']}")
    print(f"  Updated (forced):  {stats['updated']}")
    print(f"  Skipped (exists):  {stats['skipped']}")
    print(f"  Errors:            {stats['errors']}")
    if args.dry_run:
        print("\n  ⚠️  DRY RUN — no changes written to Notion")
    print("═"*55 + "\n")

    # Write stats JSON for pipeline
    stats_path = Path(__file__).parent / "last_sync_stats.json"
    with open(stats_path, "w", encoding="utf-8") as f:
        json.dump({
            **stats,
            "total": len(records),
            "run_at": datetime.utcnow().isoformat(),
            "dry_run": args.dry_run,
        }, f, ensure_ascii=False, indent=2)
    log.info(f"📊  Stats saved → {stats_path}")


if __name__ == "__main__":
    main()
