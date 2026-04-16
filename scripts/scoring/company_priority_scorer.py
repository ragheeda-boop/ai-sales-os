#!/usr/bin/env python3
"""
AI Sales OS — Company Priority Scorer (Decision Layer v7.0)

Computes a single Company Priority Score (CPS) per active company that unifies
all scoring signals into one decision. Replaces the fragmented Lead Tier system
as the primary driver of daily sales execution.

Formula:
    CPS = (BCS x 25%) + (ENG x 25%) + (FIT x 20%) + (AIS x 15%) + (MOM x 15%)

Where:
    BCS = Best Contact Score (max Lead Score among company contacts)
    ENG = Engagement Index (replied, meeting, opens, forwards)
    FIT = Firmographic Fit (industry + size)
    AIS = AI Signal Strength (AI Priority + AI Qualification + MUHIDE Fit)
    MOM = Momentum Score (stage movement + freshness)

Outputs per company (7 fields):
    1. Company Priority Score (0-100)
    2. Priority Tier (P1/P2/P3)
    3. Best Contact (name + ID)
    4. Next Action (Call/Email/Sequence/Wait/Review)
    5. Priority Reason (top 3 reasons)
    6. Action Owner (= Primary Company Owner)
    7. Action SLA (24h/48h/7d/None)

Usage:
    python scoring/company_priority_scorer.py                    # dry-run
    python scoring/company_priority_scorer.py --execute          # apply writes
    python scoring/company_priority_scorer.py --execute --force  # recompute all
    python scoring/company_priority_scorer.py --limit 50         # test batch
"""

import os
import sys
import json
import logging
import argparse
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv

# ── Path setup ────────────────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_ROOT = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, SCRIPTS_ROOT)

load_dotenv(os.path.join(SCRIPTS_ROOT, ".env"))

from core.constants import (
    # CPS fields
    FIELD_COMPANY_PRIORITY_SCORE, FIELD_PRIORITY_TIER, FIELD_BEST_CONTACT,
    FIELD_NEXT_ACTION, FIELD_PRIORITY_REASON, FIELD_ACTION_OWNER,
    FIELD_ACTION_SLA, FIELD_AI_RISK_FLAG,
    # CPS weights
    CPS_WEIGHT_BEST_CONTACT, CPS_WEIGHT_ENGAGEMENT, CPS_WEIGHT_FIRMOGRAPHIC,
    CPS_WEIGHT_AI_SIGNAL, CPS_WEIGHT_MOMENTUM,
    # CPS thresholds
    CPS_TIER_P1, CPS_TIER_P2,
    PRIORITY_P1, PRIORITY_P2, PRIORITY_P3,
    ACTION_CALL, ACTION_EMAIL, ACTION_SEQUENCE, ACTION_WAIT, ACTION_REVIEW,
    SLA_24H, SLA_48H, SLA_7D, SLA_NONE,
    # Firmographic sub-weights
    CPS_FIT_INDUSTRY_WEIGHT, CPS_FIT_SIZE_WEIGHT,
    # AI Signal sub-weights + maps
    CPS_AI_PRIORITY_WEIGHT, CPS_AI_QUAL_WEIGHT, CPS_AI_MUHIDE_WEIGHT,
    AI_PRIORITY_SCORE, AI_QUAL_SCORE,
    # Momentum constants
    MOMENTUM_STAGE_ADVANCED_7D, MOMENTUM_ACTIVITY_3D, MOMENTUM_ACTIVITY_7D,
    MOMENTUM_ACTIVITY_14D, MOMENTUM_MULTI_ENGAGED, MOMENTUM_NEW_CONTACT_7D,
    # Guards
    CPS_AI_DISQUALIFIED_CAP, CPS_MIN_COMPONENTS,
    # Existing fields
    FIELD_LEAD_SCORE, FIELD_LEAD_TIER, FIELD_ACTION_READY,
    FIELD_PRIMARY_COMPANY_OWNER, FIELD_COMPANY_STAGE, FIELD_SALES_OS_ACTIVE,
    FIELD_ACTIVE_CONTACTS, FIELD_ENGAGED_CONTACTS, FIELD_LAST_ENGAGEMENT_DATE,
    FIELD_INDUSTRY, FIELD_EMPLOYEES, FIELD_AI_PRIORITY, FIELD_AI_QUALIFICATION_STATUS,
    FIELD_AI_ACTION_TYPE, FIELD_AI_CALL_HOOK, FIELD_MUHIDE_FIT_SCORE,
    FIELD_REPLIED, FIELD_MEETING_BOOKED, FIELD_EMAIL_SENT, FIELD_EMAIL_OPEN_COUNT,
    FIELD_SENIORITY, FIELD_FULL_NAME, FIELD_EMAIL, FIELD_WORK_PHONE,
    FIELD_MOBILE_PHONE, FIELD_DO_NOT_CALL, FIELD_OUTREACH_STATUS,
    FIELD_COMPANY_RELATION, FIELD_APOLLO_ACCOUNT_ID,
    # Stage
    STAGE_TERMINAL, STAGE_PRIORITY,
    # ICP
    ICP_INDUSTRY_SCORES, ICP_INDUSTRY_DEFAULT_SCORE,
    # Misc
    OUTREACH_BLOCKED, TEAM_MEMBERS,
)
from core.notion_helpers import notion_request

