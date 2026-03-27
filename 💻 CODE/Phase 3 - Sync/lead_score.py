#!/usr/bin/env python3
"""
Lead Score Calculator — AI Sales OS

Calculates Lead Score for all contacts in Notion based on:
  - Company Size (45%)  — from related Company's employee count
  - Seniority (35%)     — from contact's Seniority field
  - Intent Score (10%)  — from Apollo Primary/Secondary Intent Score
  - Engagement (10%)    — from Outreach Status, Email, Replied, Meeting Booked

Now also writes Lead Tier (HOT/WARM/COLD) alongside Lead Score.

Usage:
    python lead_score.py              # score all contacts (skip if already scored)
    python lead_score.py --force      # recalculate ALL scores
    python lead_score.py --dry-run    # calculate but don't write to Notion
"""
import os
import sys
import logging
import time
import argparse
from typing import Dict, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.dirname(__file__))
from notion_helpers import (
    NOTION_DATABASE_ID_CONTACTS,
    NOTION_DATABASE_ID_COMPANIES,
    preload_companies,
    preload_contacts,
    update_page,
    rate_limiter,
    notion_request,
    NOTION_BASE_URL,
)
from constants import (
    FIELD_LEAD_SCORE, FIELD_LEAD_TIER, FIELD_INTENT_SCORE_PRIMARY,
    FIELD_INTENT_SCORE_SECONDARY, FIELD_SENIORITY, FIELD_OUTREACH_STATUS,
    FIELD_REPLY_STATUS, FIELD_QUALIFICATION_STATUS,
    FIELD_EMAIL_SENT, FIELD_EMAIL_OPENED, FIELD_REPLIED,
    FIELD_MEETING_BOOKED, FIELD_DEMOED, FIELD_EMPLOYEES,
    SCORE_HOT, SCORE_WARM,
)

# ─── Config ──────────────────────────────────────────────────────────────────

MAX_WORKERS = 3

# ─── Logging ─────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("lead_score.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)

# ─── Scoring Weights ─────────────────────────────────────────────────────────

# v1.1 weights — adjusted for available data (no intent/engagement yet)
# Will switch to v2.0 weights once signals & outreach data exist:
#   WEIGHT_INTENT = 0.30, WEIGHT_ENGAGEMENT = 0.25,
#   WEIGHT_SIGNALS = 0.25, WEIGHT_SIZE = 0.10, WEIGHT_SENIORITY = 0.10
WEIGHT_INTENT = 0.10       # low — mostly empty until Apollo enrichment
WEIGHT_ENGAGEMENT = 0.10   # low — no outreach data yet
WEIGHT_SIZE = 0.45         # high — employee count is our best signal now
WEIGHT_SENIORITY = 0.35   # high — decision-maker level matters most early on

# Seniority → score (0-100)
SENIORITY_SCORES = {
    "c-suite": 100,
    "c suite": 100,
    "founder": 95,
    "owner": 95,
    "partner": 90,
    "vp": 85,
    "head": 80,
    "director": 75,
    "senior": 65,
    "manager": 60,
    "individual contributor": 40,
    "entry": 25,
    "intern": 15,
    "unknown": 30,
}

# Employee count → score (0-100)
def employee_score(count: Optional[int]) -> float:
    if not count or count <= 0:
        return 20  # unknown = low-mid
    if count >= 10000:
        return 100
    if count >= 5000:
        return 90
    if count >= 1000:
        return 80
    if count >= 500:
        return 70
    if count >= 200:
        return 60
    if count >= 50:
        return 45
    if count >= 10:
        return 30
    return 20


# Engagement score based on outreach activity
def engagement_score(contact: Dict) -> float:
    """
    Calculate engagement score (0-100) based on outreach activity fields.
    """
    score = 0.0

    # Meeting Booked = highest engagement signal
    if contact.get("meeting_booked"):
        score += 40

    # Replied = strong signal
    if contact.get("replied"):
        score += 30

    # Email interactions
    if contact.get("email_opened"):
        score += 10
    if contact.get("email_sent"):
        score += 5

    # Outreach status signals
    outreach = (contact.get("outreach_status") or "").lower()
    outreach_scores = {
        "meeting booked": 15,
        "replied": 12,
        "opened": 8,
        "in sequence": 5,
        "sent": 3,
    }
    score += outreach_scores.get(outreach, 0)

    # Reply status
    reply = (contact.get("reply_status") or "").lower()
    if reply == "positive":
        score += 20
    elif reply == "replied":
        score += 10
    elif reply == "neutral":
        score += 5

    # Qualification status
    qual = (contact.get("qualification_status") or "").lower()
    if qual == "qualified":
        score += 15
    elif qual == "in progress":
        score += 5

    # Demoed
    if contact.get("demoed"):
        score += 15

    return min(score, 100)  # cap at 100


# ─── Fetch All Contacts with Scoring Fields ─────────────────────────────────

