#!/usr/bin/env python3
"""
apollo_activity_sync.py
========================
Phase 4: Pull Apollo Sequence activity → update Notion engagement fields

For each company in Notion that has an Apollo Contact ID:
  - Fetch sequence membership status from Apollo
  - Fetch email activity: sent, opened, replied, bounced
  - Update Notion: Email Sent, Email Opened, Email Replied, Email Bounced,
    In Sequence, Sequence Status, Sequence Step,
    Last Email Sent At, Last Opened At, Last Replied At,
    Last Activity Date, Last Activity Type, Activity Count, Positive Signal

Also syncs per-company aggregate stats for account-level reporting.

Run:
    python apollo_activity_sync.py
    python apollo_activity_sync.py --dry-run
    python apollo_activity_sync.py --days 30
    python apollo_activity_sync.py --limit 100
    python apollo_activity_sync.py --sequence-only   # skip contacts not in sequence
"""

import os, sys, time, json, argparse, logging
from pathlib import Path
from datetime import datetime, timezone, timedelta
from collections import defaultdict

import requests
from dotenv import load_dotenv

from constants_eng import (
    NOTION_DB_ID, APOLLO_SEQUENCE_ID, APOLLO_SEQUENCE_NAME,
    F_NAME, F_APOLLO_CON_ID, F_IN_SEQ, F_SEQ_STATUS, F_SEQ_STEP,
    F_EMAIL_SENT, F_EMAIL_OPENED, F_EMAIL_REPLIED, F_EMAIL_BOUNCED,
    F_LAST_SENT_AT, F_LAST_OPENED_AT, F_LAST_REPLIED_AT,
    F_LAST_ACT_DATE, F_LAST_ACT_TYPE, F_ACT_COUNT, F_POS_SIGNAL,
    F_MTG_BOOKED, F_STATUS, F_FOLLOWUP_STAGE,
    STALE_DAYS, OPENED_FOLLOWUP_DAYS,
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
        logging.FileHandler("apollo_activity_sync.log", encoding="utf-8"),
    ],
)
log = logging.getLogger(__name__)

# ───────────────────────────────────────────────
# Load credentials
# ───────────────────────────────────────────────

load_dotenv(Path(__file__).parent / ".env")
NOTION_TOKEN = os.getenv("NOTION_API_KEY") or os.getenv("NOTION_TOKEN")
APOLLO_KEY   = os.getenv("APOLLO_API_KEY")

if not NOTION_TOKEN:
    sys.exit("❌  NOTION_API_KEY not set in .env")
if not APOLLO_KEY:
    sys.exit("❌  APOLLO_API_KEY not set in .env")

NOTION_HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json",
}
APOLLO_BASE = "https://api.apollo.io/v1"

# ───────────────────────────────────────────────
# HTTP helpers
# ───────────────────────────────────────────────

def _notion_req(method: str, url: str, **kwargs) -> dict:
    for attempt in range(6):
        resp = requests.request(method, url, headers=NOTION_HEADERS, **kwargs)
        if resp.status_code == 429:
            time.sleep(2 ** attempt); continue
        if resp.status_code >= 500:
            time.sleep(2 ** attempt); continue
        resp.raise_for_status()
        return resp.json()
    raise RuntimeError(f"Notion request failed: {url}")


def _apollo_req(method: str, path: str, **kwargs) -> dict:
    url = f"{APOLLO_BASE}{path}"
    params = kwargs.pop("params", {})
    params["api_key"] = APOLLO_KEY
    for attempt in range(5):
        resp = requests.request(method, url, params=params, **kwargs)
        if resp.status_code == 429:
            time.sleep(3 ** attempt); continue
        if resp.status_code >= 500:
            time.sleep(2 ** attempt); continue
        if resp.status_code == 404:
            return {}
        resp.raise_for_status()
        return resp.json()
    return {}