# ── Logging ───────────────────────────────────────────────────────────────────

LOG_FILE = os.path.join(SCRIPT_DIR, "company_priority_scorer.log")
logger = logging.getLogger("company_priority_scorer")
logger.setLevel(logging.INFO)
handler = RotatingFileHandler(LOG_FILE, maxBytes=5_000_000, backupCount=3, encoding="utf-8")
handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
logger.addHandler(handler)
logger.addHandler(logging.StreamHandler(sys.stdout))

# ── Notion Config ─────────────────────────────────────────────────────────────

NOTION_API_KEY = os.getenv("NOTION_API_KEY")
COMPANIES_DB_ID = os.getenv("NOTION_DATABASE_ID_COMPANIES")
CONTACTS_DB_ID = os.getenv("NOTION_DATABASE_ID_CONTACTS")

NOTION_HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28",
}

STATS_FILE = os.path.join(SCRIPT_DIR, "last_cps_stats.json")


# ═══════════════════════════════════════════════════════════════════════════════
# NOTION HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def _get_text(props: dict, field: str) -> str:
    """Extract plain text from a Notion property."""
    p = props.get(field, {})
    ptype = p.get("type", "")
    if ptype == "title":
        return "".join(t.get("plain_text", "") for t in p.get("title", []))
    if ptype == "rich_text":
        return "".join(t.get("plain_text", "") for t in p.get("rich_text", []))
    if ptype == "select":
        sel = p.get("select")
        return sel.get("name", "") if sel else ""
    if ptype == "number":
        val = p.get("number")
        return str(val) if val is not None else ""
    if ptype == "checkbox":
        return str(p.get("checkbox", False))
    if ptype == "date":
        d = p.get("date")
        return d.get("start", "") if d else ""
    if ptype == "status":
        s = p.get("status")
        return s.get("name", "") if s else ""
    return ""


def _get_number(props: dict, field: str) -> float:
    """Extract number from a Notion property."""
    p = props.get(field, {})
    if p.get("type") == "number":
        val = p.get("number")
        return float(val) if val is not None else 0.0
    # Try text fallback
    txt = _get_text(props, field)
    try:
        return float(txt)
    except (ValueError, TypeError):
        return 0.0


def _get_bool(props: dict, field: str) -> bool:
    """Extract boolean from a Notion property."""
    p = props.get(field, {})
    if p.get("type") == "checkbox":
        return p.get("checkbox", False)
    txt = _get_text(props, field)
    return txt.lower() in {"true", "yes", "1"}


def _get_relation_ids(props: dict, field: str) -> list:
    """Extract relation page IDs."""
    p = props.get(field, {})
    if p.get("type") == "relation":
        return [r.get("id", "") for r in p.get("relation", [])]
    return []


def preload_all(db_id: str, label: str = "records") -> list:
    """Paginate through entire DB and return all pages."""
    import requests
    url = f"https://api.notion.com/v1/databases/{db_id}/query"
    pages = []
    cursor = None
    while True:
        body = {"page_size": 100}
        if cursor:
            body["start_cursor"] = cursor
        resp = requests.post(url, headers=NOTION_HEADERS, json=body, timeout=60)
        if resp.status_code == 429:
            retry = int(resp.headers.get("Retry-After", 5))
            logger.warning(f"Rate limited, waiting {retry}s...")
            time.sleep(retry)
            continue
        resp.raise_for_status()
        data = resp.json()
        pages.extend(data.get("results", []))
        if not data.get("has_more", False):
            break
        cursor = data.get("next_cursor")
    logger.info(f"Preloaded {len(pages)} {label}")
    return pages


