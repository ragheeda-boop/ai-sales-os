#!/usr/bin/env python3
"""
AI Sales OS — Meeting Tracker v1.1

Two modes:
  1. Notion-native (default): Process meetings already in Notion Meetings DB.
     Finds meetings with linked contacts → updates Contact fields (Meeting Booked, Stage).
     This is the zero-config mode — just create meetings in Notion and run this.

  2. Google Calendar mode (--calendar): Fetch events from Google Calendar,
     match attendees to Notion contacts, create Meeting records.

Data Flow (Notion-native):
  Manual meeting entry in Notion → script reads meeting → updates linked Contact
  → Contact: Meeting Booked=True, Outreach Status="Meeting Booked", Stage="Engaged"

Data Flow (Calendar):
  Google Calendar → match attendees vs Notion contacts → create Meeting records
  → update Contact

Usage:
    python meeting_tracker.py                  # Notion-native: process existing meetings
    python meeting_tracker.py --dry-run        # preview without writing
    python meeting_tracker.py --days 7         # scan last N days (default: 2)
    python meeting_tracker.py --limit 20       # max meetings to process
    python meeting_tracker.py --calendar       # enable Google Calendar sync
"""
import os
import sys
import json
import logging
import time
import argparse
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Set, Tuple
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.dirname(__file__))
from notion_helpers import (
    NOTION_DATABASE_ID_CONTACTS,
    rate_limiter,
    notion_request,
    create_page,
    update_page,
    NOTION_BASE_URL,
)
from constants import (
    FIELD_FULL_NAME, FIELD_EMAIL, FIELD_MEETING_BOOKED,
    FIELD_OUTREACH_STATUS, FIELD_STAGE, FIELD_LEAD_TIER,
    FIELD_LEAD_SCORE, FIELD_COMPANY_RELATION,
    FIELD_MEETING_TITLE, FIELD_MEETING_TYPE, FIELD_MEETING_SCHEDULED_DATE,
    FIELD_MEETING_DURATION, FIELD_MEETING_OUTCOME, FIELD_MEETING_LINK,
    FIELD_MEETING_NUM_ATTENDEES, FIELD_MEETING_CONTACT, FIELD_MEETING_COMPANY,
    FIELD_MEETING_TIMEZONE, FIELD_MEETING_AGENDA,
    MEETING_TYPE_DISCOVERY, MEETING_TYPE_OTHER,
    OUTREACH_MEETING_BOOKED, OUTREACH_BLOCKED,
)

# ─── Config ──────────────────────────────────────────────────────────────────

NOTION_DATABASE_ID_MEETINGS = os.getenv("NOTION_DATABASE_ID_MEETINGS")
GOOGLE_CALENDAR_CREDENTIALS = os.getenv("GOOGLE_CALENDAR_CREDENTIALS")
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# ─── Logging ─────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("meeting_tracker.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


# ─── Google Calendar ─────────────────────────────────────────────────────────

def get_calendar_service():
    """Build Google Calendar API service from credentials."""
    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
    except ImportError:
        logger.error(
            "Google API libraries not installed. "
            "Run: pip install google-api-python-client google-auth-oauthlib"
        )
        return None

    if not GOOGLE_CALENDAR_CREDENTIALS:
        logger.warning("GOOGLE_CALENDAR_CREDENTIALS not set — calendar sync disabled")
        return None

    try:
        creds_data = json.loads(GOOGLE_CALENDAR_CREDENTIALS)
        creds = Credentials.from_authorized_user_info(creds_data)
        service = build("calendar", "v3", credentials=creds, cache_discovery=False)
        return service
    except Exception as e:
        logger.error(f"Failed to initialize Calendar API: {e}")
        return None


