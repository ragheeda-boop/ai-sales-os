#!/usr/bin/env python3
"""
Lead Score Calculator — AI Sales OS v1.5

Calculates Lead Score for all contacts in Notion based on:
  - Company Size (35%)     — from related Company's employee count
  - Seniority (30%)        — from contact's Seniority field
  - Industry Fit (15%)     — MUHIDE ICP alignment score (new v1.5)
  - Intent Score (10%)     — from Apollo Primary/Secondary Intent Score
  - Engagement (10%)       — from Outreach Status, Email, Replied, Meeting Booked

Also writes:
  - Lead Tier (HOT/WARM/COLD) alongside Lead Score
  - Sort Score = (Lead Score × 100) + Recency Bonus (0-100)
    → Sorts HOT leads by score first, then by recency (untouched leads surface first)

Changelog:
  v1.5 — Added Industry Fit Score (15%), Recency Tiebreaker (Sort Score),
          adjusted weights: Size 35% (-10%), Seniority 30% (-5%), Industry +15%

Usage:
    python lead_score.py              # score all contacts (skip if already scored)
    python lead_score.py --force      # recalculate ALL scores
    python lead_score.py --dry-run    # calculate but don't write to Notion
"""
import sys as _sys, os as _os; _sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
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
from core.notion_helpers import (
    NOTION_DATABASE_ID_CONTACTS,
    NOTION_DATABASE_ID_COMPANIES,
    preload_companies,
    preload_contacts,
    update_page,
    rate_limiter,
    notion_request,
    NOTION_BASE_URL,
)
from core.constants import (
    FIELD_LEAD_SCORE, FIELD_LEAD_TIER, FIELD_SORT_SCORE,
    FIELD_INTENT_SCORE_PRIMARY, FIELD_INTENT_SCORE_SECONDARY,
    FIELD_SENIORITY, FIELD_OUTREACH_STATUS,
    FIELD_REPLY_STATUS, FIELD_AI_REPLY_STATUS, FIELD_QUALIFICATION_STATUS,
    FIELD_EMAIL_SENT, FIELD_EMAIL_OPENED, FIELD_REPLIED,
    FIELD_MEETING_BOOKED, FIELD_DEMOED, FIELD_EMPLOYEES,
    FIELD_INDUSTRY, FIELD_LAST_CONTACTED,
    FIELD_MUHIDE_FIT_SCORE,
    SCORE_HOT, SCORE_WARM,
    ICP_INDUSTRY_SCORES, ICP_INDUSTRY_DEFAULT_SCORE,
    # AI Sales Actions boost (conservative, Phase 5)
    FIELD_AI_PRIORITY, FIELD_AI_FIT,
    AI_PRIORITY_BOOST, AI_FIT_BOOST, AI_SCORE_BOOST_MAX,
)

# ─── Config ──────────────────────────────────────────────────────────────────

MAX_WORKERS = 3

# ─── Logging ─────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(os.path.dirname(os.path.abspath(__file__)), "lead_score.log"), encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)

# ─── Scoring Weights ─────────────────────────────────────────────────────────

# v1.5 weights — added Industry Fit (15%), adjusted Size and Seniority down
# v1.1 → v1.5 changes: Size 45%→35%, Seniority 35%→30%, Industry 0%→15%
# Will switch to v2.0 weights once signals & outreach data exist:
#   WEIGHT_INTENT = 0.30, WEIGHT_ENGAGEMENT = 0.25,
#   WEIGHT_SIGNALS = 0.25, WEIGHT_SIZE = 0.10, WEIGHT_SENIORITY = 0.10
WEIGHT_INTENT = 0.10       # low — mostly empty until Apollo enrichment
WEIGHT_ENGAGEMENT = 0.10   # low — no outreach data yet
WEIGHT_SIZE = 0.35         # reduced from 0.45 — balanced with Industry Fit
WEIGHT_SENIORITY = 0.30    # reduced from 0.35 — balanced with Industry Fit
WEIGHT_INDUSTRY = 0.15     # NEW v1.5 — MUHIDE ICP industry alignment

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

    # AI Reply Status — written by reply_intelligence.py (P1-2 fix, v6.3)
    # Values: Interested / Soft Interest / Neutral / Soft Rejection / Hard Rejection
    ai_reply = (contact.get("ai_reply_status") or "").lower()
    if ai_reply == "interested":
        score += 20
    elif ai_reply == "soft interest":
        score += 10
    elif ai_reply == "neutral":
        score += 5

    # Reply Status (legacy Apollo field — rarely populated, kept for backward compat)
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