def update_page(page_id: str, properties: dict):
    """Update a Notion page."""
    import requests
    url = f"https://api.notion.com/v1/pages/{page_id}"
    resp = requests.patch(url, headers=NOTION_HEADERS, json={"properties": properties}, timeout=60)
    if resp.status_code == 429:
        retry = int(resp.headers.get("Retry-After", 5))
        logger.warning(f"Rate limited on update, waiting {retry}s...")
        time.sleep(retry)
        return update_page(page_id, properties)
    if resp.status_code >= 400:
        logger.error(f"  Notion API {resp.status_code} for page {page_id}: {resp.text[:500]}")
    resp.raise_for_status()
    return resp.json()


# ═══════════════════════════════════════════════════════════════════════════════
# SCORING COMPONENTS
# ═══════════════════════════════════════════════════════════════════════════════

SENIORITY_RANK = {
    "C-Suite": 100, "Founder": 95, "Owner": 95, "Partner": 90,
    "VP": 85, "Head": 80, "Director": 75, "Senior": 65,
    "Manager": 60, "": 30,
}


def employee_score(count: int) -> float:
    """Company size score (same logic as lead_score.py)."""
    if count >= 10000: return 100
    if count >= 5000: return 90
    if count >= 1000: return 80
    if count >= 500: return 70
    if count >= 200: return 60
    if count >= 50: return 45
    if count >= 10: return 30
    return 20


def compute_engagement_index(contacts: list) -> Tuple[float, list]:
    """Compute Engagement Index (0-100) for a company from its contacts."""
    score = 0.0
    reasons = []

    any_replied = any(_get_bool(c["properties"], FIELD_REPLIED) for c in contacts)
    any_meeting = any(_get_bool(c["properties"], FIELD_MEETING_BOOKED) for c in contacts)
    any_email_sent = any(_get_bool(c["properties"], FIELD_EMAIL_SENT) for c in contacts)
    max_open_count = max((_get_number(c["properties"], FIELD_EMAIL_OPEN_COUNT) for c in contacts), default=0)

    if any_replied:
        score += 40
        reasons.append("Contact replied")
    if any_meeting:
        score += 30
        reasons.append("Meeting booked")
    if max_open_count >= 2:
        score += 15
        reasons.append(f"Email opened {int(max_open_count)}x")
    if any_email_sent:
        score += 10
        reasons.append("Email sent")

    return min(score, 100), reasons


def compute_firmographic_fit(props: dict) -> Tuple[float, list]:
    """Compute Firmographic Fit (0-100) from industry and size."""
    reasons = []

    # Industry fit
    industry = _get_text(props, FIELD_INDUSTRY).strip().lower()
    industry_score = ICP_INDUSTRY_SCORES.get(industry, ICP_INDUSTRY_DEFAULT_SCORE)
    if industry and industry_score >= 80:
        reasons.append(f"Industry: {industry.title()} ({industry_score})")

    # Size score
    emp = _get_number(props, FIELD_EMPLOYEES)
    size = employee_score(int(emp)) if emp > 0 else 20
    if emp >= 500:
        reasons.append(f"Large company ({int(emp)} employees)")

    fit = (industry_score * CPS_FIT_INDUSTRY_WEIGHT) + (size * CPS_FIT_SIZE_WEIGHT)
    return min(fit, 100), reasons