def fetch_calendar_events(service, days: int = 2) -> List[Dict]:
    """Fetch calendar events from the last N days."""
    now = datetime.now(timezone.utc)
    time_min = (now - timedelta(days=days)).isoformat()
    time_max = (now + timedelta(days=1)).isoformat()  # include tomorrow

    events = []
    page_token = None

    while True:
        try:
            result = service.events().list(
                calendarId="primary",
                timeMin=time_min,
                timeMax=time_max,
                maxResults=100,
                singleEvents=True,
                orderBy="startTime",
                pageToken=page_token,
            ).execute()
        except Exception as e:
            logger.error(f"Error fetching calendar events: {e}")
            break

        for event in result.get("items", []):
            # Skip cancelled events and all-day events without attendees
            if event.get("status") == "cancelled":
                continue

            attendees = event.get("attendees", [])
            if not attendees:
                continue  # Skip events with no attendees

            start = event.get("start", {})
            end = event.get("end", {})

            # Parse start/end times
            start_dt = start.get("dateTime", start.get("date", ""))
            end_dt = end.get("dateTime", end.get("date", ""))

            # Calculate duration in minutes
            duration = 0
            try:
                if "T" in start_dt and "T" in end_dt:
                    s = datetime.fromisoformat(start_dt.replace("Z", "+00:00"))
                    e = datetime.fromisoformat(end_dt.replace("Z", "+00:00"))
                    duration = int((e - s).total_seconds() / 60)
            except Exception:
                pass

            events.append({
                "id": event.get("id", ""),
                "summary": event.get("summary", "Untitled Meeting"),
                "description": event.get("description", ""),
                "start": start_dt,
                "end": end_dt,
                "duration": duration,
                "location": event.get("location", ""),
                "hangout_link": event.get("hangoutLink", ""),
                "html_link": event.get("htmlLink", ""),
                "attendees": [
                    a.get("email", "").lower().strip()
                    for a in attendees
                    if a.get("email")
                ],
                "organizer_email": event.get("organizer", {}).get("email", ""),
            })

        page_token = result.get("nextPageToken")
        if not page_token:
            break

    logger.info(f"Fetched {len(events)} calendar events from last {days} days")
    return events


# ─── Notion Contact Lookup ───────────────────────────────────────────────────

def preload_contact_emails() -> Dict[str, Dict]:
    """
    Pre-load contact emails + page IDs + company relations.
    Returns: { email: { page_id, name, company_ids, tier, score } }
    """
    lookup = {}
    cursor = None
    count = 0

    logger.info("Pre-loading contact emails from Notion...")

    while True:
        body = {"page_size": 100}
        if cursor:
            body["start_cursor"] = cursor

        try:
            resp = notion_request(
                "POST",
                f"{NOTION_BASE_URL}/databases/{NOTION_DATABASE_ID_CONTACTS}/query",
                json=body,
            )
            data = resp.json()
        except Exception as e:
            logger.error(f"Error pre-loading contacts: {e}")
            break

        for page in data.get("results", []):
            pid = page["id"]
            props = page.get("properties", {})

            email_val = props.get(FIELD_EMAIL, {}).get("email")
            if not email_val:
                continue

            email = email_val.strip().lower()
            name_items = props.get(FIELD_FULL_NAME, {}).get("title", [])
            name = name_items[0]["text"]["content"] if name_items else "Unknown"

            # Company relation
            company_rel = props.get(FIELD_COMPANY_RELATION, {}).get("relation", [])
            company_ids = [r["id"] for r in company_rel] if company_rel else []

            tier_sel = props.get(FIELD_LEAD_TIER, {}).get("select")
            tier = tier_sel.get("name", "") if tier_sel else ""

            score = props.get(FIELD_LEAD_SCORE, {}).get("number", 0) or 0

            lookup[email] = {
                "page_id": pid,
                "name": name,
                "company_ids": company_ids,
                "tier": tier,
                "score": score,
            }
            count += 1

        if not data.get("has_more"):
            break
        cursor = data.get("next_cursor")

    logger.info(f"Pre-loaded {count} contacts with emails")
    return lookup


# ─── Existing Meetings Lookup ────────────────────────────────────────────────