def fetch_contacts_for_scoring(force: bool = False) -> List[Dict]:
    """
    Fetch all contacts from Notion with fields needed for scoring.
    If not force, only fetch contacts without a Lead Score.
    """
    all_contacts = []
    has_more = True
    next_cursor = None

    logger.info("Fetching contacts from Notion for scoring...")

    while has_more:
        body = {
            "page_size": 100,
        }

        if not force:
            # Only contacts where Lead Score is empty
            body["filter"] = {
                "property": FIELD_LEAD_SCORE,
                "number": {"is_empty": True},
            }

        if next_cursor:
            body["start_cursor"] = next_cursor

        rate_limiter.wait()
        try:
            resp = notion_request(
                "POST",
                f"{NOTION_BASE_URL}/databases/{NOTION_DATABASE_ID_CONTACTS}/query",
                json=body,
            )
            data = resp.json()
        except Exception as e:
            if "start_cursor" in str(e) and next_cursor:
                logger.warning(f"Cursor expired at {len(all_contacts)} contacts, retrying without cursor...")
                next_cursor = None
                continue
            logger.warning(f"Pagination error after {len(all_contacts)} contacts: {e}")
            logger.warning("Continuing with contacts fetched so far...")
            break

        if not data or "results" not in data:
            if data and data.get("code") == "validation_error":
                logger.warning(f"Validation error at {len(all_contacts)} contacts, retrying without cursor...")
                next_cursor = None
                continue
            break

        for page in data.get("results", []):
            props = page.get("properties", {})

            # Extract checkbox values
            def get_checkbox(p: str) -> bool:
                v = props.get(p, {})
                return v.get("checkbox", False) if v.get("type") == "checkbox" else False

            # Extract select value
            def get_select(p: str) -> Optional[str]:
                v = props.get(p, {})
                sel = v.get("select")
                return sel.get("name") if sel else None

            # Extract number value
            def get_number(p: str) -> Optional[float]:
                v = props.get(p, {})
                return v.get("number")

            # Extract relation IDs
            def get_relation_ids(p: str) -> List[str]:
                v = props.get(p, {})
                return [r.get("id") for r in v.get("relation", []) if r.get("id")]

            contact = {
                "page_id": page["id"],
                "primary_intent_score": get_number(FIELD_INTENT_SCORE_PRIMARY),
                "secondary_intent_score": get_number(FIELD_INTENT_SCORE_SECONDARY),
                "seniority": get_select(FIELD_SENIORITY),
                "outreach_status": get_select(FIELD_OUTREACH_STATUS),
                "reply_status": get_select(FIELD_REPLY_STATUS),
                "qualification_status": get_select(FIELD_QUALIFICATION_STATUS),
                "email_sent": get_checkbox(FIELD_EMAIL_SENT),
                "email_opened": get_checkbox(FIELD_EMAIL_OPENED),
                "replied": get_checkbox(FIELD_REPLIED),
                "meeting_booked": get_checkbox(FIELD_MEETING_BOOKED),
                "demoed": get_checkbox(FIELD_DEMOED),
                "company_ids": get_relation_ids("Company"),
                "current_score": get_number(FIELD_LEAD_SCORE),
            }
            all_contacts.append(contact)

        has_more = data.get("has_more", False)
        next_cursor = data.get("next_cursor")

        if len(all_contacts) % 500 == 0 and all_contacts:
            logger.info(f"  Fetched {len(all_contacts)} contacts so far...")

    logger.info(f"Fetched {len(all_contacts)} contacts for scoring")
    return all_contacts


def fetch_company_employees() -> Dict[str, Optional[int]]:
    """
    Fetch all companies and their employee counts.
    Returns {page_id: employee_count}
    """
    company_employees = {}
    has_more = True
    next_cursor = None

    logger.info("Fetching company employee data...")

    while has_more:
        body = {"page_size": 100}
        if next_cursor:
            body["start_cursor"] = next_cursor

        rate_limiter.wait()
        try:
            resp = notion_request(
                "POST",
                f"{NOTION_BASE_URL}/databases/{NOTION_DATABASE_ID_COMPANIES}/query",
                json=body,
            )
            data = resp.json()
        except Exception as e:
            logger.warning(f"Pagination error after {len(company_employees)} companies: {e}")
            logger.warning("Continuing with companies fetched so far...")
            break

        if not data:
            break

        for page in data.get("results", []):
            props = page.get("properties", {})
            emp_prop = props.get(FIELD_EMPLOYEES, {})
            emp_count = emp_prop.get("number") if emp_prop.get("type") == "number" else None
            company_employees[page["id"]] = emp_count

        has_more = data.get("has_more", False)
        next_cursor = data.get("next_cursor")

    logger.info(f"Fetched employee data for {len(company_employees)} companies")
    return company_employees


# ─── Score Calculation ───────────────────────────────────────────────────────