def compute_ai_signal(props: dict) -> Tuple[float, bool, list]:
    """Compute AI Signal Strength (0-100) + risk flag."""
    reasons = []
    populated = 0

    # AI Priority
    ai_priority = _get_text(props, FIELD_AI_PRIORITY)
    ai_p_score = AI_PRIORITY_SCORE.get(ai_priority, 0)
    if ai_priority:
        populated += 1
        if ai_priority == "P1":
            reasons.append("AI Priority: P1")

    # AI Qualification
    ai_qual = _get_text(props, FIELD_AI_QUALIFICATION_STATUS)
    ai_q_score = AI_QUAL_SCORE.get(ai_qual, 0)
    risk_flag = (ai_qual == "Disqualified")
    if ai_qual:
        populated += 1
        if ai_qual == "Qualified":
            reasons.append("AI Qualified")
        elif ai_qual == "Disqualified":
            reasons.append("AI Risk: Disqualified")

    # MUHIDE Fit
    muhide = _get_number(props, FIELD_MUHIDE_FIT_SCORE)
    if muhide > 0:
        populated += 1
        if muhide >= 70:
            reasons.append(f"MUHIDE Fit: {int(muhide)}")

    if populated == 0:
        return 0, risk_flag, reasons  # Will use fallback

    # Weighted combination of available signals
    signal = (ai_p_score * CPS_AI_PRIORITY_WEIGHT +
              ai_q_score * CPS_AI_QUAL_WEIGHT +
              muhide * CPS_AI_MUHIDE_WEIGHT)

    return min(signal, 100), risk_flag, reasons


def compute_momentum(props: dict, contacts: list) -> Tuple[float, list]:
    """Compute Momentum Score (0-100) from freshness and stage movement."""
    score = 0.0
    reasons = []
    now = datetime.now(timezone.utc)

    # Last engagement freshness
    last_eng_str = _get_text(props, FIELD_LAST_ENGAGEMENT_DATE)
    if last_eng_str:
        try:
            last_eng = datetime.fromisoformat(last_eng_str.replace("Z", "+00:00"))
            days_ago = (now - last_eng).days
            if days_ago <= 3:
                score += MOMENTUM_ACTIVITY_3D
                reasons.append(f"Active {days_ago}d ago")
            elif days_ago <= 7:
                score += MOMENTUM_ACTIVITY_7D
            elif days_ago <= 14:
                score += MOMENTUM_ACTIVITY_14D
        except (ValueError, TypeError):
            pass

    # Multiple contacts engaged
    engaged = _get_number(props, FIELD_ENGAGED_CONTACTS)
    if engaged >= 2:
        score += MOMENTUM_MULTI_ENGAGED
        reasons.append(f"{int(engaged)} contacts engaged")

    return min(score, 100), reasons


def select_best_contact(contacts: list) -> Optional[dict]:
    """Select the best contact at a company using cascade logic."""
    # Filter to Action Ready contacts first, fall back to all
    eligible = [c for c in contacts
                if _get_bool(c["properties"], FIELD_ACTION_READY)
                and _get_text(c["properties"], FIELD_OUTREACH_STATUS) not in OUTREACH_BLOCKED
                and not _get_bool(c["properties"], FIELD_DO_NOT_CALL)]

    if not eligible:
        eligible = [c for c in contacts
                    if _get_text(c["properties"], FIELD_OUTREACH_STATUS) not in OUTREACH_BLOCKED
                    and not _get_bool(c["properties"], FIELD_DO_NOT_CALL)]

    if not eligible:
        eligible = contacts  # Last resort: any contact

    if not eligible:
        return None

    # Sort by: Lead Score DESC, Seniority DESC, has phone
    def sort_key(c):
        props = c["properties"]
        score = _get_number(props, FIELD_LEAD_SCORE)
        seniority = _get_text(props, FIELD_SENIORITY)
        sen_rank = SENIORITY_RANK.get(seniority, 30)
        has_phone = 1 if (_get_text(props, FIELD_WORK_PHONE) or _get_text(props, FIELD_MOBILE_PHONE)) else 0
        return (score, sen_rank, has_phone)

    eligible.sort(key=sort_key, reverse=True)
    return eligible[0]


def determine_next_action(tier: str, ai_action_type: str, engagement_score: float) -> str:
    """Determine the Next Action based on tier + AI action type."""
    if tier == PRIORITY_P1:
        if ai_action_type == "Email":
            return ACTION_EMAIL
        return ACTION_CALL  # Default P1 = Call
    if tier == PRIORITY_P2:
        if ai_action_type == "Call":
            return ACTION_CALL
        if ai_action_type == "Sequence":
            return ACTION_SEQUENCE
        return ACTION_EMAIL  # Default P2 = Email
    return ACTION_WAIT  # P3


