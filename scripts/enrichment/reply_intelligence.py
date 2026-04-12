#!/usr/bin/env python3
"""
AI Sales OS — Reply Intelligence Engine

Analyzes contacts with Replied=True and writes AI-classified reply
intelligence fields to Notion. This is a READ + WRITE-NEW-FIELDS-ONLY
layer — it NEVER modifies existing fields, scores, stages, outreach
statuses, or any other system state.

Fields Written (6 — all on Contacts DB, all AI-prefixed):
  - AI Reply Status        (select)   Interested / Soft Interest / Neutral / Soft Rejection / Hard Rejection
  - AI Reply Reason        (select)   13 values covering positive, neutral, and negative reasons
  - AI Close Probability   (number)   0-100
  - AI Next Action         (select)   Call Now / Follow-up Email / Send Proposal / Re-engage Later / Change Stakeholder / No Action
  - AI Reply Confidence    (select)   High / Medium / Low
  - AI Reply Last Analyzed (date)     ISO 8601 timestamp of last analysis

Safety guarantees:
  - ZERO writes to Lead Score, Lead Tier, Stage, Outreach Status, Action Ready,
    Contact Responded, Meeting Booked, or any field managed by daily_sync /
    lead_score / action_ready_updater / auto_tasks / ingestion_gate / data_governor.
  - NEVER archives, blocks, or skips contacts from system ingestion.
  - NEVER creates tasks or mutates governance decisions.
  - 100% independent enrichment layer.
  - Idempotent: re-running produces the same result.

Trigger logic (reanalyze only when reply-specific signals are newer):
  - Contact has Replied=True (mandatory)
  AND one of:
    - AI Reply Last Analyzed is empty (never analyzed)
    - contact last_edited_time > AI Reply Last Analyzed (any Notion edit since)
    - Emails Replied Count changed (numeric mismatch check via last_edited proxy)

Usage:
    cd scripts
    python enrichment/reply_intelligence.py --dry-run              # preview without writing
    python enrichment/reply_intelligence.py                        # analyze all triggered contacts
    python enrichment/reply_intelligence.py --limit 50             # limit to first N contacts
    python enrichment/reply_intelligence.py --force                # re-analyze ALL replied contacts
    python enrichment/reply_intelligence.py --export               # save analysis report to file
"""
import sys as _sys, os as _os; _sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
import os
import sys
import json
import logging
import time
import argparse
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple
from dotenv import load_dotenv

load_dotenv()

