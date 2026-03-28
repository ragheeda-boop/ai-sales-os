#!/usr/bin/env python3
"""
AI Sales OS — Opportunity Manager v1.0

Closes the revenue loop: Meetings → Opportunities → Pipeline Tracking.

What it does:
  1. Reads Meetings with Outcome="Positive" that have no linked Opportunity
  2. Auto-creates Opportunity records (Stage=Discovery, linked to Contact+Company)
  3. Reads existing Opportunities and advances stages based on new meetings
  4. Detects stale deals (no update in 14+ days) and creates follow-up tasks
  5. Updates Contact fields: Opportunity Created=True

Data Flow:
  Notion Meetings DB (Outcome=Positive)
    → Check if Contact already has an Opportunity
    → If not: Create Opportunity (Discovery stage)
    → If yes: Check if Meeting Type warrants stage advancement
  Notion Opportunities DB (open deals)
    → Flag stale deals → Create follow-up tasks

Usage:
    python opportunity_manager.py                  # run full cycle
    python opportunity_manager.py --dry-run        # preview without writing
    python opportunity_manager.py --limit 20       # limit creations
    python opportunity_manager.py --stale-only     # only check stale deals
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
    # Contact fields
    FIELD_FULL_NAME, FIELD_EMAIL, FIELD_LEAD_SCORE, FIELD_LEAD_TIER,
    FIELD_SENIORITY, FIELD_OPPORTUNITY_CREATED, FIELD_COMPANY_RELATION,
    # Meeting fields
    FIELD_MEETING_TITLE, FIELD_MEETING_TYPE, FIELD_MEETING_OUTCOME,
    FIELD_MEETING_CONTACT, FIELD_MEETING_COMPANY, FIELD_MEETING_OPPORTUNITY,
    FIELD_MEETING_NEXT_STEPS, FIELD_MEETING_SCHEDULED_DATE,
    MEETING_OUTCOME_POSITIVE, MEETING_OUTCOME_NEGATIVE, MEETING_OUTCOME_NO_SHOW,
    # Opportunity fields
    FIELD_OPP_NAME, FIELD_OPP_STAGE, FIELD_OPP_DEAL_HEALTH,
    FIELD_OPP_PROBABILITY, FIELD_OPP_NEXT_ACTION, FIELD_OPP_CONTACT,
    FIELD_OPP_COMPANY, FIELD_OPP_RECORD_SOURCE, FIELD_OPP_EXPECTED_CLOSE,
    OPP_STAGE_DISCOVERY, OPP_STAGE_PROPOSAL, OPP_STAGE_NEGOTIATION,
    OPP_STAGE_CLOSED_WON, OPP_STAGE_CLOSED_LOST,
    OPP_HEALTH_GREEN, OPP_HEALTH_YELLOW, OPP_HEALTH_RED,
    STAGE_ADVANCE_MAP, STAGE_PROBABILITY, STALE_DEAL_DAYS,
    # Task fields
    FIELD_TASK_TITLE, FIELD_TASK_PRIORITY, FIELD_TASK_STATUS,
    FIELD_TASK_DUE_DATE, FIELD_TASK_TYPE, FIELD_TASK_CONTACT,
    FIELD_TASK_COMPANY, FIELD_TASK_OPPORTUNITY, FIELD_TASK_CONTEXT,
    FIELD_TASK_EXPECTED_OUTCOME, FIELD_TASK_AUTO_CREATED,
    FIELD_TASK_AUTOMATION_TYPE,
    TASK_STATUS_NOT_STARTED,
)

# ─── Config ──────────────────────────────────────────────────────────────────

NOTION_DATABASE_ID_MEETINGS = os.getenv("NOTION_DATABASE_ID_MEETINGS")
NOTION_DATABASE_ID_OPPORTUNITIES = os.getenv("NOTION_DATABASE_ID_OPPORTUNITIES")
NOTION_DATABASE_ID_TASKS = os.getenv("NOTION_DATABASE_ID_TASKS")
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# ─── Logging ─────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("opportunity_manager.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


# ─── Data Fetchers ───────────────────────────────────────────────────────────

def fetch_positive_meetings_without_opportunity() -> List[Dict]:
    """Fetch meetings with Outcome=Positive that have no linked Opportunity."""
    if not NOTION_DATABASE_ID_MEETINGS:
        return []

    results = []
    cursor = None

    while True:
        body = {
            "page_size": 100,
            "filter": {
                "and": [
                    {"property": FIELD_MEETING_OUTCOME, "select": {"equals": MEETING_OUTCOME_POSITIVE}},
                    {"property": FIELD_MEETING_OPPORTUNITY, "relation": {"is_empty": True}},
                ]
            },
        }
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
            logger.error(f"Error fetching meetings: {e}")
            break

        for page in data.get("results", []):
            pid = page["id"]
            props = page.get("properties", {})

            title_items = props.get(FIELD_MEETING_TITLE, {}).get("title", [])
            title = title_items[0]["text"]["content"] if title_items else "Unknown"

            meeting_type_sel = props.get(FIELD_MEETING_TYPE, {}).get("select")
            meeting_type = meeting_type_sel.get("name", "") if meeting_type_sel else ""

            contact_rel = props.get(FIELD_MEETING_CONTACT, {}).get("relation", [])
            contact_ids = [r["id"] for r in contact_rel] if contact_rel else []

            company_rel = props.get(FIELD_MEETING_COMPANY, {}).get("relation", [])
            company_ids = [r["id"] for r in company_rel] if company_rel else []

            next_steps_rt = props.get(FIELD_MEETING_NEXT_STEPS, {}).get("rich_text", [])
            next_steps = next_steps_rt[0].get("plain_text", "") if next_steps_rt else ""

            sched = props.get(FIELD_MEETING_SCHEDULED_DATE, {}).get("date")
            scheduled_date = sched.get("start", "") if sched else ""

            results.append({
                "page_id": pid,
                "title": title,
                "meeting_type": meeting_type,
                "contact_ids": contact_ids,
                "company_ids": company_ids,
                "next_steps": next_steps,
                "scheduled_date": scheduled_date,
            })

        if not data.get("has_more"):
            break
        cursor = data.get("next_cursor")

    logger.info(f"Found {len(results)} positive meetings without opportunities")
    return results


def fetch_contact_info(contact_id: str) -> Optional[Dict]:
    """Fetch contact name and company for opportunity naming."""
    try:
        resp = notion_request("GET", f"{NOTION_BASE_URL}/pages/{contact_id}")
        props = resp.json().get("properties", {})

        name_items = props.get(FIELD_FULL_NAME, {}).get("title", [])
        name = name_items[0]["text"]["content"] if name_items else "Unknown"

        tier_sel = props.get(FIELD_LEAD_TIER, {}).get("select")
        tier = tier_sel.get("name", "") if tier_sel else ""

        score = props.get(FIELD_LEAD_SCORE, {}).get("number", 0) or 0

        return {"name": name, "tier": tier, "score": score}
    except Exception as e:
        logger.warning(f"Could not fetch contact {contact_id}: {e}")
        return None


def fetch_existing_opportunities_for_contacts(contact_ids: List[str]) -> Dict[str, str]:
    """
    Check if any of the given contact IDs already have an open Opportunity.
    Returns: { contact_page_id: opportunity_page_id }
    """
    if not NOTION_DATABASE_ID_OPPORTUNITIES or not contact_ids:
        return {}

    existing = {}

    for contact_id in contact_ids:
        cursor = None
        while True:
            body = {
                "page_size": 10,
                "filter": {
                    "and": [
                        {"property": FIELD_OPP_CONTACT, "relation": {"contains": contact_id}},
                        {
                            "or": [
                                {"property": FIELD_OPP_STAGE, "status": {"equals": OPP_STAGE_DISCOVERY}},
                                {"property": FIELD_OPP_STAGE, "status": {"equals": OPP_STAGE_PROPOSAL}},
                                {"property": FIELD_OPP_STAGE, "status": {"equals": OPP_STAGE_NEGOTIATION}},
                            ]
                        },
                    ]
                },
            }
            if cursor:
                body["start_cursor"] = cursor

            try:
                resp = notion_request(
                    "POST",
                    f"{NOTION_BASE_URL}/databases/{NOTION_DATABASE_ID_OPPORTUNITIES}/query",
                    json=body,
                )
                data = resp.json()
            except Exception as e:
                logger.warning(f"Error checking opportunities for {contact_id}: {e}")
                break

            for page in data.get("results", []):
                existing[contact_id] = page["id"]

            if not data.get("has_more"):
                break
            cursor = data.get("next_cursor")

    return existing


def fetch_open_opportunities() -> List[Dict]:
    """Fetch all open (non-closed) opportunities for stale deal detection."""
    if not NOTION_DATABASE_ID_OPPORTUNITIES:
        return []

    results = []
    cursor = None

    while True:
        body = {
            "page_size": 100,
            "filter": {
                "and": [
                    {"property": FIELD_OPP_STAGE, "status": {"does_not_equal": OPP_STAGE_CLOSED_WON}},
                    {"property": FIELD_OPP_STAGE, "status": {"does_not_equal": OPP_STAGE_CLOSED_LOST}},
                ]
            },
        }
        if cursor:
            body["start_cursor"] = cursor

        try:
            resp = notion_request(
                "POST",
                f"{NOTION_BASE_URL}/databases/{NOTION_DATABASE_ID_OPPORTUNITIES}/query",
                json=body,
            )
            data = resp.json()
        except Exception as e:
            logger.error(f"Error fetching opportunities: {e}")
            break

        for page in data.get("results", []):
            pid = page["id"]
            props = page.get("properties", {})
            last_edited = page.get("last_edited_time", "")

            title_items = props.get(FIELD_OPP_NAME, {}).get("title", [])
            title = title_items[0]["text"]["content"] if title_items else "Unknown"

            stage_prop = props.get(FIELD_OPP_STAGE, {}).get("status")
            stage = stage_prop.get("name", "") if stage_prop else ""

            contact_rel = props.get(FIELD_OPP_CONTACT, {}).get("relation", [])
            contact_ids = [r["id"] for r in contact_rel]

            company_rel = props.get(FIELD_OPP_COMPANY, {}).get("relation", [])
            company_ids = [r["id"] for r in company_rel]

            health_sel = props.get(FIELD_OPP_DEAL_HEALTH, {}).get("select")
            health = health_sel.get("name", "") if health_sel else ""

            results.append({
                "page_id": pid,
                "title": title,
                "stage": stage,
                "last_edited": last_edited,
                "contact_ids": contact_ids,
                "company_ids": company_ids,
                "health": health,
            })

        if not data.get("has_more"):
            break
        cursor = data.get("next_cursor")

    logger.info(f"Found {len(results)} open opportunities")
    return results


# ─── Opportunity Creation ────────────────────────────────────────────────────

def create_opportunity(
    meeting: Dict,
    contact_info: Optional[Dict],
    dry_run: bool = False,
) -> Optional[str]:
    """Create an Opportunity from a positive meeting."""
    if not NOTION_DATABASE_ID_OPPORTUNITIES:
        logger.error("NOTION_DATABASE_ID_OPPORTUNITIES not set")
        return None

    contact_name = contact_info["name"] if contact_info else "Unknown"
    opp_name = f"{contact_name} — {meeting['meeting_type'] or 'Discovery'}"

    # Expected close: 90 days from meeting date
    try:
        if meeting.get("scheduled_date"):
            base = datetime.fromisoformat(meeting["scheduled_date"][:10])
        else:
            base = datetime.now(timezone.utc)
        expected_close = (base + timedelta(days=90)).strftime("%Y-%m-%d")
    except Exception:
        expected_close = (datetime.now(timezone.utc) + timedelta(days=90)).strftime("%Y-%m-%d")

    initial_stage = STAGE_ADVANCE_MAP.get(meeting.get("meeting_type", ""), OPP_STAGE_DISCOVERY)
    probability = STAGE_PROBABILITY.get(initial_stage, "25%")

    properties = {
        FIELD_OPP_NAME: {"title": [{"text": {"content": opp_name[:100]}}]},
        FIELD_OPP_STAGE: {"status": {"name": initial_stage}},
        FIELD_OPP_PROBABILITY: {"select": {"name": probability}},
        FIELD_OPP_DEAL_HEALTH: {"select": {"name": OPP_HEALTH_GREEN}},
        FIELD_OPP_EXPECTED_CLOSE: {"date": {"start": expected_close}},
        FIELD_OPP_RECORD_SOURCE: {"select": {"name": "Apollo"}},
    }

    # Next Action from meeting next steps
    next_steps = meeting.get("next_steps", "")
    if next_steps:
        properties[FIELD_OPP_NEXT_ACTION] = {
            "rich_text": [{"text": {"content": next_steps[:2000]}}]
        }

    # Relations
    if meeting.get("contact_ids"):
        properties[FIELD_OPP_CONTACT] = {
            "relation": [{"id": meeting["contact_ids"][0]}]
        }
    if meeting.get("company_ids"):
        properties[FIELD_OPP_COMPANY] = {
            "relation": [{"id": meeting["company_ids"][0]}]
        }

    if dry_run:
        logger.info(
            f"  [DRY RUN] Would create opportunity: {opp_name} "
            f"| Stage: {initial_stage} | Close: {expected_close}"
        )
        return "dry-run-id"

    try:
        page_id = create_page(NOTION_DATABASE_ID_OPPORTUNITIES, properties)
        logger.info(f"  Created opportunity: {opp_name} → {page_id}")
        return page_id
    except Exception as e:
        logger.error(f"  Failed to create opportunity '{opp_name}': {e}")
        return None


def link_meeting_to_opportunity(meeting_id: str, opp_id: str, dry_run: bool = False) -> bool:
    """Link the meeting record to the newly created opportunity."""
    if dry_run:
        return True
    try:
        update_page(meeting_id, {
            FIELD_MEETING_OPPORTUNITY: {"relation": [{"id": opp_id}]}
        })
        return True
    except Exception as e:
        logger.warning(f"Could not link meeting to opportunity: {e}")
        return False


def update_contact_opportunity_created(contact_id: str, dry_run: bool = False) -> bool:
    """Set Opportunity Created = True on the contact."""
    if dry_run:
        return True
    try:
        update_page(contact_id, {
            FIELD_OPPORTUNITY_CREATED: {"checkbox": True}
        })
        return True
    except Exception as e:
        logger.warning(f"Could not update contact opportunity flag: {e}")
        return False


# ─── Stage Advancement ───────────────────────────────────────────────────────

def advance_opportunity_stage(
    opp_id: str,
    current_stage: str,
    meeting_type: str,
    dry_run: bool = False,
) -> bool:
    """Advance opportunity stage based on meeting type."""
    target_stage = STAGE_ADVANCE_MAP.get(meeting_type)
    if not target_stage:
        return False

    # Stage ordering for advancement
    stage_order = [OPP_STAGE_DISCOVERY, OPP_STAGE_PROPOSAL, OPP_STAGE_NEGOTIATION]
    current_idx = stage_order.index(current_stage) if current_stage in stage_order else -1
    target_idx = stage_order.index(target_stage) if target_stage in stage_order else -1

    if target_idx <= current_idx:
        return False  # Don't go backwards

    probability = STAGE_PROBABILITY.get(target_stage, "50%")

    if dry_run:
        logger.info(f"  [DRY RUN] Would advance opportunity to: {target_stage}")
        return True

    try:
        update_page(opp_id, {
            FIELD_OPP_STAGE: {"status": {"name": target_stage}},
            FIELD_OPP_PROBABILITY: {"select": {"name": probability}},
        })
        logger.info(f"  Advanced opportunity to: {target_stage}")
        return True
    except Exception as e:
        logger.error(f"  Failed to advance opportunity: {e}")
        return False


# ─── Stale Deal Detection ───────────────────────────────────────────────────

def detect_stale_deals(opportunities: List[Dict], dry_run: bool = False) -> Dict:
    """Find deals that haven't been updated in STALE_DEAL_DAYS days."""
    stale_stats = {"stale_count": 0, "tasks_created": 0, "health_updated": 0}
    cutoff = datetime.now(timezone.utc) - timedelta(days=STALE_DEAL_DAYS)

    for opp in opportunities:
        if not opp.get("last_edited"):
            continue

        try:
            last_edit = datetime.fromisoformat(opp["last_edited"].replace("Z", "+00:00"))
        except Exception:
            continue

        if last_edit > cutoff:
            continue  # Not stale

        stale_stats["stale_count"] += 1
        logger.warning(
            f"  STALE DEAL: {opp['title']} | Stage: {opp['stage']} "
            f"| Last updated: {opp['last_edited'][:10]}"
        )

        # Update deal health to Yellow if currently Green
        if opp.get("health") == OPP_HEALTH_GREEN:
            if not dry_run:
                try:
                    update_page(opp["page_id"], {
                        FIELD_OPP_DEAL_HEALTH: {"select": {"name": OPP_HEALTH_YELLOW}},
                    })
                    stale_stats["health_updated"] += 1
                except Exception as e:
                    logger.error(f"  Failed to update deal health: {e}")
            else:
                logger.info(f"  [DRY RUN] Would set deal health to Yellow")
                stale_stats["health_updated"] += 1

        # Create follow-up task if Tasks DB is configured
        if NOTION_DATABASE_ID_TASKS and opp.get("contact_ids"):
            task_created = create_stale_deal_task(opp, dry_run)
            if task_created:
                stale_stats["tasks_created"] += 1

    return stale_stats