def determine_sla(tier: str, action: str) -> str:
    """Determine SLA based on tier."""
    if tier == PRIORITY_P1:
        return SLA_24H
    if tier == PRIORITY_P2:
        return SLA_48H
    return SLA_NONE


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN SCORING FUNCTION
# ═══════════════════════════════════════════════════════════════════════════════

def score_company(company: dict, contacts: list) -> Optional[dict]:
    """Score a single company. Returns dict of fields to write, or None if skipped."""
    props = company["properties"]
    company_id = company["id"]
    company_name = _get_text(props, "Name") or _get_text(props, "Company Name") or company_id[:8]

    # Skip terminal stages
    stage = _get_text(props, FIELD_COMPANY_STAGE)
    if stage in STAGE_TERMINAL:
        return None

    if not contacts:
        return None

    # ── Component 1: Best Contact Score (BCS) ──
    bcs = max((_get_number(c["properties"], FIELD_LEAD_SCORE) for c in contacts), default=0)
    bcs_populated = bcs > 0

    # ── Component 2: Engagement Index (ENG) ──
    eng, eng_reasons = compute_engagement_index(contacts)
    eng_populated = eng > 0

    # ── Component 3: Firmographic Fit (FIT) ──
    fit, fit_reasons = compute_firmographic_fit(props)
    fit_populated = (_get_text(props, FIELD_INDUSTRY) != "" or _get_number(props, FIELD_EMPLOYEES) > 0)

    # ── Component 4: AI Signal Strength (AIS) ──
    ais, risk_flag, ai_reasons = compute_ai_signal(props)
    ais_populated = ais > 0

    # ── Component 5: Momentum (MOM) ──
    mom, mom_reasons = compute_momentum(props, contacts)
    mom_populated = mom > 0

    # ── Weight redistribution for empty components ──
    components = {
        "bcs": (bcs, CPS_WEIGHT_BEST_CONTACT, bcs_populated),
        "eng": (eng, CPS_WEIGHT_ENGAGEMENT, eng_populated),
        "fit": (fit, CPS_WEIGHT_FIRMOGRAPHIC, fit_populated),
        "ais": (ais, CPS_WEIGHT_AI_SIGNAL, ais_populated),
        "mom": (mom, CPS_WEIGHT_MOMENTUM, mom_populated),
    }

    populated_count = sum(1 for _, _, p in components.values() if p)

    # Min 2 components required
    if populated_count < CPS_MIN_COMPONENTS:
        return {
            "company_id": company_id,
            "company_name": company_name,
            "score": 0, "tier": PRIORITY_P3,
            "best_contact_name": _get_text(contacts[0]["properties"], FIELD_FULL_NAME) if contacts else "Unknown",
            "best_contact_id": contacts[0]["id"] if contacts else "",
            "next_action": ACTION_WAIT,
            "reason": "Insufficient data for prioritization",
            "owner": _get_text(props, FIELD_PRIMARY_COMPANY_OWNER),
            "sla": SLA_NONE,
            "risk_flag": False,
            "bcs": 0, "eng": 0, "fit": 0, "ais": 0, "mom": 0,
        }

    # Redistribute weights from empty components to populated ones
    total_populated_weight = sum(w for _, w, p in components.values() if p)
    if total_populated_weight == 0:
        total_populated_weight = 1  # Safety

    cps = 0.0
    for name, (value, weight, populated) in components.items():
        if populated:
            adjusted_weight = weight / total_populated_weight
            cps += value * adjusted_weight

    # ── Sparse-data cap (v8.0) ──────────────────────────────────────
    # When fewer than 3 components are populated, cap CPS to prevent
    # single-component weight redistribution from inflating scores.
    # E.g., Firmographic Fit alone (industry=100, size=100) would
    # redistribute to CPS=100 → P1, which is too aggressive for a
    # company with zero engagement or contact signals.
    #
    # With 1 component: max CPS = 65 (can reach P2 but not P1)
    # With 2 components: max CPS = 80 (can reach P1 with strong signals)
    SPARSE_DATA_CAPS = {1: 65.0, 2: 80.0}
    sparse_cap = SPARSE_DATA_CAPS.get(populated_count)
    if sparse_cap is not None and cps > sparse_cap:
        cps = sparse_cap
    # ────────────────────────────────────────────────────────────────

    # ── Apply guards ──
    cps = min(cps, 100)

    # AI Disqualified cap
    if risk_flag and cps > CPS_AI_DISQUALIFIED_CAP:
        cps = CPS_AI_DISQUALIFIED_CAP

    cps = round(cps, 1)

    # ── Determine tier ──
    if cps >= CPS_TIER_P1:
        tier = PRIORITY_P1
    elif cps >= CPS_TIER_P2:
        tier = PRIORITY_P2
    else:
        tier = PRIORITY_P3

    # ── Best Contact ──
    best = select_best_contact(contacts)
    best_name = _get_text(best["properties"], FIELD_FULL_NAME) if best else "Unknown"
    best_id = best["id"] if best else ""
    best_score = _get_number(best["properties"], FIELD_LEAD_SCORE) if best else 0

    # ── Next Action + SLA ──
    ai_action = _get_text(props, FIELD_AI_ACTION_TYPE)
    action = determine_next_action(tier, ai_action, eng)
    sla = determine_sla(tier, action)

    # ── Priority Reason (top 3) ──
    all_reasons = eng_reasons + fit_reasons + ai_reasons + mom_reasons
    if best and best_score >= 80:
        seniority = _get_text(best["properties"], FIELD_SENIORITY)
        all_reasons.insert(0, f"Strong contact: {best_name} ({seniority}, score {int(best_score)})")
    reason_text = " | ".join(all_reasons[:3]) if all_reasons else "Firmographic fit only"

    # ── Owner ──
    owner = _get_text(props, FIELD_PRIMARY_COMPANY_OWNER)

    return {
        "company_id": company_id,
        "company_name": company_name,
        "score": cps,
        "tier": tier,
        "best_contact_name": best_name,
        "best_contact_id": best_id,
        "next_action": action,
        "reason": reason_text,
        "owner": owner,
        "sla": sla,
        "risk_flag": risk_flag,
        "bcs": round(bcs, 1),
        "eng": round(eng, 1),
        "fit": round(fit, 1),
        "ais": round(ais, 1),
        "mom": round(mom, 1),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# NOTION WRITE
# ═══════════════════════════════════════════════════════════════════════════════

def build_update_payload(result: dict) -> dict:
    """Build Notion update payload from scoring result."""
    props = {}

    # Number field
    props[FIELD_COMPANY_PRIORITY_SCORE] = {"number": result.get("score", 0)}

    # Select fields
    tier = result.get("tier", PRIORITY_P3)
    next_action = result.get("next_action", ACTION_WAIT)
    sla = result.get("sla", SLA_NONE)

    props[FIELD_PRIORITY_TIER] = {"select": {"name": tier}}
    props[FIELD_NEXT_ACTION] = {"select": {"name": next_action}}
    props[FIELD_ACTION_SLA] = {"select": {"name": sla}}

    owner = result.get("owner", "")
    if owner and owner in TEAM_MEMBERS:
        props[FIELD_ACTION_OWNER] = {"select": {"name": owner}}

    # Rich text fields
    best_name = result.get("best_contact_name", "Unknown")
    best_id = result.get("best_contact_id", "")
    best_text = f"{best_name} ({best_id[:8]})" if best_id else best_name
    props[FIELD_BEST_CONTACT] = {
        "rich_text": [{"text": {"content": best_text[:2000]}}]
    }
    reason = result.get("reason", "")
    props[FIELD_PRIORITY_REASON] = {
        "rich_text": [{"text": {"content": reason[:2000]}}]
    }

    # AI Risk Flag as rich_text (Notion field type is rich_text)
    risk_text = "Yes — AI Disqualified" if result.get("risk_flag", False) else ""
    if risk_text:
        props[FIELD_AI_RISK_FLAG] = {
            "rich_text": [{"text": {"content": risk_text}}]
        }
    else:
        props[FIELD_AI_RISK_FLAG] = {"rich_text": []}

    return props


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def run(execute: bool = False, force: bool = False, limit: int = None):
    """Main execution."""
    logger.info(f"=== Company Priority Scorer v7.0 — {'EXECUTE' if execute else 'DRY-RUN'} ===")

    if not NOTION_API_KEY or not COMPANIES_DB_ID or not CONTACTS_DB_ID:
        raise EnvironmentError(
            "Missing required env vars: NOTION_API_KEY, "
            "NOTION_DATABASE_ID_COMPANIES, NOTION_DATABASE_ID_CONTACTS"
        )

    # ── Step 1: Preload all data ──
    logger.info("Step 1: Preloading companies...")
    companies = preload_all(COMPANIES_DB_ID, "companies")

    logger.info("Step 2: Preloading contacts...")
    contacts = preload_all(CONTACTS_DB_ID, "contacts")

    # ── Step 2: Build company → contacts map ──
    logger.info("Step 3: Building company-contacts map...")
    company_contacts: Dict[str, list] = {}
    orphan_count = 0
    for contact in contacts:
        company_ids = _get_relation_ids(contact["properties"], FIELD_COMPANY_RELATION)
        if company_ids:
            for cid in company_ids:
                company_contacts.setdefault(cid, []).append(contact)
        else:
            orphan_count += 1

    logger.info(f"  Mapped contacts to {len(company_contacts)} companies, {orphan_count} orphans")

    # ── Step 3: Score each company ──
    logger.info("Step 4: Scoring companies...")
    results = []
    skipped = 0
    scored = 0
    p1_count = 0
    p2_count = 0
    p3_count = 0

    companies_to_process = companies[:limit] if limit else companies

    for i, company in enumerate(companies_to_process):
        if i > 0 and i % 500 == 0:
            logger.info(f"  Progress: {i}/{len(companies_to_process)} companies scored")

        company_id = company["id"]
        company_contacts_list = company_contacts.get(company_id, [])

        # Skip if already scored and not forcing
        if not force:
            existing_score = _get_number(company["properties"], FIELD_COMPANY_PRIORITY_SCORE)
            if existing_score > 0:
                skipped += 1
                continue

        result = score_company(company, company_contacts_list)
        if result is None:
            skipped += 1
            continue

        result["company_id"] = company_id
        results.append(result)
        scored += 1

        if result["tier"] == PRIORITY_P1:
            p1_count += 1
        elif result["tier"] == PRIORITY_P2:
            p2_count += 1
        else:
            p3_count += 1

    logger.info(f"  Scored: {scored} | Skipped: {skipped}")
    logger.info(f"  Distribution: P1={p1_count}, P2={p2_count}, P3={p3_count}")

    # Log top 10 P1/P2
    top = sorted(results, key=lambda r: r["score"], reverse=True)[:15]
    if top:
        logger.info("  Top companies:")
        for r in top:
            logger.info(f"    {r['tier']} {r['score']:.1f} — {r['company_name']} — {r['reason'][:60]}")

    # ── Step 4: Write to Notion ──
    if execute and results:
        logger.info(f"Step 5: Writing {len(results)} updates to Notion...")
        written = 0
        errors = 0
        for i, result in enumerate(results):
            try:
                payload = build_update_payload(result)
                update_page(result["company_id"], payload)
                written += 1
                if (i + 1) % 50 == 0:
                    logger.info(f"  Written {i + 1}/{len(results)}")
            except Exception as e:
                errors += 1
                logger.error(f"  Failed to update {result['company_name']}: {e}")

        logger.info(f"  Written: {written} | Errors: {errors}")
    elif not execute:
        logger.info("Step 5: DRY-RUN — no writes performed")

    # ── Step 5: Save stats ──
    stats = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "mode": "execute" if execute else "dry-run",
        "total_companies": len(companies),
        "total_contacts": len(contacts),
        "scored": scored,
        "skipped": skipped,
        "p1": p1_count,
        "p2": p2_count,
        "p3": p3_count,
    }
    with open(STATS_FILE, "w") as f:
        json.dump(stats, f, indent=2)
    logger.info(f"Stats saved to {STATS_FILE}")

    return stats


def main():
    parser = argparse.ArgumentParser(description="Company Priority Scorer — Decision Layer v7.0")
    parser.add_argument("--execute", action="store_true", help="Apply writes to Notion (default: dry-run)")
    parser.add_argument("--force", action="store_true", help="Recompute all companies (even already scored)")
    parser.add_argument("--limit", type=int, help="Limit to first N companies (testing)")
    args = parser.parse_args()

    run(execute=args.execute, force=args.force, limit=args.limit)


if __name__ == "__main__":
    main()