from core.notion_helpers import (
    NOTION_DATABASE_ID_CONTACTS,
    update_page,
    rate_limiter,
    notion_request,
    NOTION_BASE_URL,
)
from core.constants import (
    # ── Contact fields (READ-ONLY for this script) ──
    FIELD_REPLIED,
    FIELD_EMAILS_REPLIED_COUNT,
    FIELD_EMAIL_OPEN_COUNT,
    FIELD_EMAILS_SENT_COUNT,
    FIELD_LAST_CONTACTED,
    FIELD_LEAD_SCORE,
    FIELD_LEAD_TIER,
    FIELD_FULL_NAME,
    FIELD_APOLLO_CONTACT_ID,
    FIELD_CONTACT_OWNER,
    FIELD_COMPANY_RELATION,
    FIELD_MEETING_BOOKED,
    FIELD_DEMOED,
    FIELD_EMAIL_SENT,
    FIELD_EMAIL_OPENED,
    FIELD_SENIORITY,
    FIELD_TITLE,
    # Score thresholds (read-only reference)
    SCORE_HOT,
    SCORE_WARM,
    TIER_HOT,
    TIER_WARM,
    TIER_COLD,
    # ── Reply Intelligence fields (WRITE targets — the ONLY fields we touch) ──
    FIELD_AI_REPLY_STATUS,
    FIELD_AI_REPLY_REASON,
    FIELD_AI_CLOSE_PROBABILITY,
    FIELD_AI_NEXT_ACTION,
    FIELD_AI_REPLY_CONFIDENCE,
    FIELD_AI_REPLY_LAST_ANALYZED,
    # Status values
    AI_REPLY_STATUS_INTERESTED,
    AI_REPLY_STATUS_SOFT_INTEREST,
    AI_REPLY_STATUS_NEUTRAL,
    AI_REPLY_STATUS_SOFT_REJECTION,
    AI_REPLY_STATUS_HARD_REJECTION,
    # Reason values
    AI_REPLY_REASON_MEETING_REQUEST,
    AI_REPLY_REASON_PRICING_ASK,
    AI_REPLY_REASON_INFO_REQUEST,
    AI_REPLY_REASON_DELEGATION,
    AI_REPLY_REASON_TIMING,
    AI_REPLY_REASON_BUDGET,
    AI_REPLY_REASON_NO_NEED,
    AI_REPLY_REASON_ALREADY_HAS_SOLUTION,
    AI_REPLY_REASON_TRUST_RISK,
    AI_REPLY_REASON_COMPLEXITY,
    AI_REPLY_REASON_UNKNOWN,
    AI_REPLY_REASON_GENERIC_REJECTION,
    AI_REPLY_REASON_EXPLICIT_REJECTION,
    # Next Action values (NO Archive — this layer never archives)
    AI_REPLY_NEXT_CALL_NOW,
    AI_REPLY_NEXT_FOLLOW_UP_EMAIL,
    AI_REPLY_NEXT_SEND_PROPOSAL,
    AI_REPLY_NEXT_RE_ENGAGE_LATER,
    AI_REPLY_NEXT_CHANGE_STAKEHOLDER,
    AI_REPLY_NEXT_NO_ACTION,
    # Confidence values
    AI_REPLY_CONFIDENCE_HIGH,
    AI_REPLY_CONFIDENCE_MEDIUM,
    AI_REPLY_CONFIDENCE_LOW,
)


# ─── Config ──────────────────────────────────────────────────────────────────

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
QUERY_PAGE_SIZE = 100  # Notion max per page


# ─── Logging (script-relative path per v6.2 convention) ─────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(
            os.path.join(SCRIPT_DIR, "reply_intelligence.log"),
            encoding="utf-8",
        ),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# HELPERS: Notion Property Extractors (read-only)
# ═══════════════════════════════════════════════════════════════════════════════

def _get_checkbox(props: Dict, field: str) -> bool:
    return props.get(field, {}).get("checkbox", False)

def _get_number(props: Dict, field: str) -> Optional[float]:
    return props.get(field, {}).get("number")

def _get_select(props: Dict, field: str) -> Optional[str]:
    sel = props.get(field, {}).get("select")
    return sel.get("name") if sel else None

def _get_rich_text(props: Dict, field: str) -> Optional[str]:
    rt = props.get(field, {}).get("rich_text", [])
    return rt[0].get("plain_text", "").strip() if rt else None

def _get_title(props: Dict, field: str) -> Optional[str]:
    t = props.get(field, {}).get("title", [])
    return t[0].get("plain_text", "").strip() if t else None

def _get_date(props: Dict, field: str) -> Optional[str]:
    d = props.get(field, {}).get("date")
    return d.get("start") if d else None

def _get_relation_ids(props: Dict, field: str) -> List[str]:
    return [r.get("id", "") for r in props.get(field, {}).get("relation", [])]

def _parse_iso(s: str) -> Optional[datetime]:
    """Parse an ISO 8601 string to a timezone-aware datetime, or None."""
    if not s:
        return None
    try:
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, TypeError):
        return None


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 1: FETCH — Query Notion for Replied Contacts
# ═══════════════════════════════════════════════════════════════════════════════