def preload_existing_meetings() -> Set[str]:
    """
    Load existing meeting titles to prevent duplicates.
    Returns: set of meeting titles (lowercase).
    """
    if not NOTION_DATABASE_ID_MEETINGS:
        return set()

    titles = set()
    cursor = None

    while True:
        body = {"page_size": 100}
        if cursor:
            body["start_cursor"] = cursor

        try:
            resp = notion_request(
                "POST",
                f"{NOTION_BASE_URL}/databases/{NOTION_DATABASE_ID_MEETINGS}/query",
                json=body,
            )
            data = resp.json()
        except Exception as e:
            logger.error(f"Error pre-loading meetings: {e}")
            break

        for page in data.get("results", []):
            props = page.get("properties", {})
            title_items = props.get(FIELD_MEETING_TITLE, {}).get("title", [])
            if title_items:
                t = title_items[0].get("text", {}).get("content", "").strip().lower()
                if t:
                    titles.add(t)

        if not data.get("has_more"):
            break
        cursor = data.get("next_cursor")

    logger.info(f"Pre-loaded {len(titles)} existing meetings")
    return titles


# ─── Meeting Creation ────────────────────────────────────────────────────────

def build_meeting_dedup_key(event_summary: str, event_start: str) -> str:
    """Create a dedup key from summary + date."""
    date_part = event_start[:10] if event_start else ""
    return f"{event_summary.strip().lower()}|{date_part}"


def create_meeting_from_event(
    event: Dict,
    matched_contacts: List[Dict],
    dry_run: bool = False,
) -> Optional[str]:
    """Create a Meeting record in Notion from a calendar event."""
    if not NOTION_DATABASE_ID_MEETINGS:
        logger.error("NOTION_DATABASE_ID_MEETINGS not set")
        return None

    # Use first matched contact as primary
    primary = matched_contacts[0]

    properties = {
        FIELD_MEETING_TITLE: {
            "title": [{"text": {"content": event["summary"][:100]}}]
        },
        FIELD_MEETING_TYPE: {"select": {"name": MEETING_TYPE_DISCOVERY}},
        FIELD_MEETING_TIMEZONE: {"select": {"name": "AST (UTC+3)"}},
    }

    # Scheduled date
    if event.get("start"):
        date_obj = {"start": event["start"]}
        if "T" in event["start"]:
            date_obj["start"] = event["start"]
        properties[FIELD_MEETING_SCHEDULED_DATE] = {"date": date_obj}

    # Duration
    if event.get("duration") and event["duration"] > 0:
        properties[FIELD_MEETING_DURATION] = {"number": event["duration"]}

    # Attendees count
    properties[FIELD_MEETING_NUM_ATTENDEES] = {
        "number": len(event.get("attendees", []))
    }

    # Meeting link
    link = event.get("hangout_link") or event.get("html_link") or ""
    if link:
        properties[FIELD_MEETING_LINK] = {"url": link}

    # Agenda from event description
    desc = event.get("description", "")
    if desc:
        properties[FIELD_MEETING_AGENDA] = {
            "rich_text": [{"text": {"content": desc[:2000]}}]
        }

    # Primary Contact relation
    properties[FIELD_MEETING_CONTACT] = {
        "relation": [{"id": primary["page_id"]}]
    }

    # Company relation (from primary contact)
    if primary.get("company_ids"):
        properties[FIELD_MEETING_COMPANY] = {
            "relation": [{"id": primary["company_ids"][0]}]
        }

    if dry_run:
        logger.info(
            f"  [DRY RUN] Would create meeting: {event['summary']} "
            f"| Contact: {primary['name']} | Date: {event.get('start', 'N/A')}"
        )
        return "dry-run-id"

    try:
        page_id = create_page(NOTION_DATABASE_ID_MEETINGS, properties)
        logger.info(f"  Created meeting: {event['summary']} → {page_id}")
        return page_id
    except Exception as e:
        logger.error(f"  Failed to create meeting '{event['summary']}': {e}")
        return None


def update_contact_meeting_booked(
    contact: Dict,
    dry_run: bool = False,
) -> bool:
    """Update contact: Meeting Booked=True, Outreach Status=Meeting Booked, Stage=Engaged."""
    properties = {
        FIELD_MEETING_BOOKED: {"checkbox": True},
    }

    # Only update Outreach Status if not in a blocked state
    # and not already a more advanced status
    properties[FIELD_OUTREACH_STATUS] = {
        "select": {"name": OUTREACH_MEETING_BOOKED}
    }

    # Update Stage to Engaged (if not already Customer/Churned)
    properties[FIELD_STAGE] = {"select": {"name": "Engaged"}}

    if dry_run:
        logger.info(f"  [DRY RUN] Would update contact: {contact['name']} → Meeting Booked")
        return True

    try:
        update_page(contact["page_id"], properties)
        logger.info(f"  Updated contact: {contact['name']} → Meeting Booked")
        return True
    except Exception as e:
        logger.error(f"  Failed to update contact {contact['name']}: {e}")
        return False