def notion_query_all(db_id: str, filter_payload: dict = None) -> list[dict]:
    pages, cursor = [], None
    while True:
        body = {"page_size": 100}
        if cursor:
            body["start_cursor"] = cursor
        if filter_payload:
            body["filter"] = filter_payload
        data = _notion_req("POST", f"https://api.notion.com/v1/databases/{db_id}/query", json=body)
        pages.extend(data.get("results", []))
        if not data.get("has_more"):
            break
        cursor = data["next_cursor"]
    return pages


def update_page(page_id: str, props: dict) -> dict:
    return _notion_req("PATCH", f"https://api.notion.com/v1/pages/{page_id}", json={"properties": props})


# ───────────────────────────────────────────────
# Property helpers
# ───────────────────────────────────────────────

def _get_text(props: dict, field: str) -> str:
    blocks = props.get(field, {}).get("rich_text", [])
    return blocks[0]["plain_text"].strip() if blocks else ""

def _get_title(props: dict, field: str) -> str:
    blocks = props.get(field, {}).get("title", [])
    return blocks[0]["plain_text"].strip() if blocks else ""

def _get_select(props: dict, field: str) -> str:
    sel = props.get(field, {}).get("select")
    return sel["name"] if sel else ""

def _text(val: str) -> dict:
    return {"rich_text": [{"text": {"content": str(val)[:2000] if val else ""}}]}

def _checkbox(val: bool) -> dict:
    return {"checkbox": bool(val)}

def _select(val: str) -> dict:
    return {"select": {"name": val}} if val else {"select": None}

def _number(val) -> dict:
    return {"number": int(val) if val is not None else None}

def _date(val: str) -> dict:
    """val should be ISO 8601 string or empty."""
    if not val:
        return {"date": None}
    return {"date": {"start": val}}


# ───────────────────────────────────────────────
# Apollo sequence activity fetcher
# ───────────────────────────────────────────────

def fetch_sequence_memberships(sequence_id: str, page: int = 1) -> dict:
    """Fetch contacts enrolled in a specific sequence."""
    return _apollo_req("GET", "/emailer_campaigns/search", params={
        "emailer_campaign_ids[]": sequence_id,
        "page": page,
        "per_page": 100,
    })


def fetch_contact_activity(contact_id: str) -> dict:
    """Fetch email activity for a specific contact."""
    return _apollo_req("GET", f"/contacts/{contact_id}", params={})


def fetch_sequence_analytics(sequence_id: str) -> dict:
    """Fetch aggregate sequence analytics."""
    return _apollo_req("GET", "/emailer_campaigns/search", params={
        "id": sequence_id,
    })


def parse_contact_activity(contact_data: dict) -> dict:
    """
    Extract engagement signals from Apollo contact data.
    Returns a dict with all relevant engagement fields.
    """
    activity = {
        "email_sent": False,
        "email_opened": False,
        "email_replied": False,
        "email_bounced": False,
        "in_sequence": False,
        "sequence_status": "",
        "sequence_step": 0,
        "last_sent_at": "",
        "last_opened_at": "",
        "last_replied_at": "",
        "last_activity_date": "",
        "last_activity_type": "",
        "activity_count": 0,
        "positive_signal": False,
        "meeting_booked": False,
    }

    if not contact_data:
        return activity

    contact = contact_data.get("contact", contact_data)

    # Check emailer campaign memberships
    campaigns = contact.get("emailer_campaign_statuses", [])
    for campaign in campaigns:
        if campaign.get("emailer_campaign_id") == APOLLO_SEQUENCE_ID:
            activity["in_sequence"] = True
            status = campaign.get("status", "")
            activity["sequence_status"] = status
            activity["sequence_step"] = campaign.get("current_step", 0) or 0

            # Map Apollo status to readable
            if status in ("active", "paused"):
                activity["email_sent"] = True
            elif status in ("finished", "replied", "demo_booked"):
                activity["email_sent"] = True
                if status in ("replied", "demo_booked"):
                    activity["email_replied"] = True
                    activity["positive_signal"] = True
                if status == "demo_booked":
                    activity["meeting_booked"] = True
            elif status == "bounced":
                activity["email_bounced"] = True

    # Check email_opened, email_replied from contact fields
    if contact.get("email_open_count", 0) > 0:
        activity["email_opened"] = True
    if contact.get("email_replied_count", 0) > 0:
        activity["email_replied"] = True
        activity["positive_signal"] = True

    # Email sent count
    sent_count = contact.get("emails_sent_count", 0) or contact.get("email_sends_count", 0) or 0
    if sent_count > 0:
        activity["email_sent"] = True
        activity["activity_count"] = int(sent_count)

    # Dates from contact fields
    last_contacted = contact.get("last_contacted_at") or contact.get("last_activity_date") or ""
    if last_contacted:
        activity["last_activity_date"] = last_contacted[:10]
        activity["last_sent_at"] = last_contacted[:10]

    # If replied, use replied_at
    last_replied = contact.get("last_replied_at") or ""
    if last_replied:
        activity["last_replied_at"] = last_replied[:10]
        activity["last_activity_date"] = last_replied[:10]
        activity["last_activity_type"] = "Reply"

    # Email opened
    if activity["email_opened"] and not activity["last_opened_at"]:
        activity["last_opened_at"] = activity["last_activity_date"]

    # Positive signal from Apollo boolean
    if contact.get("phone_numbers"):
        # Has phone = actively enriched
        pass

    # Determine last activity type
    if not activity["last_activity_type"]:
        if activity["email_replied"]:
            activity["last_activity_type"] = "Reply"
        elif activity["email_opened"]:
            activity["last_activity_type"] = "Open"
        elif activity["email_sent"]:
            activity["last_activity_type"] = "Sent"

    return activity