def industry_fit_score(industry: Optional[str]) -> float:
    """
    Calculate industry fit score (0-100) based on MUHIDE ICP alignment.
    Uses ICP_INDUSTRY_SCORES from constants.py.
    Returns ICP_INDUSTRY_DEFAULT_SCORE (30) for unknown/unmapped industries.
    """
    if not industry or not str(industry).strip():
        return ICP_INDUSTRY_DEFAULT_SCORE

    industry_lower = str(industry).strip().lower()

    # Direct match
    if industry_lower in ICP_INDUSTRY_SCORES:
        return float(ICP_INDUSTRY_SCORES[industry_lower])

    # Partial match — find highest scoring industry that is a substring
    best_score = ICP_INDUSTRY_DEFAULT_SCORE
    for key, score in ICP_INDUSTRY_SCORES.items():
        if key in industry_lower or industry_lower in key:
            if score > best_score:
                best_score = score

    return float(best_score)


def recency_bonus(last_contacted_str: Optional[str]) -> float:
    """
    Calculate recency bonus (0-100) for Sort Score tiebreaker.

    Logic: contacts NOT recently contacted surface FIRST in the HOT view.
    This ensures the sales team prioritizes cold HOT leads (untouched) over
    leads already contacted this week.

    Returns:
        100  — never contacted (highest priority)
        80   — last contacted > 30 days ago
        60   — last contacted 15-30 days ago
        40   — last contacted 7-15 days ago
        20   — last contacted 3-7 days ago
        5    — last contacted < 3 days (just reached out, hold off)
    """
    if not last_contacted_str:
        return 100.0  # Never contacted — highest priority

    try:
        from datetime import datetime, timezone
        # Parse ISO date string (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS...)
        date_str = str(last_contacted_str)[:10]
        last_dt = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        now = datetime.now(tz=timezone.utc)
        days_ago = (now - last_dt).days

        if days_ago > 30:
            return 80.0
        elif days_ago > 15:
            return 60.0
        elif days_ago > 7:
            return 40.0
        elif days_ago > 3:
            return 20.0
        else:
            return 5.0
    except Exception:
        return 100.0  # If date parsing fails, treat as never contacted


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
        cursor_retries = 0
        max_cursor_retries = 3
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
            error_code = data.get("code", "") if data else ""
            error_msg = data.get("message", "") if data else ""
            if ("validation_error" in error_code or "start_cursor" in error_msg) and cursor_retries < max_cursor_retries:
                cursor_retries += 1
                logger.warning(f"Cursor invalid at {len(all_contacts)} contacts (attempt {cursor_retries}), resetting cursor...")
                next_cursor = None
                continue
            if data:
                logger.warning(f"API error at {len(all_contacts)} contacts: {error_code} — {error_msg}")
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

            # Extract date value (ISO string or None)
            def get_date(p: str) -> Optional[str]:
                v = props.get(p, {})
                d = v.get("date")
                return d.get("start") if d else None

            contact = {
                "page_id": page["id"],
                "primary_intent_score": get_number(FIELD_INTENT_SCORE_PRIMARY),
                "secondary_intent_score": get_number(FIELD_INTENT_SCORE_SECONDARY),
                "seniority": get_select(FIELD_SENIORITY),
                "outreach_status": get_select(FIELD_OUTREACH_STATUS),
                "reply_status": get_select(FIELD_REPLY_STATUS),
                "ai_reply_status": get_select(FIELD_AI_REPLY_STATUS),
                "qualification_status": get_select(FIELD_QUALIFICATION_STATUS),
                "email_sent": get_checkbox(FIELD_EMAIL_SENT),
                "email_opened": get_checkbox(FIELD_EMAIL_OPENED),
                "replied": get_checkbox(FIELD_REPLIED),
                "meeting_booked": get_checkbox(FIELD_MEETING_BOOKED),
                "demoed": get_checkbox(FIELD_DEMOED),
                "company_ids": get_relation_ids("Company"),
                "current_score": get_number(FIELD_LEAD_SCORE),
                "last_contacted": get_date(FIELD_LAST_CONTACTED),  # v1.5 — for recency bonus
            }
            all_contacts.append(contact)

        has_more = data.get("has_more", False)
        next_cursor = data.get("next_cursor")

        if len(all_contacts) % 500 == 0 and all_contacts:
            logger.info(f"  Fetched {len(all_contacts)} contacts so far...")

    logger.info(f"Fetched {len(all_contacts)} contacts for scoring")
    return all_contacts