# ─── Notion-Native Processing ─────────────────────────────────────────────────

def fetch_unprocessed_meetings(days: int = 7) -> List[Dict]:
    """
    Fetch meetings from Notion Meetings DB that have a linked Contact
    but where the Contact hasn't been updated yet (Meeting Booked != True).
    Also finds meetings without linked contacts that need attention.
    """
    if not NOTION_DATABASE_ID_MEETINGS:
        return []

    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
    results = []
    cursor = None

    while True:
        body = {
            "page_size": 100,
            "filter": {
                "and": [
                    {
                        "property": FIELD_MEETING_SCHEDULED_DATE,
                        "date": {"on_or_after": cutoff},
                    },
                ]
            },
            "sorts": [{"property": FIELD_MEETING_SCHEDULED_DATE, "direction": "descending"}],
        }
        if cursor:
            body["start_cursor"] = cursor

        rate_limiter.wait()
        try:
            resp = notion_request(
                "POST",
                f"{NOTION_BASE_URL}/databases/{NOTION_DATABASE_ID_MEETINGS}/query",
                json=body,
            )
            data = resp.json()
        except Exception as e:
            logger.error(f"Error fetching meetings from Notion: {e}")
            break

        for page in data.get("results", []):
            pid = page["id"]
            props = page.get("properties", {})

            title_items = props.get(FIELD_MEETING_TITLE, {}).get("title", [])
            title = title_items[0]["text"]["content"] if title_items else "Unknown"

            type_sel = props.get(FIELD_MEETING_TYPE, {}).get("select")
            meeting_type = type_sel.get("name", "") if type_sel else ""

            outcome_sel = props.get(FIELD_MEETING_OUTCOME, {}).get("select")
            outcome = outcome_sel.get("name", "") if outcome_sel else ""

            date_prop = props.get(FIELD_MEETING_SCHEDULED_DATE, {}).get("date")
            scheduled = date_prop.get("start", "") if date_prop else ""

            # Get linked contact(s)
            contact_rel = props.get(FIELD_MEETING_CONTACT, {}).get("relation", [])
            contact_ids = [r["id"] for r in contact_rel] if contact_rel else []

            # Get linked company
            company_rel = props.get(FIELD_MEETING_COMPANY, {}).get("relation", [])
            company_ids = [r["id"] for r in company_rel] if company_rel else []

            results.append({
                "page_id": pid,
                "title": title,
                "type": meeting_type,
                "outcome": outcome,
                "scheduled": scheduled,
                "contact_ids": contact_ids,
                "company_ids": company_ids,
            })

        if not data.get("has_more"):
            break
        cursor = data.get("next_cursor")

    logger.info(f"Found {len(results)} meetings in Notion (last {days} days)")
    return results


def fetch_contact_meeting_status(contact_id: str) -> Dict:
    """Check if a contact already has Meeting Booked = True."""
    rate_limiter.wait()
    try:
        resp = notion_request("GET", f"{NOTION_BASE_URL}/pages/{contact_id}")
        page = resp.json()
        props = page.get("properties", {})

        name_items = props.get(FIELD_FULL_NAME, {}).get("title", [])
        name = name_items[0]["text"]["content"] if name_items else "Unknown"

        meeting_booked = props.get(FIELD_MEETING_BOOKED, {}).get("checkbox", False)
        outreach_sel = props.get(FIELD_OUTREACH_STATUS, {}).get("select")
        outreach = outreach_sel.get("name", "") if outreach_sel else ""

        return {
            "page_id": contact_id,
            "name": name,
            "meeting_booked": meeting_booked,
            "outreach_status": outreach,
        }
    except Exception as e:
        logger.error(f"Error fetching contact {contact_id}: {e}")
        return {}