def build_update_props(act: dict) -> dict:
    """Build Notion update properties from activity dict."""
    props = {}

    # Only update sent/opened/replied if Apollo explicitly has data
    # (safe boolean writing — don't overwrite True with False)
    if act["email_sent"]:
        props[F_EMAIL_SENT] = _checkbox(True)
    if act["email_opened"]:
        props[F_EMAIL_OPENED] = _checkbox(True)
    if act["email_replied"]:
        props[F_EMAIL_REPLIED] = _checkbox(True)
        props[F_POS_SIGNAL] = _checkbox(True)
    if act["email_bounced"]:
        props[F_EMAIL_BOUNCED] = _checkbox(True)

    if act["in_sequence"]:
        props[F_IN_SEQ] = _checkbox(True)
        props[F_SEQ_STATUS] = _select(act["sequence_status"])
        props[F_SEQ_STEP] = _number(act["sequence_step"])

    if act["last_sent_at"]:
        props[F_LAST_SENT_AT] = _date(act["last_sent_at"])
    if act["last_opened_at"]:
        props[F_LAST_OPENED_AT] = _date(act["last_opened_at"])
    if act["last_replied_at"]:
        props[F_LAST_REPLIED_AT] = _date(act["last_replied_at"])
    if act["last_activity_date"]:
        props[F_LAST_ACT_DATE] = _date(act["last_activity_date"])
    if act["last_activity_type"]:
        props[F_LAST_ACT_TYPE] = _select(act["last_activity_type"])
    if act["activity_count"]:
        props[F_ACT_COUNT] = _number(act["activity_count"])
    if act["meeting_booked"]:
        props[F_MTG_BOOKED] = _checkbox(True)

    return props