def calculate_lead_score(contact: Dict, company_employees: Dict) -> Tuple[float, Dict]:
    """
    Calculate lead score (0-100) for a contact.
    Returns (score, breakdown_dict).
    """
    # 1. Intent Score (0-100) — use max of primary and secondary
    primary_intent = contact.get("primary_intent_score") or 0
    secondary_intent = contact.get("secondary_intent_score") or 0
    intent = max(primary_intent, secondary_intent)
    intent = min(max(intent, 0), 100)  # clamp 0-100

    # 2. Engagement Score (0-100)
    engage = engagement_score(contact)

    # 3. Company Size Score (0-100)
    emp_count = None
    for cid in (contact.get("company_ids") or []):
        emp_count = company_employees.get(cid)
        if emp_count:
            break
    size = employee_score(emp_count)

    # 4. Seniority Score (0-100)
    seniority_raw = (contact.get("seniority") or "unknown").lower()
    seniority = SENIORITY_SCORES.get(seniority_raw, 30)

    # Weighted total
    total = (
        intent * WEIGHT_INTENT
        + engage * WEIGHT_ENGAGEMENT
        + size * WEIGHT_SIZE
        + seniority * WEIGHT_SENIORITY
    )
    total = round(min(max(total, 0), 100), 1)

    breakdown = {
        "intent": round(intent, 1),
        "engagement": round(engage, 1),
        "size": round(size, 1),
        "seniority": round(seniority, 1),
        "total": total,
    }

    return total, breakdown


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Lead Score Calculator — AI Sales OS")
    parser.add_argument("--force", action="store_true", help="Recalculate ALL scores (even existing)")
    parser.add_argument("--dry-run", action="store_true", help="Calculate but don't write to Notion")
    args = parser.parse_args()

    logger.info("=" * 80)
    logger.info(f"LEAD SCORE CALCULATOR | Force: {args.force} | Dry Run: {args.dry_run}")
    logger.info("=" * 80)

    start_time = time.time()

    # Step 1: Fetch company employee data
    company_employees = fetch_company_employees()

    # Step 2: Fetch contacts
    contacts = fetch_contacts_for_scoring(force=args.force)

    if not contacts:
        logger.info("No contacts to score. Done!")
        return

    # Step 3: Calculate scores
    logger.info(f"Calculating scores for {len(contacts)} contacts...")

    scored = []
    score_distribution = {"hot": 0, "warm": 0, "cold": 0, "zero": 0}

    for c in contacts:
        score, breakdown = calculate_lead_score(c, company_employees)
        c["new_score"] = score
        c["breakdown"] = breakdown
        scored.append(c)

        if score >= 80:
            score_distribution["hot"] += 1
        elif score >= 50:
            score_distribution["warm"] += 1
        elif score > 0:
            score_distribution["cold"] += 1
        else:
            score_distribution["zero"] += 1

    logger.info(f"Score distribution: {score_distribution}")
    logger.info(f"  HOT (80+):   {score_distribution['hot']}")
    logger.info(f"  WARM (50-79): {score_distribution['warm']}")
    logger.info(f"  COLD (<50):   {score_distribution['cold']}")
    logger.info(f"  ZERO (0):     {score_distribution['zero']}")

    if args.dry_run:
        logger.info("DRY RUN — not writing to Notion")
        # Show sample scores
        for c in scored[:10]:
            logger.info(f"  Sample: score={c['new_score']} breakdown={c['breakdown']}")
        elapsed = time.time() - start_time
        logger.info(f"Done in {elapsed:.1f}s")
        return

    # Step 4: Write scores to Notion
    logger.info(f"Writing scores to Notion for {len(scored)} contacts...")
    stats = {"updated": 0, "skipped": 0, "errors": 0}

    def _get_tier(score: float) -> str:
        """Determine Lead Tier from score."""
        if score >= SCORE_HOT:
            return "HOT"
        elif score >= SCORE_WARM:
            return "WARM"
        return "COLD"

    def write_score(contact):
        page_id = contact["page_id"]
        new_score = contact["new_score"]
        current = contact.get("current_score")
        tier = _get_tier(new_score)

        # Skip if score hasn't changed (within 0.1)
        if current is not None and abs(current - new_score) < 0.1:
            return "skipped"

        try:
            update_page(page_id, {
                FIELD_LEAD_SCORE: {"number": new_score},
                FIELD_LEAD_TIER: {"select": {"name": tier}},
            })
            return "updated"
        except Exception as e:
            logger.error(f"Error writing score for {page_id}: {e}")
            return "error"

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(write_score, c): c for c in scored}
        for i, fut in enumerate(as_completed(futures), 1):
            result = fut.result()
            if result == "updated":
                stats["updated"] += 1
            elif result == "skipped":
                stats["skipped"] += 1
            else:
                stats["errors"] += 1

            if i % 200 == 0:
                logger.info(f"  Progress: {i}/{len(scored)} | {stats}")

    elapsed = time.time() - start_time

    logger.info("=" * 80)
    logger.info(f"LEAD SCORE COMPLETE")
    logger.info(f"  Updated: {stats['updated']}")
    logger.info(f"  Skipped (unchanged): {stats['skipped']}")
    logger.info(f"  Errors: {stats['errors']}")
    logger.info(f"  Distribution: HOT={score_distribution['hot']} | WARM={score_distribution['warm']} | COLD={score_distribution['cold']}")
    logger.info(f"  Time: {elapsed / 60:.1f} minutes")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
