#!/usr/bin/env python3
"""
AI Sales OS — Auto Sequence Enrollment

Automatically enrolls Action Ready contacts into Apollo Sequences
based on Lead Tier + Role category. Round-robins between senders.

Flow:
  1. Fetch Action Ready contacts NOT already "In Sequence"
  2. Detect role category (Finance, Legal, Sales, General)
  3. Map (Tier, Role) → Apollo Sequence ID
  4. Round-robin sender assignment
  5. Enroll via Apollo API
  6. Update Notion Outreach Status → "In Sequence"

Usage:
    python auto_sequence.py                     # enroll all eligible contacts
    python auto_sequence.py --dry-run           # preview without enrolling
    python auto_sequence.py --limit 10          # limit to first N
    python auto_sequence.py --tier HOT          # only HOT contacts
    python auto_sequence.py --sender ragheed    # force specific sender
"""
import sys as _sys, os as _os; _sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
import os
import sys
import json
import logging
import time
import argparse
import re
from typing import Dict, List, Optional, Tuple
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.dirname(__file__))
from core.notion_helpers import (
    NOTION_DATABASE_ID_CONTACTS,
    update_page,
    rate_limiter,
    notion_request,
    NOTION_BASE_URL,
)
from core.constants import (
    FIELD_LEAD_SCORE, FIELD_LEAD_TIER, FIELD_ACTION_READY,
    FIELD_OUTREACH_STATUS, FIELD_SENIORITY, FIELD_TITLE,
    FIELD_EMAIL, FIELD_FULL_NAME, FIELD_APOLLO_CONTACT_ID,
    FIELD_DO_NOT_CALL,
    TIER_HOT, TIER_WARM,
    SCORE_HOT, SCORE_WARM,
    OUTREACH_BLOCKED,
    # AI Sales Actions
    FIELD_AI_ACTION_TYPE, FIELD_AI_EMAIL_SUBJECT,
    AI_ACTION_CALL, AI_ACTION_EMAIL, AI_ACTION_SEQUENCE, AI_ACTION_NONE,
)

NOTION_DATABASE_ID_COMPANIES = os.getenv("NOTION_DATABASE_ID_COMPANIES")


def preload_company_ai_actions(company_ids: set) -> Dict[str, str]:
    """Return {company_page_id: ai_action_type} for the given set.

    Queries the Companies DB once and filters to requested IDs.
    Only includes entries with a non-empty action type.
    """
    if not company_ids or not NOTION_DATABASE_ID_COMPANIES:
        return {}
    out: Dict[str, str] = {}
    cursor = None
    while True:
        body = {"page_size": 100}
        if cursor:
            body["start_cursor"] = cursor
        rate_limiter.wait()
        try:
            resp = notion_request(
                "POST",
                f"{NOTION_BASE_URL}/databases/{NOTION_DATABASE_ID_COMPANIES}/query",
                json=body,
            )
            data = resp.json()
        except Exception as e:
            logger.error(f"Error preloading company AI actions: {e}")
            break
        for page in data.get("results", []):
            pid = page["id"]
            if pid not in company_ids:
                continue
            sel = page.get("properties", {}).get(FIELD_AI_ACTION_TYPE, {}).get("select")
            if sel and sel.get("name"):
                out[pid] = sel["name"]
        if not data.get("has_more"):
            break
        cursor = data.get("next_cursor")
    return out

# ─── Config ──────────────────────────────────────────────────────────────────

APOLLO_API_KEY = os.getenv("APOLLO_API_KEY")
APOLLO_BASE_URL = "https://api.apollo.io/api/v1"

# ─── Email Accounts (round-robin senders) ────────────────────────────────────

EMAIL_ACCOUNTS = {
    "ragheed": [
        {"id": "69ae0b048808c5002115d96e", "email": "ragheed@joinmuhide.com"},
        {"id": "68a5a63d4cef7600114c08f2", "email": "ragheed.a@ratlfintech.com"},
    ],
    "ibrahim": [
        {"id": "69ae0b2d8808c5002115dbfd", "email": "ibrahim@joinmuhide.com"},
        {"id": "67d029c075e828001de8e5cf", "email": "ibrahim.a@muhide.com"},
    ],
    "soha": [
        {"id": "699db1a35b8396000d22b78d", "email": "soha@joinmuhide.com"},
        {"id": "68d923390628b20011d261a9", "email": "soha@ratlfintech.com"},
    ],
}