def process_notion_meetings(
    meetings: List[Dict],
    dry_run: bool = False,
    limit: int = 50,
) -> Dict:
    """
    Process meetings already in Notion Meetings DB.
    For each meeting with linked contacts, update Contact fields if not already done.
    """
    stats = {
        "meetings_scanned": len(meetings),
        "contacts_updated": 0,
        "already_processed": 0,
        "no_contact_linked": 0,
        "errors": 0,
    }

    processed = 0

    for meeting in meetings:
        if processed >= limit:
            break

        if not meeting["contact_ids"]:
            stats["no_contact_linked"] += 1
            logger.debug(f"  Meeting '{meeting['title']}' has no linked contact — skipping")
            continue

        for contact_id in meeting["contact_ids"]:
            contact_info = fetch_contact_meeting_status(contact_id)
            if not contact_info:
                stats["errors"] += 1
                continue

            # Skip if already processed
            if contact_info.get("meeting_booked"):
                stats["already_processed"] += 1
                logger.debug(
                    f"  Contact '{contact_info['name']}' already has Meeting Booked — skipping"
                )
                continue

            # Check if outreach is in a blocked state
            if contact_info.get("outreach_status") in OUTREACH_BLOCKED:
                logger.debug(
                    f"  Contact '{contact_info['name']}' has blocked outreach status — skipping"
                )
                stats["already_processed"] += 1
                continue

            # Update contact
            success = update_contact_meeting_booked(contact_info, dry_run)
            if success:
                stats["contacts_updated"] += 1
                processed += 1
            else:
                stats["errors"] += 1

    return stats


# ─── Calendar Pipeline ────────────────────────────────────────────────────────