def create_stale_deal_task(opp: Dict, dry_run: bool = False) -> bool:
    """Create a follow-up task for a stale deal."""
    title = f"STALE DEAL: Follow up on {opp['title']}"
    due = (datetime.now(timezone.utc) + timedelta(hours=24)).strftime("%Y-%m-%dT%H:%M:%S.000+00:00")
    context = (
        f"This deal ({opp['stage']}) has not been updated in {STALE_DEAL_DAYS}+ days. "
        f"Follow up with the contact to check status and update the opportunity."
    )

    properties = {
        FIELD_TASK_TITLE: {"title": [{"text": {"content": title[:100]}}]},
        FIELD_TASK_PRIORITY: {"select": {"name": "High"}},
        FIELD_TASK_STATUS: {"status": {"name": TASK_STATUS_NOT_STARTED}},
        FIELD_TASK_DUE_DATE: {"date": {"start": due}},
        FIELD_TASK_TYPE: {"select": {"name": "Follow-up"}},
        FIELD_TASK_CONTEXT: {"rich_text": [{"text": {"content": context}}]},
        FIELD_TASK_EXPECTED_OUTCOME: {
            "rich_text": [{"text": {"content": "Update opportunity status and next steps"}}]
        },
        FIELD_TASK_AUTO_CREATED: {"checkbox": True},
        FIELD_TASK_AUTOMATION_TYPE: {"select": {"name": "Stale Deal Alert"}},
    }

    if opp.get("contact_ids"):
        properties[FIELD_TASK_CONTACT] = {"relation": [{"id": opp["contact_ids"][0]}]}
    if opp.get("company_ids"):
        properties[FIELD_TASK_COMPANY] = {"relation": [{"id": opp["company_ids"][0]}]}

    # Link to opportunity
    properties[FIELD_TASK_OPPORTUNITY] = {"relation": [{"id": opp["page_id"]}]}

    if dry_run:
        logger.info(f"  [DRY RUN] Would create stale deal task: {title}")
        return True

    try:
        create_page(NOTION_DATABASE_ID_TASKS, properties)
        logger.info(f"  Created stale deal task: {title}")
        return True
    except Exception as e:
        logger.error(f"  Failed to create stale deal task: {e}")
        return False