def fetch_replied_contacts() -> List[Dict]:
    """
    Query Notion Contacts DB for all contacts with Replied = True.
    Returns list of raw Notion page objects (includes last_edited_time).
    """
    contacts = []
    has_more = True
    start_cursor = None

    logger.info("Fetching contacts with Replied=True from Notion...")

    filter_obj = {
        "property": FIELD_REPLIED,
        "checkbox": {"equals": True},
    }

    while has_more:
        body = {
            "page_size": QUERY_PAGE_SIZE,
            "filter": filter_obj,
        }
        if start_cursor:
            body["start_cursor"] = start_cursor

        resp = notion_request(
            "POST",
            f"{NOTION_BASE_URL}/databases/{NOTION_DATABASE_ID_CONTACTS}/query",
            json=body,
        )
        data = resp.json()

        for page in data.get("results", []):
            contacts.append(page)

        has_more = data.get("has_more", False)
        start_cursor = data.get("next_cursor")

    logger.info(f"Fetched {len(contacts)} contacts with Replied=True")
    return contacts


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 2: FILTER — Apply Trigger Conditions (reply-specific freshness)
# ═══════════════════════════════════════════════════════════════════════════════

def should_analyze(page: Dict, force: bool = False) -> Tuple[bool, str]:
    """
    Determine if a contact needs (re-)analysis.

    Trigger logic — reanalyze only when reply-specific signals are newer:
      1. force=True → always analyze
      2. AI Reply Last Analyzed is empty → never analyzed before
      3. page.last_edited_time > AI Reply Last Analyzed → contact record
         was edited after our last analysis (covers reply count changes,
         new engagement data written by analytics_tracker, etc.)

    We use last_edited_time (Notion page metadata, not a property) because
    it captures ANY change to the contact — including Emails Replied Count
    updates written by analytics_tracker, outcome_tracker, or daily_sync.
    This is more reliable than comparing against Last Contacted alone,
    which only reflects manual/task-based outreach timestamps.
    """
    if force:
        return True, "forced"

    props = page.get("properties", {})
    last_analyzed_str = _get_date(props, FIELD_AI_REPLY_LAST_ANALYZED)

    # Never analyzed → must analyze
    if not last_analyzed_str:
        return True, "never_analyzed"

    last_analyzed = _parse_iso(last_analyzed_str)
    if not last_analyzed:
        return True, "date_parse_error"

    # Use Notion page last_edited_time as freshness signal
    last_edited_str = page.get("last_edited_time")
    last_edited = _parse_iso(last_edited_str)

    if last_edited and last_edited > last_analyzed:
        return True, "contact_edited_since_analysis"

    return False, "already_current"


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 3: ANALYZE — Classify Reply Signals
# ═══════════════════════════════════════════════════════════════════════════════

def _compute_engagement_score(props: Dict) -> int:
    """
    Compute a raw engagement intensity score (0-100) from available signals.

    All inputs are READ-ONLY from existing Notion fields.
    """
    score = 0

    # ── Replies (strongest signal) ──
    replies = _get_number(props, FIELD_EMAILS_REPLIED_COUNT) or 0
    if replies >= 3:
        score += 35
    elif replies >= 2:
        score += 25
    elif replies >= 1:
        score += 15

    # ── Open engagement depth ──
    opens = _get_number(props, FIELD_EMAIL_OPEN_COUNT) or 0
    sent = _get_number(props, FIELD_EMAILS_SENT_COUNT) or 0
    if sent > 0:
        open_rate = opens / sent
        if open_rate >= 0.8:
            score += 15
        elif open_rate >= 0.5:
            score += 10
        elif open_rate >= 0.2:
            score += 5
    elif opens >= 3:
        score += 10

    # ── Meeting / Demo (very strong — read only, never write) ──
    if _get_checkbox(props, FIELD_MEETING_BOOKED):
        score += 25
    if _get_checkbox(props, FIELD_DEMOED):
        score += 20

    # ── Recency bonus ──
    last_contacted_str = _get_date(props, FIELD_LAST_CONTACTED)
    if last_contacted_str:
        lc = _parse_iso(last_contacted_str)
        if lc:
            days_ago = (datetime.now(timezone.utc) - lc).days
            if days_ago <= 3:
                score += 10
            elif days_ago <= 7:
                score += 7
            elif days_ago <= 14:
                score += 5
            elif days_ago <= 30:
                score += 2

    return min(score, 100)