def fetch_company_data() -> Dict[str, Dict]:
    """
    Fetch all companies with employee counts and industry.
    Returns {page_id: {"employees": int_or_None, "industry": str_or_None}}

    v1.5: Added industry for ICP Industry Fit Score calculation.
    """
    company_data = {}
    has_more = True
    next_cursor = None

    logger.info("Fetching company data (employees + industry)...")

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
            logger.warning(f"Pagination error after {len(company_data)} companies: {e}")
            logger.warning("Continuing with companies fetched so far...")
            break

        if not data:
            break

        for page in data.get("results", []):
            props = page.get("properties", {})

            # Employee count
            emp_prop = props.get(FIELD_EMPLOYEES, {})
            emp_count = emp_prop.get("number") if emp_prop.get("type") == "number" else None

            # Industry (select field)
            industry_prop = props.get(FIELD_INDUSTRY, {})
            industry = None
            if industry_prop.get("type") == "select":
                sel = industry_prop.get("select")
                industry = sel.get("name") if sel else None
            elif industry_prop.get("type") == "rich_text":
                rt = industry_prop.get("rich_text", [])
                industry = rt[0].get("plain_text") if rt else None

            # MUHIDE Fit Score — AI-computed by muhide_strategic_analysis.py (1-100)
            # Used as primary industry_fit signal in lead scoring when available
            muhide_fit_prop = props.get(FIELD_MUHIDE_FIT_SCORE, {})
            muhide_fit = muhide_fit_prop.get("number") if muhide_fit_prop.get("type") == "number" else None

            # AI Sales Actions — conservative boost signals (Phase 5)
            ai_pri_sel = props.get(FIELD_AI_PRIORITY, {}).get("select")
            ai_priority = ai_pri_sel.get("name") if ai_pri_sel else None
            ai_fit_sel = props.get(FIELD_AI_FIT, {}).get("select")
            ai_fit = ai_fit_sel.get("name") if ai_fit_sel else None

            company_data[page["id"]] = {
                "employees": emp_count,
                "industry": industry,
                "muhide_fit": muhide_fit,  # None if not yet analyzed
                "ai_priority": ai_priority,  # P1/P2/P3 or None
                "ai_fit": ai_fit,            # High/Medium/Low or None
            }

        has_more = data.get("has_more", False)
        next_cursor = data.get("next_cursor")

    logger.info(f"Fetched data for {len(company_data)} companies")
    return company_data


# ─── Score Calculation ───────────────────────────────────────────────────────