# Round-robin order for automatic sender assignment
SENDER_ROTATION = ["ragheed", "ibrahim"]
_sender_index = 0

# ─── Sequence Mapping ────────────────────────────────────────────────────────
# Maps (Tier, Role) → Apollo Sequence ID
# Built from actual Apollo sequences

SEQUENCE_MAP = {
    # HOT leads — more aggressive sequences
    ("HOT", "ceo"): "69a887edb72a4a0019a5824b",           # Building Materials - CEOs/Owner - Risk & Control
    ("HOT", "cfo"): "69a89267c017cd00151e06f7",           # Building Materials - CFOs/Finance Managers - Risk & Control
    ("HOT", "sales"): "69b9264ece3973001d8b6862",         # Ragheed - Building Materials - Sales Directors/Managers
    ("HOT", "legal"): "699da3276f9437002139b817",         # Ragheed - Building Materials - Legal/Compliance
    ("HOT", "general"): "69a88207cccd68000da7d983",       # Building Materials - CEOs/Owner - Sales Focussed

    # WARM leads — nurture sequences
    ("WARM", "ceo"): "69a88207cccd68000da7d983",          # CEOs/Owner - Sales Focussed
    ("WARM", "cfo"): "69a88c8beeae3f00153a42b5",          # Ibrahim - Building Materials- CFOs/Finance Managers - Sales Focussed
    ("WARM", "sales"): "69a8960eca0c91000df4f949",        # Building Materials - Sales Directors/Managers (All)
    ("WARM", "legal"): "69a8c0f7024732001900a315",        # Legal/Compliance
    ("WARM", "general"): "69a8960eca0c91000df4f949",      # Building Materials - Sales Directors/Managers (All)
}

# Fallback sequences if specific mapping not found
FALLBACK_SEQUENCES = {
    "HOT": "69a88207cccd68000da7d983",    # CEOs/Owner - Sales Focussed
    "WARM": "69a8960eca0c91000df4f949",   # Sales Directors/Managers (All)
}

# ─── Logging ─────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("auto_sequence.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


# ─── Role Detection ─────────────────────────────────────────────────────────

def detect_role_category(seniority: str, title: str) -> str:
    """
    Detect role category from seniority + title.
    Returns: 'ceo', 'cfo', 'sales', 'legal', or 'general'
    """
    title_lower = (title or "").lower()
    seniority_lower = (seniority or "").lower()

    # CEO/Owner/Founder detection
    if any(kw in title_lower for kw in ["ceo", "chief executive", "owner", "founder", "managing director", "president"]):
        return "ceo"
    if seniority_lower in ("owner", "founder"):
        return "ceo"

    # CFO/Finance detection
    if any(kw in title_lower for kw in ["cfo", "chief financial", "finance director", "finance manager",
                                         "financial controller", "treasurer", "comptroller", "accounting"]):
        return "cfo"

    # Legal/Compliance detection
    if any(kw in title_lower for kw in ["legal", "compliance", "counsel", "attorney", "lawyer",
                                         "regulatory", "governance"]):
        return "legal"

    # Sales detection
    if any(kw in title_lower for kw in ["sales", "business development", "commercial", "revenue",
                                         "account executive", "account manager", "partnerships"]):
        return "sales"

    # C-Suite that doesn't match above → general
    if seniority_lower in ("c-suite", "c suite"):
        return "ceo"

    return "general"


# ─── Get Next Sender ─────────────────────────────────────────────────────────