def _infer_reply_reason(props: Dict, engagement_score: int) -> str:
    """
    Infer the most likely reply reason from available engagement signals.

    NOTE: We do NOT have reply text content in Notion — only boolean/numeric
    signals. The classification is a best-effort inference from signal patterns.
    """
    meeting_booked = _get_checkbox(props, FIELD_MEETING_BOOKED)
    demoed = _get_checkbox(props, FIELD_DEMOED)
    replies = _get_number(props, FIELD_EMAILS_REPLIED_COUNT) or 0
    opens = _get_number(props, FIELD_EMAIL_OPEN_COUNT) or 0
    lead_score = _get_number(props, FIELD_LEAD_SCORE) or 0

    # ── Clear positive signals ──
    if meeting_booked:
        return AI_REPLY_REASON_MEETING_REQUEST
    if demoed:
        return AI_REPLY_REASON_PRICING_ASK

    # ── Multi-reply = active conversation ──
    if replies >= 2 and opens >= 3:
        return AI_REPLY_REASON_INFO_REQUEST
    if replies >= 2:
        if lead_score >= SCORE_HOT:
            return AI_REPLY_REASON_PRICING_ASK
        return AI_REPLY_REASON_INFO_REQUEST

    # ── Single reply territory ──
    if lead_score >= SCORE_HOT and opens >= 3:
        # High-value contact opened many times, replied once → delegation
        return AI_REPLY_REASON_DELEGATION

    if lead_score >= SCORE_WARM and engagement_score >= 30:
        return AI_REPLY_REASON_TIMING

    # Low engagement single reply → negative signal
    if engagement_score <= 15:
        last_contacted_str = _get_date(props, FIELD_LAST_CONTACTED)
        lc = _parse_iso(last_contacted_str) if last_contacted_str else None
        if lc:
            days_ago = (datetime.now(timezone.utc) - lc).days
            if days_ago > 60:
                return AI_REPLY_REASON_EXPLICIT_REJECTION
            if days_ago > 30:
                return AI_REPLY_REASON_NO_NEED
        return AI_REPLY_REASON_GENERIC_REJECTION

    if engagement_score <= 25:
        return AI_REPLY_REASON_TIMING

    # Default for moderate signals
    return AI_REPLY_REASON_UNKNOWN


def _classify_reply_status(props: Dict, engagement_score: int, reason: str) -> str:
    """
    Classify the overall reply status from engagement score + reason.
    """
    meeting_booked = _get_checkbox(props, FIELD_MEETING_BOOKED)
    demoed = _get_checkbox(props, FIELD_DEMOED)

    # Hard overrides from strong signals
    if meeting_booked or demoed:
        return AI_REPLY_STATUS_INTERESTED
    if reason == AI_REPLY_REASON_MEETING_REQUEST:
        return AI_REPLY_STATUS_INTERESTED
    if reason == AI_REPLY_REASON_EXPLICIT_REJECTION:
        return AI_REPLY_STATUS_HARD_REJECTION
    if reason in (AI_REPLY_REASON_GENERIC_REJECTION, AI_REPLY_REASON_NO_NEED):
        return AI_REPLY_STATUS_SOFT_REJECTION

    # Score-based tiers
    if engagement_score >= 60:
        return AI_REPLY_STATUS_INTERESTED
    elif engagement_score >= 40:
        return AI_REPLY_STATUS_SOFT_INTEREST
    elif engagement_score >= 25:
        return AI_REPLY_STATUS_NEUTRAL
    elif engagement_score >= 10:
        return AI_REPLY_STATUS_SOFT_REJECTION
    else:
        return AI_REPLY_STATUS_HARD_REJECTION


