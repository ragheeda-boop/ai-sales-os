#!/usr/bin/env python3
"""
AI Sales OS — Opportunity Manager v2.0 (Company-Centric)

Closes the revenue loop: Meetings → Opportunities → Pipeline Tracking.
v2.0: ONE active Opportunity per Company (not per Contact).

What it does:
  1. Reads Meetings with Outcome="Positive" that have no linked Opportunity
  2. Groups meetings by Company (not Contact)
  3. Checks if Company already has an open Opportunity → update it
  4. If not → creates ONE Opportunity per Company (with all stakeholders)
  5. Advances existing Opportunity stages based on new meeting types
  6. Detects stale deals (no update in 14+ days) → creates follow-up tasks
  7. Updates Contact fields: Opportunity Created=True

Company-Centric Rules:
  - One active Opportunity per Company (enforced)
  - Opportunity named: "Company Name — Stage" (not Contact Name)
  - Stakeholder Contacts = all contacts involved in meetings
  - Task Owner = Primary Company Owner
  - Buying Committee Size = count of unique stakeholder contacts

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
    NOTION_DATABASE_ID_COMPANIES,
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
    FIELD_CONTACT_OWNER,
    # Company fields
    FIELD_COMPANY_NAME, FIELD_PRIMARY_COMPANY_OWNER, FIELD_COMPANY_STAGE,
    COMPANY_STAGE_OPPORTUNITY,
    # Meeting fields
    FIELD_MEETING_TITLE, FIELD_MEETING_TYPE, FIELD_MEETING_OUTCOME,
    FIELD_MEETING_CONTACT, FIELD_MEETING_COMPANY, FIELD_MEETING_OPPORTUNITY,
    FIELD_MEETING_NEXT_STEPS, FIELD_MEETING_SCHEDULED_DATE,
    MEETING_OUTCOME_POSITIVE, MEETING_OUTCOME_NEGATIVE, MEETING_OUTCOME_NO_SHOW,
    # Opportunity fields
    FIELD_OPP_NAME, FIELD_OPP_STAGE, FIELD_OPP_DEAL_HEALTH,
    FIELD_OPP_PROBABILITY, FIELD_OPP_NEXT_ACTION, FIELD_OPP_CONTACT,
    FIELD_OPP_COMPANY, FIELD_OPP_RECORD_SOURCE, FIELD_OPP_EXPECTED_CLOSE,
    FIELD_OPP_STAKEHOLDER_CONTACTS,
    FIELD_OPP_COMPANY_OWNER_SNAPSHOT, FIELD_OPP_BUYING_COMMITTEE_SIZE,
    FIELD_OPP_DECISION_MAKER_IDENTIFIED, FIELD_OPP_REVENUE_PRIORITY,
    OPP_STAGE_DISCOVERY, OPP_STAGE_PROPOSAL, OPP_STAGE_NEGOTIATION,
    OPP_STAGE_CLOSED_WON, OPP_STAGE_CLOSED_LOST,
    OPP_HEALTH_GREEN, OPP_HEALTH_YELLOW, OPP_HEALTH_RED,
    STAGE_ADVANCE_MAP, STAGE_PROBABILITY, STALE_DEAL_DAYS,
    # Task fields
    FIELD_TASK_TITLE, FIELD_TASK_PRIORITY, FIELD_TASK_STATUS,
    FIELD_TASK_DUE_DATE, FIELD_TASK_TYPE, FIELD_TASK_CONTACT,
    FIELD_TASK_COMPANY, FIELD_TASK_OPPORTUNITY, FIELD_TASK_CONTEXT,
    FIELD_TASK_EXPECTED_OUTCOME, FIELD_TASK_AUTO_CREATED,
    FIELD_TASK_AUTOMATION_TYPE, FIELD_TASK_OWNER, FIELD_OWNER_SOURCE,
    TASK_STATUS_NOT_STARTED,
    # Score tiers
    TIER_HOT, TIER_WARM,
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


def fetch_company_info(company_id: str) -> Optional[Dict]:
    """Fetch company name and primary owner for opportunity naming."""
    try:
        resp = notion_request("GET", f"{NOTION_BASE_URL}/pages/{company_id}")
        props = resp.json().get("properties", {})

        name_items = props.get(FIELD_COMPANY_NAME, {}).get("title", [])
        name = name_items[0]["text"]["content"] if name_items else "Unknown"

        primary_owner_sel = props.get(FIELD_PRIMARY_COMPANY_OWNER, {}).get("select")
        primary_owner = primary_owner_sel.get("name", "") if primary_owner_sel else ""

        return {"name": name, "primary_owner": primary_owner}
    except Exception as e:
        logger.warning(f"Could not fetch company {company_id}: {e}")
        return None


def fetch_contact_info(contact_id: str) -> Optional[Dict]:
    """Fetch contact name, tier, score, seniority for stakeholder tracking."""
    try:
        resp = notion_request("GET", f"{NOTION_BASE_URL}/pages/{contact_id}")
        props = resp.json().get("properties", {})

        name_items = props.get(FIELD_FULL_NAME, {}).get("title", [])
        name = name_items[0]["text"]["content"] if name_items else "Unknown"

        tier_sel = props.get(FIELD_LEAD_TIER, {}).get("select")
        tier = tier_sel.get("name", "") if tier_sel else ""

        score = props.get(FIELD_LEAD_SCORE, {}).get("number", 0) or 0

        seniority_sel = props.get(FIELD_SENIORITY, {}).get("select")
        seniority = seniority_sel.get("name", "") if seniority_sel else ""

        return {"name": name, "tier": tier, "score": score, "seniority": seniority}
    except Exception as e:
        logger.warning(f"Could not fetch contact {contact_id}: {e}")
        return None


def fetch_existing_opportunities_for_companies(company_ids: List[str]) -> Dict[str, Dict]:
    """
    Check if any of the given company IDs already have an open Opportunity.
    v2.0: Company-Centric — ONE opportunity per company.
    Returns: { company_page_id: {"opp_id": str, "stage": str, "contact_ids": list} }
    """
    if not NOTION_DATABASE_ID_OPPORTUNITIES or not company_ids:
        return {}

    existing = {}

    for company_id in company_ids:
        cursor = None
        while True:
            body = {
                "page_size": 10,
                "filter": {
                    "and": [
                        {"property": FIELD_OPP_COMPANY, "relation": {"contains": company_id}},
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
                logger.warning(f"Error checking opportunities for company {company_id}: {e}")
                break

            for page in data.get("results", []):
                props = page.get("properties", {})
                stage_prop = props.get(FIELD_OPP_STAGE, {}).get("status")
                stage = stage_prop.get("name", "") if stage_prop else ""

                contact_rel = props.get(FIELD_OPP_CONTACT, {}).get("relation", [])
                opp_contact_ids = [r["id"] for r in contact_rel]

                # Keep only the first (most recent) open opportunity per company
                if company_id not in existing:
                    existing[company_id] = {
                        "opp_id": page["id"],
                        "stage": stage,
                        "contact_ids": opp_contact_ids,
                    }

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


# ─── Grouping ────────────────────────────────────────────────────────────────

def group_meetings_by_company(meetings: List[Dict]) -> Dict[str, List[Dict]]:
    """
    Group meetings by company_id. Meetings without a company
    are grouped under their first contact's company (fetched from Notion).
    v2.0: Company is the primary grouping entity.
    """
    company_meetings: Dict[str, List[Dict]] = {}

    for meeting in meetings:
        company_id = None

        # Prefer direct company link on the meeting
        if meeting.get("company_ids"):
            company_id = meeting["company_ids"][0]
        elif meeting.get("contact_ids"):
            # Fall back: look up the contact's company
            contact_id = meeting["contact_ids"][0]
            try:
                resp = notion_request("GET", f"{NOTION_BASE_URL}/pages/{contact_id}")
                props = resp.json().get("properties", {})
                comp_rel = props.get(FIELD_COMPANY_RELATION, {}).get("relation", [])
                if comp_rel:
                    company_id = comp_rel[0]["id"]
            except Exception as e:
                logger.warning(f"Could not resolve company for contact {contact_id}: {e}")

        if not company_id:
            logger.warning(f"Skipping meeting '{meeting['title']}' — no company resolvable")
            continue

        # Ensure meeting has the company_id set for downstream use
        if not meeting.get("company_ids"):
            meeting["company_ids"] = [company_id]

        company_meetings.setdefault(company_id, []).append(meeting)

    return company_meetings


# ─── Opportunity Creation (Company-Centric) ──────────────────────────────────

def create_opportunity(
    company_id: str,
    company_info: Optional[Dict],
    meetings: List[Dict],
    all_contact_ids: List[str],
    stakeholder_infos: List[Dict],
    dry_run: bool = False,
) -> Optional[str]:
    """
    Create ONE Opportunity for a Company from its positive meetings.
    v2.0: Company-Centric naming, stakeholder tracking, owner snapshot.
    """
    if not NOTION_DATABASE_ID_OPPORTUNITIES:
        logger.error("NOTION_DATABASE_ID_OPPORTUNITIES not set")
        return None

    company_name = company_info["name"] if company_info else "Unknown"
    primary_owner = company_info.get("primary_owner", "") if company_info else ""

    # Pick the highest-priority meeting type for initial stage
    best_meeting_type = ""
    latest_next_steps = ""
    latest_scheduled = ""
    for m in meetings:
        mt = m.get("meeting_type", "")
        if mt in STAGE_ADVANCE_MAP:
            # Pick the most advanced meeting type
            if not best_meeting_type or \
               list(STAGE_ADVANCE_MAP.keys()).index(mt) > list(STAGE_ADVANCE_MAP.keys()).index(best_meeting_type):
                best_meeting_type = mt
        if m.get("next_steps"):
            latest_next_steps = m["next_steps"]
        sd = m.get("scheduled_date", "")
        if sd > latest_scheduled:
            latest_scheduled = sd

    initial_stage = STAGE_ADVANCE_MAP.get(best_meeting_type, OPP_STAGE_DISCOVERY)
    probability = STAGE_PROBABILITY.get(initial_stage, "25%")
    opp_name = f"{company_name} — {initial_stage}"

    # Expected close: 90 days from most recent meeting
    try:
        if latest_scheduled:
            base = datetime.fromisoformat(latest_scheduled[:10])
        else:
            base = datetime.now(timezone.utc)
        expected_close = (base + timedelta(days=90)).strftime("%Y-%m-%d")
    except Exception:
        expected_close = (datetime.now(timezone.utc) + timedelta(days=90)).strftime("%Y-%m-%d")

    # Build stakeholder summary
    stakeholder_names = [s["name"] for s in stakeholder_infos if s]
    stakeholder_summary = ", ".join(stakeholder_names) if stakeholder_names else ""

    # Check for decision maker among stakeholders
    decision_maker_found = any(
        s.get("seniority", "") in ("C-Suite", "VP", "Director", "Owner", "Founder", "Partner")
        for s in stakeholder_infos if s
    )

    # Determine revenue priority from best contact tier
    best_tier = ""
    for s in stakeholder_infos:
        if s and s.get("tier") == TIER_HOT:
            best_tier = TIER_HOT
            break
        if s and s.get("tier") == TIER_WARM and best_tier != TIER_HOT:
            best_tier = TIER_WARM

    revenue_priority = "Tier 1" if best_tier == TIER_HOT else "Tier 2" if best_tier == TIER_WARM else "Tier 3"

    properties = {
        FIELD_OPP_NAME: {"title": [{"text": {"content": opp_name[:100]}}]},
        FIELD_OPP_STAGE: {"status": {"name": initial_stage}},
        FIELD_OPP_PROBABILITY: {"select": {"name": probability}},
        FIELD_OPP_DEAL_HEALTH: {"select": {"name": OPP_HEALTH_GREEN}},
        FIELD_OPP_EXPECTED_CLOSE: {"date": {"start": expected_close}},
        FIELD_OPP_RECORD_SOURCE: {"select": {"name": "Apollo"}},
        # Company-Centric v2.0 fields
        FIELD_OPP_BUYING_COMMITTEE_SIZE: {"number": len(all_contact_ids)},
        FIELD_OPP_DECISION_MAKER_IDENTIFIED: {"checkbox": decision_maker_found},
        FIELD_OPP_REVENUE_PRIORITY: {"select": {"name": revenue_priority}},
    }

    # Owner = Primary Company Owner
    # NOTE: "Opportunity Owner" is a person-type field in Notion (requires user IDs).
    # We write the owner name to Company Owner Snapshot (rich_text) instead.
    if primary_owner:
        properties[FIELD_OPP_COMPANY_OWNER_SNAPSHOT] = {
            "rich_text": [{"text": {"content": primary_owner}}]
        }

    # Stakeholder Contacts summary (rich_text — names + seniority)
    if stakeholder_summary:
        properties[FIELD_OPP_STAKEHOLDER_CONTACTS] = {
            "rich_text": [{"text": {"content": stakeholder_summary[:2000]}}]
        }

    # Next Action from latest meeting next steps
    if latest_next_steps:
        properties[FIELD_OPP_NEXT_ACTION] = {
            "rich_text": [{"text": {"content": latest_next_steps[:2000]}}]
        }

    # Company relation
    properties[FIELD_OPP_COMPANY] = {"relation": [{"id": company_id}]}

    # Primary Contact = highest-scored contact
    if all_contact_ids:
        properties[FIELD_OPP_CONTACT] = {"relation": [{"id": all_contact_ids[0]}]}

    if dry_run:
        logger.info(
            f"  [DRY RUN] Would create opportunity: {opp_name} "
            f"| Stage: {initial_stage} | Close: {expected_close} "
            f"| Stakeholders: {len(all_contact_ids)} | Owner: {primary_owner}"
        )
        return "dry-run-id"

    try:
        page_id = create_page(NOTION_DATABASE_ID_OPPORTUNITIES, properties)
        logger.info(
            f"  Created opportunity: {opp_name} → {page_id} "
            f"| Stakeholders: {len(all_contact_ids)} | Owner: {primary_owner}"
        )
        return page_id
    except Exception as e:
        logger.error(f"  Failed to create opportunity '{opp_name}': {e}")
        return None


def link_meeting_to_opportunity(meeting_id: str, opp_id: str, dry_run: bool = False) -> bool:
    """Link the meeting record to the opportunity."""
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


def update_company_stage_to_opportunity(company_id: str, dry_run: bool = False) -> bool:
    """Set Company Stage = Opportunity when an opportunity is created."""
    if dry_run:
        return True
    try:
        update_page(company_id, {
            FIELD_COMPANY_STAGE: {"select": {"name": COMPANY_STAGE_OPPORTUNITY}}
        })
        logger.info(f"  Updated Company Stage → Opportunity for {company_id}")
        return True
    except Exception as e:
        logger.warning(f"Could not update company stage: {e}")
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


def update_opportunity_stakeholders(
    opp_id: str,
    new_contact_ids: List[str],
    existing_contact_ids: List[str],
    dry_run: bool = False,
) -> bool:
    """Add new stakeholder contacts to an existing opportunity."""
    # Merge existing + new, deduplicate
    all_ids = list(dict.fromkeys(existing_contact_ids + new_contact_ids))
    if set(all_ids) == set(existing_contact_ids):
        return False  # No new stakeholders

    if dry_run:
        logger.info(f"  [DRY RUN] Would update stakeholders: {len(existing_contact_ids)} → {len(all_ids)}")
        return True

    try:
        update_page(opp_id, {
            FIELD_OPP_BUYING_COMMITTEE_SIZE: {"number": len(all_ids)},
        })
        logger.info(f"  Updated buying committee: {len(existing_contact_ids)} → {len(all_ids)}")
        return True
    except Exception as e:
        logger.warning(f"Could not update opportunity stakeholders: {e}")
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

        # Create follow-up task (Company-Centric: uses company, not contact)
        if NOTION_DATABASE_ID_TASKS and opp.get("company_ids"):
            task_created = create_stale_deal_task(opp, dry_run)
            if task_created:
                stale_stats["tasks_created"] += 1

    return stale_stats


def create_stale_deal_task(opp: Dict, dry_run: bool = False) -> bool:
    """
    Create a follow-up task for a stale deal.
    v2.0: Task Owner from Primary Company Owner, linked to Company.
    """
    title = f"STALE DEAL: Follow up on {opp['title']}"
    due = (datetime.now(timezone.utc) + timedelta(hours=24)).strftime("%Y-%m-%dT%H:%M:%S.000+00:00")
    context = (
        f"This deal ({opp['stage']}) has not been updated in {STALE_DEAL_DAYS}+ days. "
        f"Follow up with the company to check status and update the opportunity."
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

    # Company relation (primary link in v2.0)
    if opp.get("company_ids"):
        properties[FIELD_TASK_COMPANY] = {"relation": [{"id": opp["company_ids"][0]}]}

        # Fetch Primary Company Owner for Task Owner
        company_info = fetch_company_info(opp["company_ids"][0])
        if company_info and company_info.get("primary_owner"):
            properties[FIELD_TASK_OWNER] = {"select": {"name": company_info["primary_owner"]}}
            properties[FIELD_OWNER_SOURCE] = {"select": {"name": "Company Primary"}}

    # Contact relation (secondary — first contact if available)
    if opp.get("contact_ids"):
        properties[FIELD_TASK_CONTACT] = {"relation": [{"id": opp["contact_ids"][0]}]}

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
    parser = argparse.ArgumentParser(description="AI Sales OS — Opportunity Manager v2.0 (Company-Centric)")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing")
    parser.add_argument("--limit", type=int, default=50, help="Max opportunities to create")
    parser.add_argument("--stale-only", action="store_true", help="Only check for stale deals")
    args = parser.parse_args()

    logger.info("=" * 70)
    logger.info(f"OPPORTUNITY MANAGER v2.0 (Company-Centric) | Dry Run: {args.dry_run}")
    logger.info("=" * 70)

    start_time = time.time()

    if not NOTION_DATABASE_ID_OPPORTUNITIES:
        logger.error("NOTION_DATABASE_ID_OPPORTUNITIES not set. Add to .env.")
        sys.exit(1)

    stats = {
        "meetings_found": 0,
        "companies_with_meetings": 0,
        "opps_created": 0,
        "opps_advanced": 0,
        "contacts_updated": 0,
        "skipped_existing": 0,
        "stakeholders_updated": 0,
        "company_stages_updated": 0,
        "stale_deals": 0,
        "stale_tasks": 0,
        "errors": 0,
    }

    # ── Part 1: Create/Update Opportunities from Positive Meetings ──

    if not args.stale_only:
        logger.info("Part 1: Processing positive meetings → opportunities (Company-Centric)...")

        meetings = fetch_positive_meetings_without_opportunity()
        stats["meetings_found"] = len(meetings)

        if meetings:
            # v2.0: Group meetings by COMPANY, not by contact
            company_meetings = group_meetings_by_company(meetings)
            stats["companies_with_meetings"] = len(company_meetings)
            logger.info(f"  Grouped into {len(company_meetings)} companies")

            # Batch-check which companies already have open opportunities
            company_ids = list(company_meetings.keys())
            existing_opps = fetch_existing_opportunities_for_companies(company_ids)

            processed = 0
            for company_id, comp_meetings in company_meetings.items():
                if processed >= args.limit:
                    break

                # Collect all unique contact IDs across all meetings for this company
                all_contact_ids = []
                for m in comp_meetings:
                    for cid in m.get("contact_ids", []):
                        if cid not in all_contact_ids:
                            all_contact_ids.append(cid)

                if not all_contact_ids:
                    logger.warning(f"  Skipping company {company_id} — no contacts in meetings")
                    continue

                # Fetch stakeholder info for all contacts
                stakeholder_infos = []
                for cid in all_contact_ids:
                    info = fetch_contact_info(cid)
                    if info:
                        stakeholder_infos.append(info)

                # Sort stakeholders by score (highest first) for primary contact selection
                scored_contacts = sorted(
                    zip(all_contact_ids, stakeholder_infos),
                    key=lambda x: x[1].get("score", 0) if x[1] else 0,
                    reverse=True,
                )
                all_contact_ids = [c[0] for c in scored_contacts]
                stakeholder_infos = [c[1] for c in scored_contacts]

                existing = existing_opps.get(company_id)

                if existing:
                    # Company already has an open opportunity → advance stage + update stakeholders
                    stats["skipped_existing"] += 1
                    opp_id = existing["opp_id"]
                    current_stage = existing["stage"]

                    logger.info(
                        f"  Company {company_id} already has opportunity {opp_id} "
                        f"(Stage: {current_stage}) — checking advancement"
                    )

                    # Try to advance stage with the best meeting type
                    for m in comp_meetings:
                        mt = m.get("meeting_type", "")
                        if mt:
                            advanced = advance_opportunity_stage(
                                opp_id, current_stage, mt, dry_run=args.dry_run
                            )
                            if advanced:
                                stats["opps_advanced"] += 1
                                # Update current_stage so subsequent meetings don't regress
                                target = STAGE_ADVANCE_MAP.get(mt, current_stage)
                                current_stage = target
                                break

                    # Update stakeholder count if new contacts appeared
                    updated = update_opportunity_stakeholders(
                        opp_id, all_contact_ids, existing.get("contact_ids", []),
                        dry_run=args.dry_run,
                    )
                    if updated:
                        stats["stakeholders_updated"] += 1

                    # Link all meetings to the existing opportunity
                    for m in comp_meetings:
                        link_meeting_to_opportunity(m["page_id"], opp_id, args.dry_run)

                    # Mark contacts as opportunity-created
                    for cid in all_contact_ids:
                        if update_contact_opportunity_created(cid, args.dry_run):
                            stats["contacts_updated"] += 1

                    continue

                # No existing opportunity → create one for the company
                company_info = fetch_company_info(company_id)

                opp_id = create_opportunity(
                    company_id=company_id,
                    company_info=company_info,
                    meetings=comp_meetings,
                    all_contact_ids=all_contact_ids,
                    stakeholder_infos=stakeholder_infos,
                    dry_run=args.dry_run,
                )

                if opp_id:
                    stats["opps_created"] += 1
                    processed += 1

                    # Link all meetings to the new opportunity
                    for m in comp_meetings:
                        link_meeting_to_opportunity(m["page_id"], opp_id, args.dry_run)

                    # Mark all contacts as opportunity-created
                    for cid in all_contact_ids:
                        if update_contact_opportunity_created(cid, args.dry_run):
                            stats["contacts_updated"] += 1

                    # Update Company Stage → Opportunity
                    if update_company_stage_to_opportunity(company_id, args.dry_run):
                        stats["company_stages_updated"] += 1
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
    logger.info("OPPORTUNITY MANAGER v2.0 SUMMARY")
    logger.info(f"  Positive meetings found:   {stats['meetings_found']}")
    logger.info(f"  Companies with meetings:   {stats['companies_with_meetings']}")
    logger.info(f"  Opportunities created:     {stats['opps_created']}")
    logger.info(f"  Opportunities advanced:    {stats['opps_advanced']}")
    logger.info(f"  Skipped (existing opp):    {stats['skipped_existing']}")
    logger.info(f"  Stakeholders updated:      {stats['stakeholders_updated']}")
    logger.info(f"  Company stages updated:    {stats['company_stages_updated']}")
    logger.info(f"  Contacts updated:          {stats['contacts_updated']}")
    logger.info(f"  Stale deals detected:      {stats['stale_deals']}")
    logger.info(f"  Stale deal tasks:          {stats['stale_tasks']}")
    logger.info(f"  Errors:                    {stats['errors']}")
    logger.info(f"  Runtime:                   {elapsed:.1f}s")
    logger.info("=" * 50)


if __name__ == "__main__":
    main()