def get_next_sender(forced: Optional[str] = None) -> Tuple[str, Dict]:
    """Get next sender in round-robin rotation."""
    global _sender_index

    if forced and forced in EMAIL_ACCOUNTS:
        accounts = EMAIL_ACCOUNTS[forced]
        account = accounts[_sender_index % len(accounts)]
        return forced, account

    sender_name = SENDER_ROTATION[_sender_index % len(SENDER_ROTATION)]
    accounts = EMAIL_ACCOUNTS[sender_name]
    account = accounts[(_sender_index // len(SENDER_ROTATION)) % len(accounts)]
    _sender_index += 1
    return sender_name, account


# ─── Apollo API ──────────────────────────────────────────────────────────────

def apollo_request(method: str, url: str, max_retries: int = 5, **kwargs):
    """Apollo API request with retry.

    Auth: Apollo deprecated api_key in body/query. X-Api-Key header is now required.
    This helper injects the header defensively for every caller, matching the
    pattern in core/daily_sync.py::apollo_headers().
    """
    import requests
    kwargs.setdefault("timeout", 30)

    # Inject X-Api-Key header (required by Apollo — body/query auth deprecated)
    headers = kwargs.pop("headers", {}) or {}
    headers.setdefault("X-Api-Key", APOLLO_API_KEY)
    headers.setdefault("Content-Type", "application/json")
    kwargs["headers"] = headers

    for attempt in range(max_retries):
        try:
            resp = requests.request(method, url, **kwargs)
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            if attempt < max_retries - 1:
                wait = min(2 ** attempt, 30)
                logger.warning(f"Connection error (attempt {attempt + 1}): {e}, retrying in {wait}s")
                time.sleep(wait)
                continue
            raise

        if resp.status_code == 429:
            wait = float(resp.headers.get("Retry-After", min(2 ** attempt, 30)))
            logger.warning(f"Rate limited, waiting {wait}s")
            time.sleep(wait)
            continue

        if resp.status_code >= 500:
            wait = min(2 ** attempt, 30)
            time.sleep(wait)
            continue

        if resp.status_code >= 400:
            logger.error(f"Apollo API error {resp.status_code}: {resp.text[:300]}")

        resp.raise_for_status()
        return resp

    raise Exception(f"Failed after {max_retries} retries")


def enroll_contact_in_sequence(
    apollo_contact_id: str,
    sequence_id: str,
    email_account_id: str,
) -> bool:
    """Add a contact to an Apollo sequence."""
    try:
        resp = apollo_request(
            "POST",
            f"{APOLLO_BASE_URL}/emailer_campaigns/{sequence_id}/add_contact_ids",
            json={
                # api_key removed — Apollo deprecated body auth; X-Api-Key header
                # is injected by apollo_request() above.
                "contact_ids": [apollo_contact_id],
                "emailer_campaign_id": sequence_id,
                "send_email_from_email_account_id": email_account_id,
            },
        )
        return resp.status_code < 400
    except Exception as e:
        logger.error(f"Failed to enroll {apollo_contact_id} in sequence {sequence_id}: {e}")
        return False


# ─── Fetch Eligible Contacts ─────────────────────────────────────────────────

def fetch_eligible_contacts(tier_filter: Optional[str] = None, limit: Optional[int] = None) -> List[Dict]:
    """
    Fetch contacts that are:
    - Action Ready = True
    - Outreach Status is NOT "In Sequence", not blocked
    - Has email
    - Has Apollo Contact ID
    """
    results = []
    cursor = None

    min_score = SCORE_HOT if tier_filter == "HOT" else SCORE_WARM

    while True:
        body = {
            "page_size": 100,
            "filter": {
                "and": [
                    {"property": FIELD_ACTION_READY, "checkbox": {"equals": True}},
                    {"property": FIELD_LEAD_SCORE, "number": {"greater_than_or_equal_to": min_score}},
                ]
            },
            "sorts": [{"property": FIELD_LEAD_SCORE, "direction": "descending"}],
        }
        if cursor:
            body["start_cursor"] = cursor

        rate_limiter.wait()
        try:
            resp = notion_request("POST", f"{NOTION_BASE_URL}/databases/{NOTION_DATABASE_ID_CONTACTS}/query", json=body)
            data = resp.json()
        except Exception as e:
            logger.error(f"Error fetching contacts: {e}")
            break

        for page in data.get("results", []):
            props = page.get("properties", {})

            # Extract fields
            def get_title(p):
                items = props.get(p, {}).get("title", [])
                return items[0]["text"]["content"] if items else ""

            def get_text(p):
                items = props.get(p, {}).get("rich_text", [])
                return items[0]["text"]["content"] if items else ""

            def get_select(p):
                sel = props.get(p, {}).get("select")
                return sel.get("name") if sel else ""

            def get_number(p):
                return props.get(p, {}).get("number", 0) or 0

            def get_email(p):
                return props.get(p, {}).get("email", "")

            def get_checkbox(p):
                return props.get(p, {}).get("checkbox", False)

            outreach = get_select(FIELD_OUTREACH_STATUS)

            # Skip if already in sequence or blocked
            if outreach == "In Sequence":
                continue
            if outreach in OUTREACH_BLOCKED:
                continue
            if get_checkbox(FIELD_DO_NOT_CALL):
                continue

            apollo_id = get_text(FIELD_APOLLO_CONTACT_ID)
            email = get_email(FIELD_EMAIL)

            # Must have Apollo ID and email
            if not apollo_id or not email:
                continue

            # Read Company relation (first link) + AI Email presence for gating
            company_rel = props.get("Company", {}).get("relation") or []
            company_ids = [r["id"] for r in company_rel if r.get("id")]
            ai_email_rt = props.get(FIELD_AI_EMAIL_SUBJECT, {}).get("rich_text") or []
            has_ai_email = any(seg.get("plain_text", "").strip() for seg in ai_email_rt)

            contact = {
                "page_id": page["id"],
                "name": get_title(FIELD_FULL_NAME),
                "email": email,
                "apollo_contact_id": apollo_id,
                "score": get_number(FIELD_LEAD_SCORE),
                "tier": get_select(FIELD_LEAD_TIER),
                "seniority": get_select(FIELD_SENIORITY),
                "title": get_text(FIELD_TITLE) if props.get(FIELD_TITLE, {}).get("type") == "rich_text" else get_select(FIELD_TITLE),
                "outreach_status": outreach,
                "company_ids": company_ids,
                "has_ai_email": has_ai_email,
            }
            results.append(contact)

        if limit and len(results) >= limit:
            results = results[:limit]
            break

        if not data.get("has_more"):
            break
        cursor = data.get("next_cursor")

    logger.info(f"Found {len(results)} eligible contacts for sequence enrollment")
    return results


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="AI Sales OS — Auto Sequence Enrollment")
    parser.add_argument("--dry-run", action="store_true", help="Preview without enrolling")
    parser.add_argument("--limit", type=int, default=None, help="Limit to first N contacts")
    parser.add_argument("--tier", choices=["HOT", "WARM"], default=None, help="Only process specific tier")
    parser.add_argument("--sender", choices=list(EMAIL_ACCOUNTS.keys()), default=None, help="Force specific sender")
    args = parser.parse_args()

    logger.info("=" * 70)
    logger.info(f"AUTO SEQUENCE | Dry Run: {args.dry_run} | Limit: {args.limit or 'ALL'} | Tier: {args.tier or 'ALL'}")
    logger.info("=" * 70)

    start_time = time.time()

    # Step 1: Fetch eligible contacts
    logger.info("Step 1: Fetching eligible contacts...")
    contacts = fetch_eligible_contacts(tier_filter=args.tier, limit=args.limit)

    if not contacts:
        logger.info("No eligible contacts found. Done!")
        return

    # Step 1b: Preload company-level AI Action Type for gating
    logger.info("Step 1b: Preloading company AI Action Type...")
    unique_company_ids = {cid for c in contacts for cid in c.get("company_ids", [])}
    company_ai_action = preload_company_ai_actions(unique_company_ids)
    logger.info(f"  {len(company_ai_action)} companies have an AI Action Type set")

    # Step 2: Enroll contacts
    logger.info(f"Step 2: Processing {len(contacts)} contacts...")
    stats = {
        "enrolled": 0, "no_sequence": 0, "errors": 0, "skipped": 0,
        "skipped_ai_none": 0, "skipped_ai_call_only": 0, "ai_email_drafts": 0,
    }

    for i, contact in enumerate(contacts, 1):
        tier = contact["tier"] or ("HOT" if contact["score"] >= SCORE_HOT else "WARM")
        role = detect_role_category(contact["seniority"], contact["title"])

        # ── AI Sales Actions gating ──
        # If the company has an explicit AI Action Type, respect it:
        #   None      → skip entirely (Apollo says do not contact)
        #   Call      → skip sequence (auto_tasks handles call follow-up)
        #   Email     → proceed (current behaviour: stock sequence; future: per-contact copy)
        #   Sequence  → proceed
        company_action = ""
        for cid in contact.get("company_ids", []):
            if cid in company_ai_action:
                company_action = company_ai_action[cid]
                break
        if company_action == AI_ACTION_NONE:
            stats["skipped_ai_none"] += 1
            continue
        if company_action == AI_ACTION_CALL:
            stats["skipped_ai_call_only"] += 1
            continue
        if contact.get("has_ai_email"):
            # Contact has an AI-generated email draft propagated by the enricher.
            # We still enroll in a stock sequence today, but log the override opportunity
            # so a future v1.2 can push per-contact copy via a custom campaign.
            stats["ai_email_drafts"] += 1
            logger.info(
                f"  [{i}/{len(contacts)}] AI Email Draft present for {contact['name']} — "
                f"stock sequence will be used (future: override with AI copy)"
            )

        # Find matching sequence
        sequence_id = SEQUENCE_MAP.get((tier, role))
        if not sequence_id:
            sequence_id = FALLBACK_SEQUENCES.get(tier)

        if not sequence_id:
            stats["no_sequence"] += 1
            logger.warning(f"  No sequence for tier={tier} role={role}: {contact['name']}")
            continue

        # Get sender
        sender_name, sender_account = get_next_sender(forced=args.sender)

        if args.dry_run:
            logger.info(
                f"  [{i}/{len(contacts)}] [DRY RUN] {contact['name']} | "
                f"Score={contact['score']:.0f} | Tier={tier} | Role={role} | "
                f"Sender={sender_name} ({sender_account['email']}) | "
                f"Sequence={sequence_id[:12]}..."
            )
            stats["enrolled"] += 1
            continue

        # Enroll in Apollo
        success = enroll_contact_in_sequence(
            apollo_contact_id=contact["apollo_contact_id"],
            sequence_id=sequence_id,
            email_account_id=sender_account["id"],
        )

        if success:
            # Update Notion outreach status
            try:
                update_page(contact["page_id"], {
                    FIELD_OUTREACH_STATUS: {"select": {"name": "In Sequence"}},
                })
            except Exception as e:
                logger.warning(f"Enrolled but failed to update Notion: {e}")

            stats["enrolled"] += 1
            logger.info(
                f"  [{i}/{len(contacts)}] Enrolled: {contact['name']} | "
                f"Tier={tier} | Role={role} | Sender={sender_name}"
            )
        else:
            stats["errors"] += 1

        # Rate limit
        time.sleep(0.3)

    elapsed = time.time() - start_time

    logger.info("=" * 70)
    logger.info(f"AUTO SEQUENCE COMPLETE")
    logger.info(f"  Enrolled: {stats['enrolled']}")
    logger.info(f"  No matching sequence: {stats['no_sequence']}")
    logger.info(f"  Skipped (AI=None): {stats['skipped_ai_none']}")
    logger.info(f"  Skipped (AI=Call only): {stats['skipped_ai_call_only']}")
    logger.info(f"  AI email drafts present: {stats['ai_email_drafts']}")
    logger.info(f"  Errors: {stats['errors']}")
    logger.info(f"  Time: {elapsed:.1f}s")
    logger.info("=" * 70)

    # Save stats
    stats_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "last_sequence_stats.json")
    try:
        with open(stats_file, "w") as f:
            json.dump(stats, f, indent=2)
    except Exception:
        pass


if __name__ == "__main__":
    main()