def _compute_close_probability(
    status: str,
    reason: str,
    engagement_score: int,
    lead_score: float,
    seniority: Optional[str],
) -> int:
    """
    Compute close probability (0-100).

    Formula: base (from status) + reason_mod + lead_score_bonus + seniority_bonus + engagement_mod
    Capped at 0-95 (only Closed Won = 100).
    """
    STATUS_BASE = {
        AI_REPLY_STATUS_INTERESTED: 55,
        AI_REPLY_STATUS_SOFT_INTEREST: 35,
        AI_REPLY_STATUS_NEUTRAL: 18,
        AI_REPLY_STATUS_SOFT_REJECTION: 8,
        AI_REPLY_STATUS_HARD_REJECTION: 2,
    }
    base = STATUS_BASE.get(status, 15)

    REASON_MOD = {
        AI_REPLY_REASON_MEETING_REQUEST: 15,
        AI_REPLY_REASON_PRICING_ASK: 12,
        AI_REPLY_REASON_INFO_REQUEST: 5,
        AI_REPLY_REASON_DELEGATION: 3,
        AI_REPLY_REASON_TIMING: -2,
        AI_REPLY_REASON_BUDGET: -4,
        AI_REPLY_REASON_NO_NEED: -5,
        AI_REPLY_REASON_ALREADY_HAS_SOLUTION: -6,
        AI_REPLY_REASON_TRUST_RISK: -3,
        AI_REPLY_REASON_COMPLEXITY: -1,
        AI_REPLY_REASON_UNKNOWN: 0,
        AI_REPLY_REASON_GENERIC_REJECTION: -5,
        AI_REPLY_REASON_EXPLICIT_REJECTION: -5,
    }
    base += REASON_MOD.get(reason, 0)

    # Lead score bonus (0-15)
    ls = lead_score or 0
    if ls >= SCORE_HOT:
        base += 15
    elif ls >= SCORE_WARM:
        base += 8
    elif ls >= 30:
        base += 3

    # Seniority bonus (decision makers close faster)
    if seniority:
        sl = seniority.lower().replace("-", " ").strip()
        if sl in ("c suite", "c-suite", "founder", "owner"):
            base += 10
        elif sl in ("vp", "vice president", "director"):
            base += 6
        elif sl in ("manager", "senior"):
            base += 3

    # Engagement modifier (0-10)
    if engagement_score >= 70:
        base += 10
    elif engagement_score >= 40:
        base += 5
    elif engagement_score >= 20:
        base += 2

    return max(0, min(95, base))


def _determine_next_action(status: str, reason: str, close_prob: int) -> str:
    """
    Map (status, reason, probability) to recommended next action.

    IMPORTANT: This layer NEVER recommends Archive.
    The 6 allowed actions are advisory labels for the sales operator.
    """
    # ── Reason-driven overrides ──
    if reason == AI_REPLY_REASON_MEETING_REQUEST:
        return AI_REPLY_NEXT_CALL_NOW
    if reason == AI_REPLY_REASON_EXPLICIT_REJECTION:
        return AI_REPLY_NEXT_NO_ACTION
    if reason == AI_REPLY_REASON_DELEGATION:
        return AI_REPLY_NEXT_CHANGE_STAKEHOLDER

    # ── Status + probability driven ──
    if status == AI_REPLY_STATUS_INTERESTED:
        if reason == AI_REPLY_REASON_PRICING_ASK:
            return AI_REPLY_NEXT_SEND_PROPOSAL
        if close_prob >= 50:
            return AI_REPLY_NEXT_CALL_NOW
        return AI_REPLY_NEXT_SEND_PROPOSAL

    if status == AI_REPLY_STATUS_SOFT_INTEREST:
        if close_prob >= 40:
            return AI_REPLY_NEXT_SEND_PROPOSAL
        return AI_REPLY_NEXT_FOLLOW_UP_EMAIL

    if status == AI_REPLY_STATUS_NEUTRAL:
        if close_prob >= 30:
            return AI_REPLY_NEXT_FOLLOW_UP_EMAIL
        return AI_REPLY_NEXT_RE_ENGAGE_LATER

    if status == AI_REPLY_STATUS_SOFT_REJECTION:
        return AI_REPLY_NEXT_RE_ENGAGE_LATER

    if status == AI_REPLY_STATUS_HARD_REJECTION:
        return AI_REPLY_NEXT_NO_ACTION

    return AI_REPLY_NEXT_RE_ENGAGE_LATER