def process_calendar_events(
    events: List[Dict],
    contact_lookup: Dict[str, Dict],
    existing_meetings: Set[str],
    dry_run: bool = False,
    limit: int = 50,
) -> Dict:
    """Match calendar events to contacts and create meetings."""
    stats = {
        "events_scanned": len(events),
        "matched": 0,
        "created": 0,
        "skipped_duplicate": 0,
        "skipped_no_match": 0,
        "contacts_updated": 0,
        "errors": 0,
    }

    processed = 0

    for event in events:
        if processed >= limit:
            break

        # Match attendees against contact emails
        matched_contacts = []
        for attendee_email in event.get("attendees", []):
            contact = contact_lookup.get(attendee_email)
            if contact:
                matched_contacts.append(contact)

        if not matched_contacts:
            stats["skipped_no_match"] += 1
            continue

        stats["matched"] += 1

        # Dedup check: summary + date
        dedup_key = build_meeting_dedup_key(event["summary"], event.get("start", ""))
        title_lower = event["summary"].strip().lower()
        date_prefix = event.get("start", "")[:10]

        # Check if this meeting title already exists
        if title_lower in existing_meetings:
            stats["skipped_duplicate"] += 1
            logger.debug(f"  Skipping duplicate: {event['summary']}")
            continue

        # Create meeting
        meeting_id = create_meeting_from_event(event, matched_contacts, dry_run)
        if meeting_id:
            stats["created"] += 1
            existing_meetings.add(title_lower)  # prevent within-run duplicates
            processed += 1

            # Update each matched contact
            for contact in matched_contacts:
                success = update_contact_meeting_booked(contact, dry_run)
                if success:
                    stats["contacts_updated"] += 1
                else:
                    stats["errors"] += 1
        else:
            stats["errors"] += 1

    return stats


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="AI Sales OS — Meeting Tracker v1.1")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing")
    parser.add_argument("--days", type=int, default=7, help="Scan last N days (default: 7)")
    parser.add_argument("--limit", type=int, default=50, help="Max meetings/contacts to process")
    parser.add_argument("--calendar", action="store_true", help="Enable Google Calendar sync (requires credentials)")
    args = parser.parse_args()

    mode = "Calendar + Notion" if args.calendar else "Notion-native"
    logger.info("=" * 70)
    logger.info(f"MEETING TRACKER v1.1 | Mode: {mode} | Days: {args.days} | Dry Run: {args.dry_run}")
    logger.info("=" * 70)

    start_time = time.time()

    if not NOTION_DATABASE_ID_MEETINGS:
        logger.error("NOTION_DATABASE_ID_MEETINGS not set. Add to .env.")
        sys.exit(1)

    stats = {
        "meetings_scanned": 0, "contacts_updated": 0,
        "already_processed": 0, "no_contact_linked": 0,
        "errors": 0, "mode": mode,
    }

    # ── Calendar Mode: fetch events from Google Calendar → create in Notion ──
    if args.calendar:
        logger.info("Step 1: Pre-loading contacts for calendar matching...")
        contact_lookup = preload_contact_emails()
        if not contact_lookup:
            logger.warning("No contacts with emails found. Nothing to match.")
        else:
            logger.info("Step 2: Pre-loading existing meetings (dedup)...")
            existing_meetings = preload_existing_meetings()

            logger.info("Step 3: Fetching Google Calendar events...")
            service = get_calendar_service()
            if service:
                events = fetch_calendar_events(service, days=args.days)
                if events:
                    logger.info(f"Step 4: Processing {len(events)} events...")
                    cal_stats = process_calendar_events(
                        events, contact_lookup, existing_meetings,
                        dry_run=args.dry_run, limit=args.limit,
                    )
                    stats["calendar_events_scanned"] = cal_stats.get("events_scanned", 0)
                    stats["calendar_meetings_created"] = cal_stats.get("created", 0)
                    stats["contacts_updated"] += cal_stats.get("contacts_updated", 0)
                    stats["errors"] += cal_stats.get("errors", 0)
                else:
                    logger.info("No calendar events found in time range.")
            else:
                logger.warning(
                    "Calendar service unavailable. "
                    "Set GOOGLE_CALENDAR_CREDENTIALS in .env. "
                    "Falling back to Notion-native mode."
                )

    # ── Notion-Native Mode: process meetings already in Notion ──────────────
    logger.info(f"{'Step 5' if args.calendar else 'Step 1'}: Processing Notion meetings (last {args.days} days)...")
    meetings = fetch_unprocessed_meetings(days=args.days)
    stats["meetings_scanned"] = len(meetings)

    if meetings:
        logger.info(f"{'Step 6' if args.calendar else 'Step 2'}: Updating contacts from {len(meetings)} meetings...")
        notion_stats = process_notion_meetings(
            meetings, dry_run=args.dry_run, limit=args.limit,
        )
        stats["contacts_updated"] += notion_stats.get("contacts_updated", 0)
        stats["already_processed"] = notion_stats.get("already_processed", 0)
        stats["no_contact_linked"] = notion_stats.get("no_contact_linked", 0)
        stats["errors"] += notion_stats.get("errors", 0)
    else:
        logger.info("No meetings found in Notion for this period.")

    # Save stats
    elapsed = time.time() - start_time
    stats["runtime_seconds"] = round(elapsed, 1)
    stats["timestamp"] = datetime.now(timezone.utc).isoformat()

    stats_file = os.path.join(SCRIPT_DIR, "last_meeting_tracker_stats.json")
    try:
        with open(stats_file, "w") as f:
            json.dump(stats, f, indent=2)
    except Exception as e:
        logger.warning(f"Could not save stats: {e}")

    # Summary
    logger.info("")
    logger.info("=" * 50)
    logger.info(f"MEETING TRACKER SUMMARY ({mode})")
    logger.info(f"  Meetings scanned:    {stats['meetings_scanned']}")
    if args.calendar:
        logger.info(f"  Calendar events:     {stats.get('calendar_events_scanned', 0)}")
        logger.info(f"  Meetings created:    {stats.get('calendar_meetings_created', 0)}")
    logger.info(f"  Contacts updated:    {stats['contacts_updated']}")
    logger.info(f"  Already processed:   {stats['already_processed']}")
    logger.info(f"  No contact linked:   {stats['no_contact_linked']}")
    logger.info(f"  Errors:              {stats['errors']}")
    logger.info(f"  Runtime:             {elapsed:.1f}s")
    logger.info("=" * 50)


if __name__ == "__main__":
    main()