# ─── Main Pipeline ───────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="AI Sales OS — Opportunity Manager v1.0")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing")
    parser.add_argument("--limit", type=int, default=50, help="Max opportunities to create")
    parser.add_argument("--stale-only", action="store_true", help="Only check for stale deals")
    args = parser.parse_args()

    logger.info("=" * 70)
    logger.info(f"OPPORTUNITY MANAGER v1.0 | Dry Run: {args.dry_run}")
    logger.info("=" * 70)

    start_time = time.time()

    if not NOTION_DATABASE_ID_OPPORTUNITIES:
        logger.error("NOTION_DATABASE_ID_OPPORTUNITIES not set. Add to .env.")
        sys.exit(1)

    stats = {
        "meetings_found": 0,
        "opps_created": 0,
        "opps_advanced": 0,
        "contacts_updated": 0,
        "skipped_existing": 0,
        "stale_deals": 0,
        "stale_tasks": 0,
        "errors": 0,
    }

    # ── Part 1: Create Opportunities from Positive Meetings ──

    if not args.stale_only:
        logger.info("Part 1: Processing positive meetings → opportunities...")

        meetings = fetch_positive_meetings_without_opportunity()
        stats["meetings_found"] = len(meetings)

        if meetings:
            # Collect all contact IDs to batch-check existing opportunities
            all_contact_ids = []
            for m in meetings:
                all_contact_ids.extend(m.get("contact_ids", []))

            existing_opps = fetch_existing_opportunities_for_contacts(list(set(all_contact_ids)))

            processed = 0
            for meeting in meetings:
                if processed >= args.limit:
                    break

                if not meeting.get("contact_ids"):
                    logger.warning(f"  Skipping meeting '{meeting['title']}' — no contact linked")
                    continue

                primary_contact_id = meeting["contact_ids"][0]

                # Check if contact already has an open opportunity
                existing_opp_id = existing_opps.get(primary_contact_id)

                if existing_opp_id:
                    # Try to advance the stage
                    logger.info(
                        f"  Contact already has opportunity — checking stage advancement "
                        f"for meeting type: {meeting.get('meeting_type', 'N/A')}"
                    )
                    stats["skipped_existing"] += 1

                    # Fetch current stage to check advancement
                    open_opps = fetch_open_opportunities()
                    for opp in open_opps:
                        if opp["page_id"] == existing_opp_id:
                            advanced = advance_opportunity_stage(
                                existing_opp_id, opp["stage"],
                                meeting.get("meeting_type", ""),
                                dry_run=args.dry_run,
                            )
                            if advanced:
                                stats["opps_advanced"] += 1

                            # Link meeting to opportunity
                            link_meeting_to_opportunity(
                                meeting["page_id"], existing_opp_id, args.dry_run
                            )
                            break
                    continue

                # Fetch contact info for naming
                contact_info = fetch_contact_info(primary_contact_id)

                # Create opportunity
                opp_id = create_opportunity(meeting, contact_info, dry_run=args.dry_run)
                if opp_id:
                    stats["opps_created"] += 1
                    processed += 1

                    # Link meeting to opportunity
                    link_meeting_to_opportunity(meeting["page_id"], opp_id, args.dry_run)

                    # Update contact: Opportunity Created = True
                    if update_contact_opportunity_created(primary_contact_id, args.dry_run):
                        stats["contacts_updated"] += 1
                else:
                    stats["errors"] += 1

    # ── Part 2: Detect Stale Deals ──

    logger.info("Part 2: Checking for stale deals...")
    open_opps = fetch_open_opportunities()
    stale_stats = detect_stale_deals(open_opps, dry_run=args.dry_run)
    stats["stale_deals"] = stale_stats["stale_count"]
    stats["stale_tasks"] = stale_stats["tasks_created"]

    # Save stats
    elapsed = time.time() - start_time
    stats["runtime_seconds"] = round(elapsed, 1)
    stats["timestamp"] = datetime.now(timezone.utc).isoformat()

    stats_file = os.path.join(SCRIPT_DIR, "last_opportunity_stats.json")
    try:
        with open(stats_file, "w") as f:
            json.dump(stats, f, indent=2)
    except Exception as e:
        logger.warning(f"Could not save stats: {e}")

    # Summary
    logger.info("")
    logger.info("=" * 50)
    logger.info("OPPORTUNITY MANAGER SUMMARY")
    logger.info(f"  Positive meetings found: {stats['meetings_found']}")
    logger.info(f"  Opportunities created:   {stats['opps_created']}")
    logger.info(f"  Opportunities advanced:  {stats['opps_advanced']}")
    logger.info(f"  Skipped (existing opp):  {stats['skipped_existing']}")
    logger.info(f"  Contacts updated:        {stats['contacts_updated']}")
    logger.info(f"  Stale deals detected:    {stats['stale_deals']}")
    logger.info(f"  Stale deal tasks:        {stats['stale_tasks']}")
    logger.info(f"  Errors:                  {stats['errors']}")
    logger.info(f"  Runtime:                 {elapsed:.1f}s")
    logger.info("=" * 50)


if __name__ == "__main__":
    main()