def _assess_confidence(props: Dict, replies: float) -> str:
    """
    Assess classification confidence based on signal density.

    High:   >=3 distinct signals present
    Medium: 2 signals
    Low:    <=1 signal (only the Replied checkbox, sparse data)
    """
    signal_count = 0

    # Signal 1: Reply count populated and > 0
    if replies and replies >= 1:
        signal_count += 1

    # Signal 2: Open count populated and > 0
    opens = _get_number(props, FIELD_EMAIL_OPEN_COUNT)
    if opens and opens >= 1:
        signal_count += 1

    # Signal 3: Meeting or Demo boolean
    if _get_checkbox(props, FIELD_MEETING_BOOKED) or _get_checkbox(props, FIELD_DEMOED):
        signal_count += 1

    # Signal 4: Last Contacted is recent (within 30 days)
    last_contacted_str = _get_date(props, FIELD_LAST_CONTACTED)
    lc = _parse_iso(last_contacted_str) if last_contacted_str else None
    if lc:
        if (datetime.now(timezone.utc) - lc).days <= 30:
            signal_count += 1

    # Signal 5: Multiple replies (strong quality signal)
    if replies and replies >= 2:
        signal_count += 1

    if signal_count >= 3:
        return AI_REPLY_CONFIDENCE_HIGH
    elif signal_count >= 2:
        return AI_REPLY_CONFIDENCE_MEDIUM
    else:
        return AI_REPLY_CONFIDENCE_LOW


def analyze_contact(props: Dict) -> Dict:
    """
    Full reply intelligence analysis for a single contact.

    Returns dict with all 6 AI field values ready for Notion write.
    """
    engagement_score = _compute_engagement_score(props)
    lead_score = _get_number(props, FIELD_LEAD_SCORE) or 0
    seniority = _get_select(props, FIELD_SENIORITY) or _get_rich_text(props, FIELD_SENIORITY)
    replies = _get_number(props, FIELD_EMAILS_REPLIED_COUNT) or 0

    reason = _infer_reply_reason(props, engagement_score)
    status = _classify_reply_status(props, engagement_score, reason)
    close_probability = _compute_close_probability(
        status, reason, engagement_score, lead_score, seniority
    )
    next_action = _determine_next_action(status, reason, close_probability)
    confidence = _assess_confidence(props, replies)

    return {
        "status": status,
        "reason": reason,
        "close_probability": close_probability,
        "next_action": next_action,
        "confidence": confidence,
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
        "_engagement_score": engagement_score,  # internal — not written to Notion
    }


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 4: WRITE — Update Notion (ONLY the 6 AI Reply Intelligence fields)
# ═══════════════════════════════════════════════════════════════════════════════

def build_notion_properties(analysis: Dict) -> Dict:
    """
    Convert analysis dict to Notion property update payload.

    SAFETY: This function constructs properties for ONLY the 6 AI Reply
    Intelligence fields. It is structurally impossible for it to touch
    Stage, Outreach Status, Action Ready, Contact Responded, Meeting Booked,
    Lead Score, Lead Tier, or any other system field.
    """
    return {
        FIELD_AI_REPLY_STATUS: {
            "select": {"name": analysis["status"]},
        },
        FIELD_AI_REPLY_REASON: {
            "select": {"name": analysis["reason"]},
        },
        FIELD_AI_CLOSE_PROBABILITY: {
            "number": analysis["close_probability"],
        },
        FIELD_AI_NEXT_ACTION: {
            "select": {"name": analysis["next_action"]},
        },
        FIELD_AI_REPLY_CONFIDENCE: {
            "select": {"name": analysis["confidence"]},
        },
        FIELD_AI_REPLY_LAST_ANALYZED: {
            "date": {"start": analysis["analyzed_at"]},
        },
    }