def calculate_lead_score(contact: Dict, company_data: Dict) -> Tuple[float, Dict]:
    """
    Calculate lead score (0-100) and sort score for a contact.
    Returns (score, breakdown_dict).

    v1.5 formula:
        Score = Intent(10%) + Engagement(10%) + Size(35%) + Seniority(30%) + Industry(15%)
        Sort Score = (Lead Score × 100) + Recency Bonus (0-100)
    """
    # 1. Intent Score (0-100) — use max of primary and secondary
    primary_intent = contact.get("primary_intent_score") or 0
    secondary_intent = contact.get("secondary_intent_score") or 0
    intent = max(primary_intent, secondary_intent)
    intent = min(max(intent, 0), 100)  # clamp 0-100

    # 2. Engagement Score (0-100)
    engage = engagement_score(contact)

    # 3. Company Size Score (0-100) + Industry Fit Score (0-100)
    emp_count = None
    industry = None
    muhide_fit = None
    ai_priority = None
    ai_fit_label = None
    for cid in (contact.get("company_ids") or []):
        cdata = company_data.get(cid, {})
        if cdata.get("employees") and emp_count is None:
            emp_count = cdata["employees"]
        if cdata.get("industry") and industry is None:
            industry = cdata["industry"]
        if muhide_fit is None and cdata.get("muhide_fit") is not None:
            muhide_fit = cdata["muhide_fit"]
        if ai_priority is None and cdata.get("ai_priority"):
            ai_priority = cdata["ai_priority"]
        if ai_fit_label is None and cdata.get("ai_fit"):
            ai_fit_label = cdata["ai_fit"]
        if emp_count and industry and muhide_fit is not None and ai_priority and ai_fit_label:
            break

    size = employee_score(emp_count)

    # 4. Industry Fit Score (0-100) — v1.5
    # Priority: MUHIDE Fit Score (AI-computed per company) > industry name lookup table
    # MUHIDE Fit Score is generated by muhide_strategic_analysis.py using Claude API —
    # it accounts for company context, not just industry name, making it more accurate.
    if muhide_fit is not None:
        industry_fit = float(muhide_fit)
        industry_fit_source = "muhide_ai"
    else:
        industry_fit = industry_fit_score(industry)
        industry_fit_source = "industry_lookup"

    # 5. Seniority Score (0-100)
    seniority_raw = (contact.get("seniority") or "unknown").lower()
    seniority = SENIORITY_SCORES.get(seniority_raw, 30)

    # Weighted total (v1.5 formula)
    total = (
        intent * WEIGHT_INTENT
        + engage * WEIGHT_ENGAGEMENT
        + size * WEIGHT_SIZE
        + seniority * WEIGHT_SENIORITY
        + industry_fit * WEIGHT_INDUSTRY
    )

    # ── AI Sales Actions boost (Phase 5, conservative) ──
    # Additive points on top of the weighted total, capped at AI_SCORE_BOOST_MAX.
    # Apollo AI Priority/Fit acts as a nudge, not a rewrite of the base formula.
    # Total is always clamped to 0-100 AFTER the boost so no score can exceed 100.
    ai_priority_pts = AI_PRIORITY_BOOST.get(ai_priority or "", 0.0)
    ai_fit_pts = AI_FIT_BOOST.get(ai_fit_label or "", 0.0)
    ai_boost = min(ai_priority_pts + ai_fit_pts, AI_SCORE_BOOST_MAX)
    total += ai_boost

    total = round(min(max(total, 0), 100), 1)

    # Sort Score — tiebreaker for HOT leads at same score (v1.5)
    # Contacts not recently contacted surface first (recency_bonus higher = less recent)
    rec_bonus = recency_bonus(contact.get("last_contacted"))
    sort_score = round((total * 100) + rec_bonus, 0)

    breakdown = {
        "intent": round(intent, 1),
        "engagement": round(engage, 1),
        "size": round(size, 1),
        "industry_fit": round(industry_fit, 1),
        "industry_fit_source": industry_fit_source,  # "muhide_ai" or "industry_lookup"
        "industry": industry or "unknown",
        "muhide_fit_raw": muhide_fit,                # raw MUHIDE Fit Score (None if not analyzed)
        "seniority": round(seniority, 1),
        "ai_priority": ai_priority,
        "ai_fit": ai_fit_label,
        "ai_boost": round(ai_boost, 1),
        "total": total,
        "sort_score": sort_score,
        "recency_bonus": rec_bonus,
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

    # Step 1: Fetch company data (employees + industry)
    company_employees = fetch_company_data()

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
        # Show sample scores with v1.5 breakdown
        for c in scored[:10]:
            bd = c['breakdown']
            fit_src = bd.get('industry_fit_source', '?')
            muhide_raw = bd.get('muhide_fit_raw')
            fit_label = f"MUHIDE={muhide_raw}" if fit_src == "muhide_ai" else f"lookup({bd.get('industry','?')})"
            logger.info(
                f"  score={c['new_score']} | industry_fit={bd.get('industry_fit',0)} [{fit_label}] "
                f"| sort={bd.get('sort_score',0)} recency={bd.get('recency_bonus',0)}"
            )
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
        sort_score = contact["breakdown"].get("sort_score", new_score * 100)

        # Skip if score hasn't changed (within 0.1)
        if current is not None and abs(current - new_score) < 0.1:
            return "skipped"

        try:
            props = {
                FIELD_LEAD_SCORE: {"number": new_score},
                FIELD_LEAD_TIER: {"select": {"name": tier}},
                FIELD_SORT_SCORE: {"number": sort_score},
            }
            update_page(page_id, props)
            return "updated"
        except Exception as e:
            # If Sort Score field doesn't exist in Notion yet, retry without it
            if "sort score" in str(e).lower() or "property" in str(e).lower():
                try:
                    update_page(page_id, {
                        FIELD_LEAD_SCORE: {"number": new_score},
                        FIELD_LEAD_TIER: {"select": {"name": tier}},
                    })
                    logger.warning(f"Sort Score field missing in Notion — skipped for {page_id}")
                    return "updated"
                except Exception as e2:
                    logger.error(f"Error writing score for {page_id}: {e2}")
                    return "error"
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
    logger.info(f"  Formula v1.5: Size(35%) + Seniority(30%) + Industry(15%) + Intent(10%) + Engagement(10%)")
    logger.info(f"  Sort Score: (Lead Score x 100) + Recency Bonus -- sorts untouched leads first")
    logger.info(f"  Time: {elapsed / 60:.1f} minutes")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