# ───────────────────────────────────────────────
# Main
# ───────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--days", type=int, default=90, help="Look back N days for activity")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--sequence-only", action="store_true", help="Only process contacts in sequence")
    args = parser.parse_args()

    log.info("📂  Loading Notion records with Apollo Contact IDs...")

    # Filter: only records that have been matched to Apollo
    filter_payload = {
        "property": F_APOLLO_CON_ID,
        "rich_text": {"is_not_empty": True}
    } if not args.sequence_only else {
        "and": [
            {"property": F_APOLLO_CON_ID, "rich_text": {"is_not_empty": True}},
            {"property": F_IN_SEQ, "checkbox": {"equals": True}},
        ]
    }

    pages = notion_query_all(NOTION_DB_ID, filter_payload)
    log.info(f"   → {len(pages)} pages with Apollo Contact ID")

    if args.limit:
        pages = pages[:args.limit]

    # Compute lookback cutoff
    cutoff = datetime.now(timezone.utc) - timedelta(days=args.days)

    stats = defaultdict(int)
    stats["total"] = len(pages)

    for i, page in enumerate(pages, 1):
        pid = page["id"]
        props = page.get("properties", {})
        name = _get_title(props, F_NAME)
        contact_id = _get_text(props, F_APOLLO_CON_ID)

        log.info(f"[{i}/{len(pages)}] {name} → contact: {contact_id[:8] if contact_id else 'none'}…")

        if not contact_id:
            stats["skipped"] += 1
            continue

        try:
            # Fetch contact data from Apollo
            contact_data = _apollo_req("GET", f"/contacts/{contact_id}", params={})

            if not contact_data or "contact" not in contact_data:
                log.info(f"   → No data returned from Apollo")
                stats["no_data"] += 1
                time.sleep(0.3)
                continue

            act = parse_contact_activity(contact_data)
            update_props = build_update_props(act)

            if update_props:
                if not args.dry_run:
                    update_page(pid, update_props)
                stats["updated"] += 1

                # Log highlights
                highlights = []
                if act["email_replied"]:
                    highlights.append("REPLIED ✓")
                elif act["email_opened"]:
                    highlights.append("opened")
                elif act["email_sent"]:
                    highlights.append("sent")
                if act["in_sequence"]:
                    highlights.append(f"in seq ({act['sequence_status']})")
                if highlights:
                    log.info(f"   → {', '.join(highlights)}")
            else:
                stats["no_change"] += 1
                log.info(f"   → No activity data to update")

            # Accumulate aggregate stats
            if act["email_sent"]:   stats["total_sent"] += 1
            if act["email_opened"]: stats["total_opened"] += 1
            if act["email_replied"]: stats["total_replied"] += 1
            if act["email_bounced"]: stats["total_bounced"] += 1
            if act["meeting_booked"]: stats["total_meetings"] += 1

            time.sleep(0.3)  # Apollo rate limiting

        except Exception as e:
            log.error(f"   → ERROR: {e}")
            stats["errors"] += 1

    # ── Summary ──────────────────────────────────
    total = stats["total"] or 1
    print("\n" + "═"*60)
    print("   APOLLO ACTIVITY SYNC COMPLETE")
    print("═"*60)
    print(f"  Total processed:      {stats['total']}")
    print(f"  Updated:              {stats['updated']}")
    print(f"  No change:            {stats['no_change']}")
    print(f"  No data (Apollo):     {stats['no_data']}")
    print(f"  Errors:               {stats['errors']}")
    print()
    print(f"  📧  Emails sent:       {stats['total_sent']} ({stats['total_sent']/total*100:.1f}%)")
    print(f"  👁️  Emails opened:     {stats['total_opened']} ({stats['total_opened']/total*100:.1f}%)")
    print(f"  ↩️  Emails replied:    {stats['total_replied']} ({stats['total_replied']/total*100:.1f}%)")
    print(f"  ⛔  Bounced:           {stats['total_bounced']}")
    print(f"  📅  Meetings booked:   {stats['total_meetings']}")

    open_rate  = stats['total_opened']  / max(stats['total_sent'], 1) * 100
    reply_rate = stats['total_replied'] / max(stats['total_sent'], 1) * 100
    print()
    print(f"  Open rate:            {open_rate:.1f}%")
    print(f"  Reply rate:           {reply_rate:.1f}%")

    if args.dry_run:
        print("\n  ⚠️  DRY RUN — no changes written")
    print("═"*60 + "\n")

    # Save stats
    stats_path = Path(__file__).parent / "last_activity_stats.json"
    with open(stats_path, "w", encoding="utf-8") as f:
        json.dump({**dict(stats), "run_at": datetime.utcnow().isoformat()}, f, ensure_ascii=False, indent=2)
    log.info(f"📊  Stats saved → {stats_path}")


if __name__ == "__main__":
    main()