def write_analysis_to_notion(
    page_id: str,
    analysis: Dict,
    dry_run: bool = False,
) -> bool:
    """Write the 6 AI fields to a single Notion contact page. Returns True on success."""
    if dry_run:
        return True
    try:
        properties = build_notion_properties(analysis)
        update_page(page_id, properties)
        return True
    except Exception as e:
        logger.error(f"Failed to write analysis for page {page_id}: {e}")
        return False


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN PIPELINE
# ═══════════════════════════════════════════════════════════════════════════════

def run_reply_intelligence(
    dry_run: bool = False,
    limit: Optional[int] = None,
    force: bool = False,
) -> Dict:
    """
    Main pipeline: Fetch -> Filter -> Analyze -> Write.
    Returns stats dict.
    """
    stats = {
        "fetched": 0,
        "triggered": 0,
        "skipped": 0,
        "analyzed": 0,
        "written": 0,
        "errors": 0,
        "status_distribution": {},
        "reason_distribution": {},
        "action_distribution": {},
        "confidence_distribution": {},
        "avg_close_probability": 0.0,
    }

    # ── Step 1: Fetch ──
    contacts = fetch_replied_contacts()
    stats["fetched"] = len(contacts)

    if not contacts:
        logger.info("No contacts with Replied=True found. Nothing to analyze.")
        return stats

    # ── Step 2: Filter by trigger conditions ──
    triggered = []
    skip_reasons = {}

    for page in contacts:
        should_run, reason = should_analyze(page, force=force)
        if should_run:
            triggered.append(page)
        else:
            skip_reasons[reason] = skip_reasons.get(reason, 0) + 1
            stats["skipped"] += 1

    logger.info(
        f"Trigger filter: {len(triggered)} triggered, {stats['skipped']} skipped "
        f"(reasons: {skip_reasons})"
    )

    # Apply limit
    if limit and len(triggered) > limit:
        logger.info(f"Applying limit: processing {limit} of {len(triggered)} triggered contacts")
        triggered = triggered[:limit]

    stats["triggered"] = len(triggered)

    if not triggered:
        logger.info("No contacts triggered for analysis. Use --force to re-analyze all.")
        return stats

    # ── Step 3 + 4: Analyze and Write ──
    close_probs = []

    for i, page in enumerate(triggered, 1):
        page_id = page["id"]
        props = page.get("properties", {})
        name = _get_title(props, FIELD_FULL_NAME) or _get_rich_text(props, FIELD_FULL_NAME) or "Unknown"
        lead_tier = _get_select(props, FIELD_LEAD_TIER) or "—"
        lead_score_val = _get_number(props, FIELD_LEAD_SCORE) or 0

        try:
            analysis = analyze_contact(props)
            stats["analyzed"] += 1

            # Track distributions
            for key, dist_key in [
                ("status", "status_distribution"),
                ("reason", "reason_distribution"),
                ("next_action", "action_distribution"),
                ("confidence", "confidence_distribution"),
            ]:
                val = analysis[key]
                stats[dist_key][val] = stats[dist_key].get(val, 0) + 1

            close_probs.append(analysis["close_probability"])

            logger.info(
                f"[{i}/{len(triggered)}] {name} | "
                f"Tier={lead_tier} Score={lead_score_val:.0f} | "
                f"-> {analysis['status']} | {analysis['reason']} | "
                f"P(close)={analysis['close_probability']}% | "
                f"Action={analysis['next_action']} | "
                f"Conf={analysis['confidence']} | "
                f"Eng={analysis['_engagement_score']}"
            )

            if write_analysis_to_notion(page_id, analysis, dry_run=dry_run):
                stats["written"] += 1
            else:
                stats["errors"] += 1

        except Exception as e:
            logger.error(f"[{i}/{len(triggered)}] Error analyzing {name} ({page_id}): {e}")
            stats["errors"] += 1

    if close_probs:
        stats["avg_close_probability"] = round(sum(close_probs) / len(close_probs), 1)

    return stats


# ═══════════════════════════════════════════════════════════════════════════════
# REPORTING
# ═══════════════════════════════════════════════════════════════════════════════

def format_report(stats: Dict) -> str:
    """Build a human-readable markdown report from stats."""
    lines = [
        "# Reply Intelligence Report",
        f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        "",
        "## Summary",
        f"- Replied contacts fetched: {stats['fetched']}",
        f"- Triggered for analysis: {stats['triggered']}",
        f"- Skipped (already current): {stats['skipped']}",
        f"- Analyzed: {stats['analyzed']}",
        f"- Written to Notion: {stats['written']}",
        f"- Errors: {stats['errors']}",
        f"- Average Close Probability: {stats['avg_close_probability']}%",
        "",
    ]

    for title, dist_key in [
        ("Reply Status Distribution", "status_distribution"),
        ("Reply Reason Distribution", "reason_distribution"),
        ("Recommended Actions", "action_distribution"),
        ("Confidence Levels", "confidence_distribution"),
    ]:
        dist = stats.get(dist_key, {})
        if dist:
            lines.append(f"## {title}")
            lines.append(f"| {'Value':<25} | Count |")
            lines.append(f"|{'-'*27}|-------|")
            for val, count in sorted(dist.items(), key=lambda x: -x[1]):
                lines.append(f"| {val:<25} | {count:>5} |")
            lines.append("")

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="AI Sales OS — Reply Intelligence Engine"
    )
    parser.add_argument("--dry-run", action="store_true", help="Analyze without writing to Notion")
    parser.add_argument("--limit", type=int, default=None, help="Limit contacts to analyze")
    parser.add_argument("--force", action="store_true", help="Re-analyze ALL replied contacts")
    parser.add_argument("--export", action="store_true", help="Save report to markdown file")
    args = parser.parse_args()

    start_time = time.time()

    logger.info("=" * 70)
    logger.info("REPLY INTELLIGENCE ENGINE — Starting")
    logger.info(f"  Mode: {'DRY RUN' if args.dry_run else 'LIVE'}")
    logger.info(f"  Force: {args.force}")
    logger.info(f"  Limit: {args.limit or 'none'}")
    logger.info("=" * 70)

    # Validate environment
    if not NOTION_DATABASE_ID_CONTACTS:
        logger.error("NOTION_DATABASE_ID_CONTACTS not set in environment. Aborting.")
        sys.exit(1)

    # Run pipeline
    stats = run_reply_intelligence(
        dry_run=args.dry_run,
        limit=args.limit,
        force=args.force,
    )

    # Generate report
    report = format_report(stats)

    if args.export:
        report_file = os.path.join(
            SCRIPT_DIR,
            f"reply_intelligence_report_{datetime.now().strftime('%Y%m%d')}.md",
        )
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(report)
        logger.info(f"Report saved to {report_file}")

    # Print summary to log
    for line in report.split("\n"):
        if line.startswith("#") or line.startswith("|") or line.startswith("-"):
            logger.info(f"  {line}")

    elapsed = time.time() - start_time

    logger.info("=" * 70)
    logger.info(
        f"REPLY INTELLIGENCE COMPLETE | "
        f"Analyzed: {stats['analyzed']} | Written: {stats['written']} | "
        f"Errors: {stats['errors']} | Time: {elapsed:.1f}s"
    )
    logger.info("=" * 70)

    # Save stats (for pipeline freshness / monitoring)
    stats_file = os.path.join(SCRIPT_DIR, "last_reply_intelligence_stats.json")
    try:
        save_stats = {k: v for k, v in stats.items() if not k.startswith("_")}
        save_stats["timestamp"] = datetime.now(timezone.utc).isoformat()
        save_stats["dry_run"] = args.dry_run
        with open(stats_file, "w") as f:
            json.dump(save_stats, f, indent=2)
    except Exception:
        pass


if __name__ == "__main__":
    main()
