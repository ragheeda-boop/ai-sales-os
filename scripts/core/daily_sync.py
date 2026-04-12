#!/usr/bin/env python3
"""
Apollo → Notion Sync (v4.0 — Company-Centric + Governed Ingestion)

Three sync modes:
    incremental  – Pull recently updated records (default: last 24h)
    backfill     – Pull a wider historical range with checkpoint logging
    full         – Pull ALL records from Apollo (no date filter), full rebuild

v4.0 changes:
    - Integrated Ingestion Gate: companies must pass gate before sync
    - --gate flag controls gate mode (strict/review/audit/off)
    - Gate runs AFTER Apollo fetch, BEFORE Notion write

Usage:
    python daily_sync.py --mode incremental --days 7
    python daily_sync.py --mode incremental --gate strict       # enforce gate
    python daily_sync.py --mode incremental --gate audit        # log only
    python daily_sync.py --mode incremental --gate off          # disable gate
    python daily_sync.py --mode backfill --days 365
    python daily_sync.py --mode full
    python daily_sync.py                          # defaults to incremental --hours 24
"""
import sys as _sys, os as _os; _sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import os
import sys
import json
import logging
import requests
import time
import argparse
from typing import Dict, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.dirname(__file__))
from notion_helpers import (
    NOTION_DATABASE_ID_CONTACTS,
    NOTION_DATABASE_ID_COMPANIES,
    preload_companies,
    preload_contacts,
    create_page,
    update_page,
    rate_limiter,
    notion_request,
    NOTION_BASE_URL,
)
from constants import (
    APOLLO_OWNER_MAP,
    CAMPAIGN_FAILED_STATUSES,
    FIELD_CONTACT_OWNER,
    FIELD_COMPANY_OWNERS,
    FIELD_PRIMARY_COMPANY_OWNER,
    FIELD_SUPPORTING_OWNERS,
    FIELD_COMPANY_STAGE,
    FIELD_ACTIVE_CONTACTS,
    FIELD_EMAILED_CONTACTS,
    FIELD_ENGAGED_CONTACTS,
    FIELD_LAST_ENGAGEMENT_DATE,
    FIELD_SALES_OS_ACTIVE,
    COMPANY_STAGE_PROSPECT,
    COMPANY_STAGE_OUTREACH,
    COMPANY_STAGE_ENGAGED,
    COMPANY_STAGE_MEETING,
    COMPANY_STAGE_OPPORTUNITY,
    COMPANY_STAGE_CUSTOMER,
    COMPANY_STAGE_CHURNED,
    COMPANY_STAGE_ARCHIVED,
    GOVERNANCE_MODE_STRICT,
    GOVERNANCE_MODE_AUDIT,
)
from governance.ingestion_gate import IngestionGateRunner

# ─── Config ──────────────────────────────────────────────────────────────────

APOLLO_API_KEY = os.getenv("APOLLO_API_KEY")
APOLLO_BASE_URL = "https://api.apollo.io/v1"
MAX_WORKERS = 3

# Apollo pagination limits
APOLLO_MAX_PAGES = 500
APOLLO_PAGE_SIZE = 100
APOLLO_WINDOW_LIMIT = APOLLO_MAX_PAGES * APOLLO_PAGE_SIZE  # 50,000

# Checkpoint file for backfill mode
CHECKPOINT_FILE = os.path.join(os.path.dirname(__file__), "backfill_checkpoint.json")

# ─── Logging ─────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(os.path.dirname(os.path.abspath(__file__)), "daily_sync.log"), encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


# ─── Sync Stats Tracker ─────────────────────────────────────────────────────

class SyncStats:
    """Track detailed sync statistics for enhanced logging."""

    def __init__(self):
        self.apollo_fetched_contacts = 0
        self.apollo_fetched_accounts = 0
        self.notion_created_contacts = 0
        self.notion_updated_contacts = 0
        self.notion_created_companies = 0
        self.notion_updated_companies = 0
        self.skipped_unchanged = 0
        self.duplicates_prevented = 0
        self.failed_contacts = 0
        self.failed_companies = 0
        self.earliest_updated_at: Optional[str] = None
        self.latest_updated_at: Optional[str] = None
        # Run metadata — set by main() before save() is called
        self.mode: Optional[str] = None
        self.started_at: Optional[str] = None
        self.completed_at: Optional[str] = None
        self.duration_seconds: Optional[float] = None

    def track_updated_at(self, updated_at: Optional[str]):
        """Track earliest and latest updated_at timestamps."""
        if not updated_at:
            return
        if self.earliest_updated_at is None or updated_at < self.earliest_updated_at:
            self.earliest_updated_at = updated_at
        if self.latest_updated_at is None or updated_at > self.latest_updated_at:
            self.latest_updated_at = updated_at

    def summary(self) -> str:
        lines = [
            "─── SYNC SUMMARY ───────────────────────────────────────",
            f"  Apollo fetched:     {self.apollo_fetched_contacts} contacts, {self.apollo_fetched_accounts} accounts",
            f"  Notion created:     {self.notion_created_contacts} contacts, {self.notion_created_companies} companies",
            f"  Notion updated:     {self.notion_updated_contacts} contacts, {self.notion_updated_companies} companies",
            f"  Duplicates prevented: {self.duplicates_prevented}",
            f"  Failed:             {self.failed_contacts} contacts, {self.failed_companies} companies",
            f"  Earliest updated_at: {self.earliest_updated_at or 'N/A'}",
            f"  Latest updated_at:   {self.latest_updated_at or 'N/A'}",
            "────────────────────────────────────────────────────────",
        ]
        return "\n".join(lines)

    def to_dict(self) -> Dict:
        """Serializable dict for last_sync_stats.json export."""
        return {
            "mode":                    self.mode,
            "started_at":              self.started_at,
            "completed_at":            self.completed_at,
            "duration_seconds":        self.duration_seconds,
            "apollo_fetched_contacts": self.apollo_fetched_contacts,
            "apollo_fetched_accounts": self.apollo_fetched_accounts,
            "notion_created_contacts": self.notion_created_contacts,
            "notion_updated_contacts": self.notion_updated_contacts,
            "notion_created_companies": self.notion_created_companies,
            "notion_updated_companies": self.notion_updated_companies,
            "duplicates_prevented":    self.duplicates_prevented,
            "failed_contacts":         self.failed_contacts,
            "failed_companies":        self.failed_companies,
            "skipped_unchanged":       self.skipped_unchanged,
            "earliest_updated_at":     self.earliest_updated_at,
            "latest_updated_at":       self.latest_updated_at,
        }

    def save(self) -> str:
        """Persist stats to scripts/core/last_sync_stats.json.

        Called from main() after every run. The file is consumed by
        monitoring/health_check.py and uploaded by the GitHub Actions
        workflow for Job 2 visibility. Writing lives next to this script
        so the path is stable regardless of CWD.
        """
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "last_sync_stats.json")
        tmp = path + ".tmp"
        with open(tmp, "w") as f:
            json.dump(self.to_dict(), f, indent=2, default=str)
        os.replace(tmp, path)
        logger.info(f"Stats → {path}")
        return path


# ─── Apollo Helpers ──────────────────────────────────────────────────────────

def apollo_headers() -> Dict[str, str]:
    return {
        "Content-Type": "application/json",
        "X-Api-Key": APOLLO_API_KEY,
    }


def apollo_request(url: str, body: dict, max_retries: int = 5) -> Optional[dict]:
    """
    Make an Apollo API request with retry logic for connection errors.
    Returns parsed JSON or None on permanent failure.
    """
    for attempt in range(max_retries):
        try:
            resp = requests.post(url, json=body, headers=apollo_headers(), timeout=30)
            resp.raise_for_status()
            return resp.json()
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            if attempt < max_retries - 1:
                wait = min(2 ** attempt, 30)
                logger.warning(f"Apollo connection error (attempt {attempt + 1}/{max_retries}): {type(e).__name__}, retrying in {wait}s")
                time.sleep(wait)
                continue
            logger.error(f"Apollo connection error after {max_retries} retries: {e}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Apollo API error: {e}")
            return None


# ─── Fetch Functions: Date-Filtered (incremental / backfill) ─────────────────

def _fetch_with_date_filter(
    endpoint: str,
    record_key: str,
    date_range_key: str,
    sort_field: str,
    since: datetime,
    stats: SyncStats,
    label: str = "records",
) -> List[Dict]:
    """
    Generic date-filtered fetch with time-window splitting.
    Used by both incremental and backfill modes.

    Note: Apollo's date filter uses day-granularity only. A local timestamp
    filter is applied after fetch as a safety net to ensure only records
    genuinely updated within the requested window are returned.
    """
    all_records = []
    seen_ids = set()
    current_since = since.strftime("%Y-%m-%d")

    logger.info(f"Fetching Apollo {label} updated since {current_since}...")

    while True:
        page = 1
        window_records = []

        while page <= APOLLO_MAX_PAGES:
            body = {
                "page": page,
                "per_page": APOLLO_PAGE_SIZE,
                date_range_key: {"min": current_since},
                "sort_by_field": sort_field,
                "sort_ascending": True,
            }

            data = apollo_request(f"{APOLLO_BASE_URL}/{endpoint}", body)
            if data is None:
                break

            records = data.get(record_key, [])
            if not records:
                break

            window_records.extend(records)
            logger.info(f"  Page {page}: {len(records)} {label} (window: {len(window_records)}, total: {len(all_records) + len(window_records)})")
            page += 1
            time.sleep(0.1)

        # Deduplicate and track updated_at
        new_in_window = 0
        for r in window_records:
            rid = r.get("id")
            if rid and rid not in seen_ids:
                seen_ids.add(rid)
                all_records.append(r)
                new_in_window += 1
                stats.track_updated_at(r.get("updated_at"))
            elif rid:
                stats.duplicates_prevented += 1

        logger.info(f"  Window done: {len(window_records)} fetched, {new_in_window} new, {len(window_records) - new_in_window} duplicates skipped")

        # Time-window splitting if we hit the pagination ceiling
        if len(window_records) >= APOLLO_WINDOW_LIMIT:
            last_updated = window_records[-1].get("updated_at")
            if last_updated:
                new_since = last_updated[:10]  # "YYYY-MM-DD"
                if new_since == current_since:
                    dt = datetime.strptime(new_since, "%Y-%m-%d") + timedelta(days=1)
                    new_since = dt.strftime("%Y-%m-%d")
                logger.info(f"  Hit {APOLLO_WINDOW_LIMIT} limit, advancing window from {current_since} → {new_since}")
                current_since = new_since
                continue
            else:
                logger.warning(f"  Could not find updated_at on last record, stopping window split")
                break
        else:
            break

    # ── Local timestamp safety filter ────────────────────────────────────────
    # Apollo's API filter uses date-only precision and may return records from
    # the full calendar day instead of the exact requested hour window.
    # We apply a client-side filter to drop anything genuinely outside the window.
    since_str = since.strftime("%Y-%m-%dT%H:%M:%S")  # e.g. "2026-03-28T05:00:00"
    original_count = len(all_records)
    all_records = [
        r for r in all_records
        if not r.get("updated_at") or r.get("updated_at", "")[:19] >= since_str
    ]
    dropped = original_count - len(all_records)
    if dropped > 0:
        logger.warning(
            f"⚠️  Local timestamp filter removed {dropped} {label} with "
            f"updated_at < {since.strftime('%Y-%m-%d %H:%M')} UTC. "
            f"Apollo's API date filter returned records outside the requested window."
        )
        logger.info(
            f"✅ After local filter: {len(all_records)} {label} "
            f"(was {original_count} before filter)"
        )
    # ─────────────────────────────────────────────────────────────────────────

    logger.info(f"Fetched {len(all_records)} {label} from Apollo (deduplicated from {len(all_records) + stats.duplicates_prevented})")
    return all_records


def fetch_updated_contacts(since: datetime, stats: SyncStats) -> List[Dict]:
    """Fetch contacts updated since a given datetime (incremental/backfill)."""
    results = _fetch_with_date_filter(
        endpoint="contacts/search",
        record_key="contacts",
        date_range_key="contact_updated_at_range",
        sort_field="contact_updated_at",
        since=since,
        stats=stats,
        label="contacts",
    )
    stats.apollo_fetched_contacts = len(results)
    return results


def fetch_updated_accounts(since: datetime, stats: SyncStats) -> List[Dict]:
    """Fetch accounts updated since a given datetime (incremental/backfill)."""
    results = _fetch_with_date_filter(
        endpoint="accounts/search",
        record_key="accounts",
        date_range_key="account_updated_at_range",
        sort_field="account_updated_at",
        since=since,
        stats=stats,
        label="accounts",
    )
    stats.apollo_fetched_accounts = len(results)
    return results


# ─── Fetch Functions: Full Mode (NO date filter) ────────────────────────────

def _fetch_all_paginated(
    endpoint: str,
    record_key: str,
    sort_field: str,
    stats: SyncStats,
    label: str = "records",
) -> List[Dict]:
    """
    Fetch ALL records from Apollo without any date filter.
    Uses alphabetical partitioning (A-Z + other) to bypass the 500-page limit.
    Each partition is sorted by updated_at ascending with time-window splitting.
    """
    all_records = []
    seen_ids = set()

    # Partitioning strategy: first letter of name (A-Z) + catch-all
    # This distributes ~45k contacts across 27 partitions (~1,700 each = well under 50k)
    partitions = list("abcdefghijklmnopqrstuvwxyz") + ["other"]

    logger.info(f"Full mode: fetching ALL {label} using {len(partitions)} alphabetical partitions...")

    for pi, partition in enumerate(partitions, 1):
        page = 1
        partition_count = 0
        partition_dupes = 0

        while page <= APOLLO_MAX_PAGES:
            body = {
                "page": page,
                "per_page": APOLLO_PAGE_SIZE,
                "sort_by_field": sort_field,
                "sort_ascending": True,
            }

            # Add name filter for alphabetical partitioning
            if partition != "other":
                if record_key == "contacts":
                    body["q_person_name"] = f"{partition}*"
                else:
                    body["q_organization_name"] = f"{partition}*"
            else:
                # "other" = names starting with numbers/symbols
                # Use a broad query that catches non-alpha starts
                if record_key == "contacts":
                    body["q_person_name"] = "[0-9]*"
                else:
                    body["q_organization_name"] = "[0-9]*"

            data = apollo_request(f"{APOLLO_BASE_URL}/{endpoint}", body)
            if data is None:
                logger.warning(f"  Partition '{partition}': API failure on page {page}, moving on")
                break

            records = data.get(record_key, [])
            if not records:
                break

            for r in records:
                rid = r.get("id")
                if rid and rid not in seen_ids:
                    seen_ids.add(rid)
                    all_records.append(r)
                    partition_count += 1
                    stats.track_updated_at(r.get("updated_at"))
                elif rid:
                    partition_dupes += 1
                    stats.duplicates_prevented += 1

            total_entries = data.get("pagination", {}).get("total_entries", "?")
            if page == 1:
                logger.info(f"  Partition [{pi}/{len(partitions)}] '{partition}': {total_entries} total entries in Apollo")

            page += 1
            time.sleep(0.1)

        if partition_count > 0 or partition_dupes > 0:
            logger.info(f"  Partition '{partition}' done: {partition_count} new, {partition_dupes} duplicates")

    logger.info(f"Full fetch complete: {len(all_records)} {label} (deduplicated)")
    return all_records


def fetch_all_contacts(stats: SyncStats) -> List[Dict]:
    """Fetch ALL contacts from Apollo (full mode, no date filter)."""
    results = _fetch_all_paginated(
        endpoint="contacts/search",
        record_key="contacts",
        sort_field="contact_updated_at",
        stats=stats,
        label="contacts",
    )
    stats.apollo_fetched_contacts = len(results)
    return results


def fetch_all_accounts(stats: SyncStats) -> List[Dict]:
    """Fetch ALL accounts from Apollo (full mode, no date filter)."""
    results = _fetch_all_paginated(
        endpoint="accounts/search",
        record_key="accounts",
        sort_field="account_updated_at",
        stats=stats,
        label="accounts",
    )
    stats.apollo_fetched_accounts = len(results)
    return results


# ─── Contact Qualification Filter ────────────────────────────────────────────
# Only sync contacts that have:
#   1. An owner assigned (owner_id not null)
#   2. At least one email actually sent (enrolled in campaign + not all failed)

def _contact_has_email_sent(contact: Dict) -> bool:
    """Check if a contact has had at least one email actually sent.

    Requires: emailer_campaign_ids is non-empty AND at least one
    campaign status is not 'failed'. This ensures we only sync
    contacts who received real outreach, not just enrolled ones
    that bounced/failed.
    """
    campaigns = contact.get("emailer_campaign_ids") or []
    if not campaigns:
        return False

    # Check campaign statuses for at least one non-failed
    statuses = contact.get("contact_campaign_statuses") or []
    if not statuses:
        # Has campaigns but no statuses = enrolled, assume sent
        return True

    for cs in statuses:
        status = (cs.get("status") or "").lower()
        if status not in CAMPAIGN_FAILED_STATUSES:
            return True

    # All campaigns failed → email never actually delivered
    return False


def filter_qualified_contacts(contacts: List[Dict], stats: SyncStats) -> List[Dict]:
    """Filter contacts to only those with an owner AND email actually sent.

    This is the core data quality gate:
    - No contact syncs without an owner (owner_id must exist)
    - No contact syncs without real outreach (at least one non-failed campaign)

    Logs detailed breakdown of why contacts were filtered.
    """
    qualified = []
    skipped_no_owner = 0
    skipped_no_email = 0

    for c in contacts:
        owner_id = c.get("owner_id")
        if not owner_id:
            skipped_no_owner += 1
            continue

        if not _contact_has_email_sent(c):
            skipped_no_email += 1
            continue

        qualified.append(c)

    total_skipped = skipped_no_owner + skipped_no_email
    logger.info(
        f"📋 Contact qualification filter: {len(qualified)} passed / {len(contacts)} total "
        f"({total_skipped} filtered: {skipped_no_owner} no owner, {skipped_no_email} no email sent)"
    )

    return qualified


# ─── Checkpoint (backfill mode) ──────────────────────────────────────────────

def load_checkpoint() -> Optional[Dict]:
    """Load backfill checkpoint if it exists."""
    if os.path.exists(CHECKPOINT_FILE):
        try:
            with open(CHECKPOINT_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load checkpoint: {e}")
    return None


def save_checkpoint(data: Dict):
    """Save backfill checkpoint."""
    try:
        with open(CHECKPOINT_FILE, "w") as f:
            json.dump(data, f, indent=2, default=str)
        logger.info(f"Checkpoint saved: {data}")
    except Exception as e:
        logger.warning(f"Could not save checkpoint: {e}")


def clear_checkpoint():
    """Remove checkpoint file after successful completion."""
    if os.path.exists(CHECKPOINT_FILE):
        os.remove(CHECKPOINT_FILE)
        logger.info("Backfill checkpoint cleared (sync complete)")


# ─── Formatting (Apollo API format → Notion) ─────────────────────────────────

def _rt(value: str) -> dict:
    return {"rich_text": [{"text": {"content": str(value)[:2000]}}]}


def _safe_int(val) -> Optional[int]:
    if val is None:
        return None
    try:
        return int(val)
    except (ValueError, TypeError):
        return None


def map_employee_size(count: Optional[int]) -> Optional[str]:
    if not count: return None
    if count <= 10: return "1-10"
    elif count <= 50: return "11-50"
    elif count <= 200: return "51-200"
    elif count <= 500: return "201-500"
    elif count <= 1000: return "501-1000"
    elif count <= 5000: return "1001-5000"
    else: return "5001+"


def format_company_from_api(account: Dict) -> Dict:
    """Format Apollo API account data for Notion."""
    props = {}

    name = account.get("name", "Unknown Company")
    props["Company Name"] = {"title": [{"text": {"content": name[:300]}}]}

    text_map = {
        "Domain": account.get("domain"),
        "Company Address": account.get("raw_address"),
        "Company City": account.get("city"),
        "Company State": account.get("state"),
        "Company Country": account.get("country"),
        "Industry": account.get("industry"),
        "Keywords": ", ".join(account.get("keywords") or []),
        "Technologies": ", ".join(account.get("technologies") or []),
        "Apollo Account Id": account.get("id"),
        "Short Description": account.get("short_description"),
        "Record Source": "Apollo",
        "Data Status": "Raw",
    }
    for prop_name, value in text_map.items():
        if value and str(value).strip():
            props[prop_name] = _rt(str(value).strip())

    url_map = {
        "Website": account.get("website_url"),
        "Company Linkedin Url": account.get("linkedin_url"),
        "Facebook Url": account.get("facebook_url"),
        "Twitter Url": account.get("twitter_url"),
    }
    for prop_name, value in url_map.items():
        if value:
            props[prop_name] = {"url": value}

    phone = account.get("phone")
    if phone:
        props["Company Phone"] = {"phone_number": phone}

    emp = _safe_int(account.get("num_employees"))
    if emp:
        props["Employees"] = {"number": emp}
        es = map_employee_size(emp)
        if es:
            props["Employee Size"] = _rt(es)

    rev = account.get("annual_revenue")
    if rev:
        props["Annual Revenue"] = {"number": rev}

    rev_range = account.get("estimated_annual_revenue")
    if rev_range and str(rev_range).strip():
        props["Revenue Range"] = _rt(str(rev_range).strip())

    funding = account.get("total_funding")
    if funding:
        props["Total Funding"] = {"number": funding}

    latest_funding = account.get("latest_funding_amount")
    if latest_funding:
        props["Latest Funding Amount"] = {"number": latest_funding}

    last_raised = account.get("last_funding_date") or account.get("latest_funding_date")
    if last_raised:
        props["Last Raised At"] = {"date": {"start": str(last_raised)[:10]}}

    account_stage = account.get("stage")
    if account_stage and str(account_stage).strip():
        props["Account Stage"] = {"select": {"name": str(account_stage).strip().title()}}

    # NEW: Headcount Growth signals (percentage change)
    hc_6m = account.get("organization_headcount_six_month_growth") or account.get("headcount_six_month_growth")
    if hc_6m is not None:
        try:
            props["Headcount Growth 6M"] = {"number": round(float(hc_6m), 2)}
        except (ValueError, TypeError):
            pass

    hc_12m = account.get("organization_headcount_twelve_month_growth") or account.get("headcount_twelve_month_growth")
    if hc_12m is not None:
        try:
            props["Headcount Growth 12M"] = {"number": round(float(hc_12m), 2)}
        except (ValueError, TypeError):
            pass

    hc_24m = account.get("organization_headcount_twenty_four_month_growth") or account.get("headcount_twenty_four_month_growth")
    if hc_24m is not None:
        try:
            props["Headcount Growth 24M"] = {"number": round(float(hc_24m), 2)}
        except (ValueError, TypeError):
            pass

    # NEW: AI Qualification from Apollo AI typed_custom_fields
    typed_fields = account.get("typed_custom_fields") or {}

    # AI Qualification Status (extract from first line: "Qualification Status: Qualified/Disqualified/Possible Fit")
    ai_qual_raw = typed_fields.get("6913a64c52c2780001146d22")
    if ai_qual_raw and isinstance(ai_qual_raw, str) and ai_qual_raw.strip():
        # Extract status from first line
        first_line = ai_qual_raw.strip().split("\n")[0]
        qual_status = None
        if "Disqualified" in first_line:
            qual_status = "Disqualified"
        elif "Qualified" in first_line and "Disqualified" not in first_line:
            qual_status = "Qualified"
        elif "Possible Fit" in first_line:
            qual_status = "Possible Fit"

        if qual_status:
            props["AI Qualification Status"] = {"select": {"name": qual_status}}

        # Extract detail (everything after "Detail: ")
        detail_start = ai_qual_raw.find("Detail:")
        if detail_start >= 0:
            detail = ai_qual_raw[detail_start + 7:].strip()
            props["AI Qualification Detail"] = _rt(detail)
        else:
            props["AI Qualification Detail"] = _rt(ai_qual_raw.strip())

    # AI Sales Actions — raw directive block from Apollo (parsed downstream by
    # enrichment/ai_sales_actions_enricher.py). Field ID verified 2026-04-11.
    ai_sales_actions_raw = typed_fields.get("69d979efebf741000dfbce23")
    if ai_sales_actions_raw and isinstance(ai_sales_actions_raw, str) and ai_sales_actions_raw.strip():
        props["AI Sales Actions"] = _rt(ai_sales_actions_raw.strip())

    return props


def _normalize_seniority(raw: str) -> str:
    """Normalize seniority to consistent Notion select values.
    Fixes: 'C suite' vs 'C-Suite', 'Vp' vs 'VP', etc.
    """
    from constants import SENIORITY_NORMALIZE
    key = raw.strip().lower()
    if key in SENIORITY_NORMALIZE:
        return SENIORITY_NORMALIZE[key]
    # Fallback: title-case but preserve known patterns
    return raw.strip().title()


def _infer_contact_stage(contact: Dict) -> Optional[str]:
    """
    Infer Contact Stage from outreach signals when Apollo returns empty Stage.

    T8 (v1.5) — Fixes the 85% empty Stage problem.
    Priority: Meeting Booked > Replied > Outreach Status > Email Sent.
    Only applied when Apollo's stage field is empty.
    Never overwrites Customer/Churned (handled by caller).

    Mapping (from constants.STAGE_INFER_FROM_OUTREACH):
        "Meeting Booked" outreach  → "Engaged"
        "Replied"                  → "Prospect"
        "Opened" / "In Sequence" / "Sent" → "Lead"
        "Bounced" / "Do Not Contact" / "Bad Data" → "Archived"

    Returns None if no signal found (keeps field empty).
    """
    from constants import STAGE_INFER_FROM_OUTREACH, STAGE_INFER_DEFAULT

    # Highest signal: boolean flags
    if contact.get("meeting_booked"):
        return "Engaged"
    if contact.get("replied"):
        return "Prospect"

    # Second signal: Outreach Status
    outreach = (contact.get("outreach_status") or "").lower().strip()
    if outreach and outreach in STAGE_INFER_FROM_OUTREACH:
        return STAGE_INFER_FROM_OUTREACH[outreach]

    # Third signal: email_sent boolean — at minimum, they're a "Lead"
    if contact.get("email_sent") or contact.get("emailer_campaign_ids"):
        return STAGE_INFER_DEFAULT  # "Lead"

    # No signal — don't write anything (preserve empty)
    return None


def format_contact_from_api(contact: Dict, company_page_id: Optional[str] = None) -> Dict:
    """Format Apollo API contact data for Notion.
    v2.1 — Now writes: Stage, Last Contacted, Do Not Call, engagement booleans,
    Departments, Outreach Status (8 fields that were previously missing).
    """
    props = {}

    first = contact.get("first_name", "")
    last = contact.get("last_name", "")
    full = contact.get("name", f"{first} {last}".strip()) or "Unknown"

    props["Full Name"] = {"title": [{"text": {"content": full[:300]}}]}

    text_map = {
        "First Name": first,
        "Last Name": last,
        "Title": contact.get("title"),
        "City": contact.get("city"),
        "State": contact.get("state"),
        "Country": contact.get("country"),
        "Apollo Contact Id": contact.get("id"),
        "Apollo Account Id": contact.get("account_id"),
        "Company Name for Emails": contact.get("organization_name"),
    }

    # NEW: Departments (Apollo sends as list)
    departments = contact.get("departments")
    if departments and isinstance(departments, list):
        text_map["Departments"] = ", ".join(departments)

    for prop_name, value in text_map.items():
        if value and str(value).strip():
            props[prop_name] = _rt(str(value).strip())

    email = contact.get("email")
    if email:
        props["Email"] = {"email": email}

    linkedin = contact.get("linkedin_url")
    if linkedin:
        props["Person Linkedin Url"] = {"url": linkedin}

    # Seniority — normalized to fix "C suite" vs "C-Suite" bug
    seniority = contact.get("seniority")
    if seniority:
        props["Seniority"] = {"select": {"name": _normalize_seniority(seniority)}}

    email_status = contact.get("email_status")
    if email_status:
        props["Email Status"] = {"select": {"name": email_status.title()}}

    # Stage — Apollo value takes priority; if empty, infer from outreach signals (T8 v1.5)
    stage = contact.get("stage")
    if stage and str(stage).strip():
        # Apollo returned a stage — use it directly (normalize case)
        stage_val = str(stage).strip().title()
        props["Stage"] = {"select": {"name": stage_val}}
    else:
        # Apollo returned empty Stage — infer from signals
        # Never infer if contact is Customer or Churned (protect high-value stages)
        inferred = _infer_contact_stage(contact)
        if inferred and inferred not in ("Customer", "Churned"):
            props["Stage"] = {"select": {"name": inferred}}

    # NEW: Outreach Status
    outreach_status = contact.get("outreach_status")
    if outreach_status and str(outreach_status).strip():
        props["Outreach Status"] = {"select": {"name": str(outreach_status).strip().title()}}

    props["Record Source"] = {"select": {"name": "Apollo"}}
    props["Data Status"] = {"select": {"name": "Raw"}}

    # NEW: Engagement booleans — SAFE: only writes if Apollo actually returns the field
    # Does NOT write False for missing fields (prevents overwriting True with False)
    bool_fields = {
        "Email Sent": "email_sent",
        "Email Opened": "email_open",
        "Email Bounced": "email_bounced",
        "Replied": "replied",
        "Meeting Booked": "meeting_booked",
        "Demoed": "demoed",
        "Do Not Call": "do_not_call",
    }
    for notion_field, apollo_key in bool_fields.items():
        if apollo_key in contact and contact[apollo_key] is not None:
            props[notion_field] = {"checkbox": bool(contact[apollo_key])}

    # NEW: Intent Strength (from Apollo intent data)
    intent_strength = contact.get("intent_strength")
    if intent_strength and str(intent_strength).strip():
        props["Intent Strength"] = _rt(str(intent_strength).strip())

    # NEW: Job Change Event + Date
    job_change = contact.get("contact_job_change_event")
    if job_change and isinstance(job_change, dict):
        # Apollo returns job change as an object with details
        change_type = job_change.get("type", "")
        old_company = job_change.get("old_company_name", "")
        new_company = job_change.get("new_company_name", "")
        change_summary = f"{change_type}"
        if old_company:
            change_summary += f" | From: {old_company}"
        if new_company:
            change_summary += f" | To: {new_company}"
        props["Job Change Event"] = _rt(change_summary.strip())

        change_date = job_change.get("date") or job_change.get("changed_at")
        if change_date:
            props["Job Change Date"] = {"date": {"start": str(change_date)[:10]}}
    elif job_change and isinstance(job_change, str) and job_change.strip():
        props["Job Change Event"] = _rt(job_change.strip())

    # NEW: Last Contacted (date field)
    last_activity = contact.get("last_activity_date")
    if last_activity:
        props["Last Contacted"] = {"date": {"start": str(last_activity)[:10]}}

    # NEW: AI Decision (from Apollo AI typed_custom_fields)
    typed_fields = contact.get("typed_custom_fields") or {}
    ai_decision = typed_fields.get("6913a64c52c2780001146ce9")
    if ai_decision and isinstance(ai_decision, str) and ai_decision.strip():
        props["AI Decision"] = _rt(ai_decision.strip())

    # ── Qualification Status — derived from outreach signals (P1-1, v6.3) ────────
    # Nothing else writes this field; lead_score.py reads it for +15 pts.
    # Hierarchy: DNC/Bounced/Bad Data → Not Qualified
    #            Replied OR Meeting Booked → Qualified
    #            Active campaign(s) → In Progress
    #            (all other cases: do not write — leave field blank)
    _out_status = str(contact.get("outreach_status") or "").strip().lower()
    _is_replied = bool(contact.get("replied") or contact.get("contact_replied"))
    _is_booked  = bool(contact.get("meeting_booked"))
    _campaigns  = [c for c in (contact.get("emailer_campaign_ids") or []) if c]

    if _out_status in ("do not contact", "bounced", "bad data"):
        _qual_status = "Not Qualified"
    elif _is_replied or _is_booked:
        _qual_status = "Qualified"
    elif _campaigns:
        _qual_status = "In Progress"
    else:
        _qual_status = None

    if _qual_status:
        props["Qualification Status"] = {"select": {"name": _qual_status}}

    # Phone numbers
    for phone_obj in (contact.get("phone_numbers") or []):
        ptype = (phone_obj.get("type") or "").lower()
        number = phone_obj.get("sanitized_number")
        if not number:
            continue
        type_map = {
            "work_hq": "Corporate Phone",
            "work": "Work Direct Phone",
            "direct": "Work Direct Phone",
            "mobile": "Mobile Phone",
            "cell": "Mobile Phone",
            "home": "Home Phone",
        }
        prop_name = type_map.get(ptype, "Other Phone")
        if prop_name not in props:  # first occurrence only
            props[prop_name] = {"phone_number": number}

    # Contact Owner — mapped from Apollo owner_id to display name
    # Notion field is text type, so we write as rich_text
    owner_id = contact.get("owner_id")
    if owner_id:
        owner_name = APOLLO_OWNER_MAP.get(owner_id)
        if owner_name:
            props[FIELD_CONTACT_OWNER] = _rt(owner_name)
        else:
            # Unknown owner ID — write the raw ID so it's visible
            logger.warning(f"Unknown Apollo owner_id: {owner_id} — not in APOLLO_OWNER_MAP")
            props[FIELD_CONTACT_OWNER] = _rt(owner_id)

    # Company relation
    if company_page_id:
        props["Company"] = {"relation": [{"id": company_page_id}]}

    return props


# ─── Sync Logic ───────────────────────────────────────────────────────────────

def sync_companies(accounts: List[Dict], company_lookup: Dict, stats: SyncStats) -> Dict:
    """Sync companies to Notion. Returns updated company_lookup."""

    def process(account):
        aid = account.get("id", "")
        existing = company_lookup.get(f"aid:{aid}")
        props = format_company_from_api(account)

        try:
            if existing:
                update_page(existing, props)
                return "updated", aid, existing
            else:
                page_id = create_page(NOTION_DATABASE_ID_COMPANIES, props)
                return "created", aid, page_id
        except Exception as e:
            logger.error(f"Error syncing company {account.get('name', '?')}: {e}")
            return "error", aid, None

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(process, a): a for a in accounts}
        for i, fut in enumerate(as_completed(futures), 1):
            status, aid, page_id = fut.result()
            if status == "created":
                stats.notion_created_companies += 1
                if page_id:
                    company_lookup[f"aid:{aid}"] = page_id
            elif status == "updated":
                stats.notion_updated_companies += 1
            else:
                stats.failed_companies += 1
            if i % 100 == 0:
                logger.info(f"  Companies progress: {i}/{len(accounts)} (created: {stats.notion_created_companies}, updated: {stats.notion_updated_companies}, failed: {stats.failed_companies})")

    logger.info(f"Company sync done: {stats.notion_created_companies} created, {stats.notion_updated_companies} updated, {stats.failed_companies} failed")
    return company_lookup


def sync_contacts(contacts: List[Dict], company_lookup: Dict, contact_lookup: Dict, stats: SyncStats):
    """Sync contacts to Notion."""

    # Deduplicate
    seen = set()
    unique = []
    for c in contacts:
        cid = c.get("id", "")
        if cid and cid not in seen:
            seen.add(cid)
            unique.append(c)
        elif cid:
            stats.duplicates_prevented += 1

    logger.info(f"Contacts to sync: {len(unique)} unique (from {len(contacts)}, {len(contacts) - len(unique)} duplicates removed)")

    def process(contact):
        cid = contact.get("id", "")
        email = (contact.get("email") or "").lower()

        existing = contact_lookup.get(f"aid:{cid}")
        if not existing and email:
            existing = contact_lookup.get(f"email:{email}")

        # Find company
        aid = contact.get("account_id", "")
        company_page_id = company_lookup.get(f"aid:{aid}") if aid else None

        props = format_contact_from_api(contact, company_page_id)

        try:
            if existing:
                update_page(existing, props)
                return "updated", cid
            else:
                page_id = create_page(NOTION_DATABASE_ID_CONTACTS, props)
                if page_id:
                    contact_lookup[f"aid:{cid}"] = page_id
                    if email:
                        contact_lookup[f"email:{email}"] = page_id
                return "created", cid
        except Exception as e:
            logger.error(f"Error syncing contact {contact.get('name', '?')}: {e}")
            return "error", cid

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(process, c): c for c in unique}
        for i, fut in enumerate(as_completed(futures), 1):
            status, cid = fut.result()
            if status == "created":
                stats.notion_created_contacts += 1
            elif status == "updated":
                stats.notion_updated_contacts += 1
            else:
                stats.failed_contacts += 1
            if i % 100 == 0:
                logger.info(f"  Contacts progress: {i}/{len(unique)} (created: {stats.notion_created_contacts}, updated: {stats.notion_updated_contacts}, failed: {stats.failed_contacts})")

    logger.info(f"Contact sync done: {stats.notion_created_contacts} created, {stats.notion_updated_contacts} updated, {stats.failed_contacts} failed")


# ─── Company-Centric Post-Sync (v5.0) ──────────────────────────────────────
# After contact sync, compute company-level ownership, metrics, and stage.
# This is the core of the Company-Centric operating model.

def compute_company_ownership(
    contacts: List[Dict],
    company_lookup: Dict,
    accounts: Optional[List[Dict]] = None,
):
    """Derive Primary Company Owner + Supporting Owners.

    v5.1 Priority Logic:
    1. If the Apollo Account has `owner_id` → that owner wins directly.
       - Primary Company Owner = mapped Apollo owner
       - Supporting Owners     = empty (Apollo is authoritative)
       - Contact-based distribution is ignored for this company.
    2. Otherwise (owner_id missing / unmapped) → fall back to v5.0 logic:
       - Primary Owner = owner with most contacts (tie-break: most recent activity)
       - Supporting Owners = all other owners

    Writes: Primary Company Owner (select), Supporting Owners (text),
    Company Owners (text).
    """
    # ── Step 0: Build account_id → Apollo owner_id map from current accounts batch
    # Only accounts present in this sync run contribute. Companies not in the
    # batch will go through fallback logic (which is safe and preserves v5.0).
    account_owner_map: Dict[str, str] = {}
    if accounts:
        for a in accounts:
            aid = a.get("id")
            a_owner_id = a.get("owner_id")
            if aid and a_owner_id:
                account_owner_map[aid] = a_owner_id

    # ── Step 1: Build contact-based ownership data (used for fallback + union of companies)
    # { account_id: { owner_name: { count: N, last_activity: "YYYY-MM-DD" } } }
    company_data: Dict[str, Dict[str, Dict]] = {}

    for c in contacts:
        account_id = c.get("account_id")
        owner_id = c.get("owner_id")
        if not account_id or not owner_id:
            continue

        owner_name = APOLLO_OWNER_MAP.get(owner_id)
        if not owner_name:
            continue

        if account_id not in company_data:
            company_data[account_id] = {}

        if owner_name not in company_data[account_id]:
            company_data[account_id][owner_name] = {"count": 0, "last_activity": ""}

        company_data[account_id][owner_name]["count"] += 1

        # Track most recent activity date for tie-breaking
        last_activity = c.get("last_activity_date") or ""
        if last_activity > company_data[account_id][owner_name]["last_activity"]:
            company_data[account_id][owner_name]["last_activity"] = last_activity

    # ── Step 2: Union of candidate account_ids
    # (companies with Apollo owner OR with contacts-based data)
    candidate_account_ids = set(company_data.keys()) | set(account_owner_map.keys())

    if not candidate_account_ids:
        logger.info("  No company ownership data to compute")
        return

    # ── Step 3: Compute Primary + Supporting per company and write to Notion
    updated = 0
    skipped = 0
    apollo_wins = 0
    fallback_wins = 0
    apollo_unmapped = 0

    for account_id in candidate_account_ids:
        page_id = company_lookup.get(f"aid:{account_id}")
        if not page_id:
            skipped += 1
            continue

        primary_owner: Optional[str] = None
        supporting: List[str] = []
        all_owners_str: str = ""
        source: str = ""

        # Priority 1 — Apollo Account owner_id
        apollo_owner_id = account_owner_map.get(account_id)
        if apollo_owner_id:
            mapped = APOLLO_OWNER_MAP.get(apollo_owner_id)
            if mapped:
                primary_owner = mapped
                supporting = []  # Apollo is authoritative — no supporting owners
                all_owners_str = mapped
                source = "apollo"
                apollo_wins += 1
                logger.info(
                    f"[Ownership] Using Apollo owner for company {account_id} → {mapped}"
                )
            else:
                # Unknown Apollo owner_id → log and fall through to fallback logic
                apollo_unmapped += 1
                logger.warning(
                    f"[Ownership] Apollo owner_id '{apollo_owner_id}' not in "
                    f"APOLLO_OWNER_MAP for company {account_id} — falling back"
                )

        # Priority 2 — Fallback: contact-based ownership (v5.0 logic)
        if primary_owner is None:
            owners_info = company_data.get(account_id)
            if not owners_info:
                # No Apollo owner AND no contact-based owners → nothing to write
                skipped += 1
                continue

            sorted_owners = sorted(
                owners_info.items(),
                key=lambda x: (x[1]["count"], x[1]["last_activity"]),
                reverse=True,
            )
            primary_owner = sorted_owners[0][0]
            supporting = [name for name, _ in sorted_owners[1:]]
            all_owners_str = ", ".join(name for name, _ in sorted_owners)
            source = "fallback"
            fallback_wins += 1
            logger.info(
                f"[Ownership] Fallback to contact-based ownership for company {account_id} → {primary_owner}"
            )

        props = {
            FIELD_PRIMARY_COMPANY_OWNER: {"select": {"name": primary_owner}},
            FIELD_COMPANY_OWNERS: _rt(all_owners_str),
        }

        if supporting:
            props[FIELD_SUPPORTING_OWNERS] = _rt(", ".join(supporting))
        else:
            props[FIELD_SUPPORTING_OWNERS] = _rt("")

        try:
            update_page(page_id, props)
            updated += 1
        except Exception as e:
            logger.error(f"Error updating ownership for account {account_id}: {e}")

    logger.info(
        f"  Company Ownership computed: {updated} companies "
        f"(apollo={apollo_wins}, fallback={fallback_wins}, "
        f"unmapped_apollo={apollo_unmapped}, skipped={skipped})"
    )


def compute_company_metrics(contacts: List[Dict], company_lookup: Dict):
    """Compute company-level metrics from contacts.

    v5.0 — writes to Companies DB:
    - Active Contacts (count of non-archived qualified contacts)
    - Emailed Contacts (count with email sent)
    - Engaged Contacts (count that replied/opened/booked)
    - Last Engagement Date (max last_activity_date)
    - Sales OS Active (true if >= 1 active contact)
    """
    # Build metrics per company
    company_metrics: Dict[str, Dict] = {}

    for c in contacts:
        account_id = c.get("account_id")
        if not account_id:
            continue

        if account_id not in company_metrics:
            company_metrics[account_id] = {
                "active": 0,
                "emailed": 0,
                "engaged": 0,
                "last_date": "",
            }

        m = company_metrics[account_id]
        m["active"] += 1

        # Check email sent (we already filtered for this, so all contacts here have email sent)
        m["emailed"] += 1

        # Check engagement: replied, email_open, meeting_booked
        if any([
            c.get("replied"),
            c.get("email_open"),
            c.get("meeting_booked"),
        ]):
            m["engaged"] += 1

        # Track last activity
        last_activity = c.get("last_activity_date") or ""
        if last_activity and last_activity > m["last_date"]:
            m["last_date"] = last_activity

    if not company_metrics:
        logger.info("  No company metrics to compute")
        return

    updated = 0
    for account_id, m in company_metrics.items():
        page_id = company_lookup.get(f"aid:{account_id}")
        if not page_id:
            continue

        props = {
            FIELD_ACTIVE_CONTACTS: {"number": m["active"]},
            FIELD_EMAILED_CONTACTS: {"number": m["emailed"]},
            FIELD_ENGAGED_CONTACTS: {"number": m["engaged"]},
            FIELD_SALES_OS_ACTIVE: {"checkbox": m["active"] > 0},
        }

        if m["last_date"]:
            props[FIELD_LAST_ENGAGEMENT_DATE] = {"date": {"start": m["last_date"][:10]}}

        try:
            update_page(page_id, props)
            updated += 1
        except Exception as e:
            logger.error(f"Error updating metrics for account {account_id}: {e}")

    logger.info(f"  Company Metrics computed: {updated} companies")


def _preload_company_stages() -> Dict[str, str]:
    """
    Bulk-load current Company Stage for every company in Notion.

    Returns: { page_id: stage_name }

    Why: compute_company_stage() needs the current stage of each company to
    enforce the regression/terminal guard. Doing a per-company GET inside the
    loop causes N individual API calls (the classic N+1 problem) which — after
    a large full sync — triggers sustained 429 rate-limiting and turns a
    5-minute step into a multi-hour apparent hang.

    This single paginated scan replaces all of those individual GETs with one
    Notion DB query (~155 requests for 15k companies) and stores the result
    in memory for O(1) lookup in the loop.
    """
    stage_map: Dict[str, str] = {}
    has_more = True
    start_cursor: Optional[str] = None
    pages_scanned = 0
    t0 = time.time()

    logger.info("[Stage] Preloading current company stages from Notion ...")

    while has_more:
        body: Dict = {"page_size": 100}
        if start_cursor:
            body["start_cursor"] = start_cursor

        try:
            resp = notion_request(
                "POST",
                f"{NOTION_BASE_URL}/databases/{NOTION_DATABASE_ID_COMPANIES}/query",
                json=body,
            )
        except Exception as e:
            logger.warning(f"[Stage] Stage preload query failed: {e} — skipping preload, will treat all stages as empty")
            return stage_map

        data = resp.json()
        for page in data.get("results", []):
            if page.get("archived"):
                continue
            pid = page["id"]
            sel = page.get("properties", {}).get(FIELD_COMPANY_STAGE, {}).get("select")
            stage_map[pid] = sel.get("name", "") if sel else ""

        pages_scanned += len(data.get("results", []))
        has_more = data.get("has_more", False)
        start_cursor = data.get("next_cursor")

        if pages_scanned % 2000 == 0 and pages_scanned:
            logger.info(f"[Stage] Preload progress: {pages_scanned} companies scanned ...")

    elapsed = round(time.time() - t0, 1)
    logger.info(
        f"[Stage] Preload complete: {len(stage_map)} company stages loaded in {elapsed}s"
    )
    return stage_map


def compute_company_stage(contacts: List[Dict], company_lookup: Dict):
    """Derive Company Stage from contact-level signals.

    v5.2 (2026-04-12) — eliminated N+1 GET hang:
    - Preloads ALL current company stages in one bulk scan before the write loop.
    - Progress logged every 200 companies.
    - All guard logic (terminal / regression / no-op) unchanged.

    Stage derivation logic (v5.1):
    - Has contacts with Meeting Booked → "Meeting"
    - Has contacts with real intent (Replied OR Email Open Count >= 2 OR
      internal forwarding / repeated engagement) → "Engaged"
    - Has contacts with Email Sent → "Outreach"
    - Has contacts but none emailed → "Prospect"

    NOTE: Does NOT overwrite stages set by meeting_tracker or opportunity_manager
    (Meeting, Opportunity, Customer, Churned). Those are higher-priority stages.
    This function only sets: Prospect, Outreach, Engaged.
    """
    import time as _time
    from constants import has_real_intent as _has_real_intent
    from constants import is_stage_regression, STAGE_TERMINAL

    t0 = _time.time()

    # ── Phase 1: Build signal map from contacts (in-memory, fast) ───────────
    company_signals: Dict[str, Dict] = {}

    for c in contacts:
        account_id = c.get("account_id")
        if not account_id:
            continue

        if account_id not in company_signals:
            company_signals[account_id] = {
                "has_meeting": False,
                "has_intent": False,
                "intent_reasons": [],
                "has_email": False,
            }

        s = company_signals[account_id]

        if c.get("meeting_booked"):
            s["has_meeting"] = True

        intent_hit, reasons = _has_real_intent(c)
        if intent_hit:
            s["has_intent"] = True
            s["intent_reasons"].extend(reasons)

        s["has_email"] = True

    if not company_signals:
        logger.info("[Stage] No company signals found — skipping stage computation")
        return

    logger.info(
        f"[Stage] Signal map built: {len(company_signals)} companies have contact signals"
    )

    # ── Phase 2: Bulk-preload current stages (ONE paginated scan, not N GETs) ─
    current_stages: Dict[str, str] = _preload_company_stages()

    # ── Phase 3: Write loop — all guard checks use in-memory lookup ──────────
    updated = 0
    skipped_regression = 0
    skipped_terminal = 0
    skipped_noop = 0
    skipped_no_page = 0
    processed = 0

    logger.info(f"[Stage] Starting write loop for {len(company_signals)} candidates ...")

    for account_id, s in company_signals.items():
        processed += 1

        page_id = company_lookup.get(f"aid:{account_id}")
        if not page_id:
            skipped_no_page += 1
            continue

        # Determine new stage from signals
        if s["has_meeting"]:
            new_stage = COMPANY_STAGE_MEETING
        elif s["has_intent"]:
            new_stage = COMPANY_STAGE_ENGAGED
            reasons = list(dict.fromkeys(s["intent_reasons"]))
            logger.info(
                f"[Stage] {account_id} → Engaged "
                f"(intent signals: {', '.join(reasons)})"
            )
        elif s["has_email"]:
            new_stage = COMPANY_STAGE_OUTREACH
        else:
            new_stage = COMPANY_STAGE_PROSPECT

        # ── Conflict Guard — uses preloaded in-memory stage (no GET call) ──
        current_stage = current_stages.get(page_id, "")

        if current_stage in STAGE_TERMINAL:
            logger.info(
                f"[Conflict Guard] Skipping {account_id}: "
                f"stage '{current_stage}' is terminal"
            )
            skipped_terminal += 1
            continue

        if is_stage_regression(current_stage, new_stage):
            logger.info(
                f"[Conflict Guard] Regression blocked for {account_id}: "
                f"{current_stage} → {new_stage}"
            )
            skipped_regression += 1
            continue

        if current_stage == new_stage:
            skipped_noop += 1
            continue

        # ── Write ────────────────────────────────────────────────────────
        props = {FIELD_COMPANY_STAGE: {"select": {"name": new_stage}}}
        try:
            update_page(page_id, props)
            updated += 1
        except Exception as e:
            logger.error(f"[Stage] Error writing stage for {account_id}: {e}")

        # Progress heartbeat every 200 companies
        if processed % 200 == 0:
            elapsed = round(_time.time() - t0, 1)
            logger.info(
                f"[Stage] Progress: {processed}/{len(company_signals)} processed | "
                f"updated={updated} terminal={skipped_terminal} "
                f"regression={skipped_regression} noop={skipped_noop} | "
                f"elapsed={elapsed}s"
            )

    elapsed_total = round(_time.time() - t0, 1)
    logger.info(
        f"  Company Stage computed: {updated} updated, "
        f"{skipped_regression} regressions prevented, "
        f"{skipped_terminal} terminal stages preserved, "
        f"{skipped_noop} no-ops skipped, "
        f"{skipped_no_page} no page_id, "
        f"total elapsed={elapsed_total}s"
    )


# ─── Mode Runners ────────────────────────────────────────────────────────────

def run_incremental(since: datetime, stats: SyncStats, gate_mode: str = "off"):
    """
    Incremental mode: fetch records updated since `since` and sync to Notion.
    Designed for daily/hourly runs (GitHub Actions, cron).

    v4.0: Integrated Ingestion Gate between Apollo fetch and Notion write.
    """
    logger.info(f"MODE: INCREMENTAL — syncing changes since {since.strftime('%Y-%m-%d %H:%M')} UTC")
    logger.info(f"  Ingestion Gate: {gate_mode.upper()}")

    # Pre-load Notion data
    logger.info("Step 1: Pre-loading Notion data...")
    company_lookup = preload_companies()
    contact_lookup = preload_contacts()

    # Fetch from Apollo
    logger.info("Step 2: Fetching updated records from Apollo...")
    accounts = fetch_updated_accounts(since, stats)
    contacts = fetch_updated_contacts(since, stats)

    if not accounts and not contacts:
        logger.info("No updates found in Apollo. Done!")
        return

    # ── Ingestion Gate (v6.0) ────────────────────────────────────────
    if gate_mode != "off" and accounts:
        logger.info(f"Step 2.5: Running Ingestion Gate on {len(accounts)} companies...")
        gate_runner = IngestionGateRunner(mode=gate_mode)
        accounts, gate_results = gate_runner.gate_companies(accounts, contacts)
        logger.info(gate_runner.summary())

        # Save gate report for audit trail
        gate_runner.save_report(gate_results, "ingestion_gate_report.json")
    # ─────────────────────────────────────────────────────────────────

    # Sync companies first (contacts reference them)
    if accounts:
        logger.info(f"Step 3: Syncing {len(accounts)} companies to Notion...")
        company_lookup = sync_companies(accounts, company_lookup, stats)

    # Filter contacts: must have owner + email sent
    if contacts:
        contacts = filter_qualified_contacts(contacts, stats)

    # ── Contact Gate (v6.0) ──────────────────────────────────────────
    if gate_mode != "off" and contacts:
        logger.info(f"Step 3.5: Running Contact Gate on {len(contacts)} contacts...")
        gate_runner = IngestionGateRunner(mode=gate_mode)
        contacts, contact_gate_results = gate_runner.gate_contacts(contacts, company_lookup)
        logger.info(f"  Contact Gate: {len(contacts)} passed")
    # ─────────────────────────────────────────────────────────────────

    # Sync contacts
    if contacts:
        logger.info(f"Step 4: Syncing {len(contacts)} contacts to Notion...")
        sync_contacts(contacts, company_lookup, contact_lookup, stats)

        # Step 5-7: Company-Centric post-sync (v5.0)
        logger.info("Step 5: Computing Company Ownership (Primary + Supporting)...")
        compute_company_ownership(contacts, company_lookup, accounts=accounts)
        logger.info("Step 6: Computing Company Metrics...")
        compute_company_metrics(contacts, company_lookup)
        logger.info("Step 7: Computing Company Stage...")
        compute_company_stage(contacts, company_lookup)


def run_backfill(since: datetime, stats: SyncStats):
    """
    Backfill mode: same as incremental but designed for large historical ranges.
    Saves checkpoints so interrupted runs can be resumed.
    """
    logger.info(f"MODE: BACKFILL — syncing changes since {since.strftime('%Y-%m-%d %H:%M')} UTC")

    # Check for existing checkpoint
    checkpoint = load_checkpoint()
    if checkpoint:
        logger.info(f"Resuming from checkpoint: {checkpoint}")
        # If we completed companies, skip to contacts
        if checkpoint.get("companies_done"):
            logger.info("Companies already synced in previous run, skipping to contacts")

    # Pre-load Notion data
    logger.info("Step 1: Pre-loading Notion data...")
    company_lookup = preload_companies()
    contact_lookup = preload_contacts()

    # Fetch and sync companies
    if not (checkpoint and checkpoint.get("companies_done")):
        logger.info("Step 2: Fetching ALL updated accounts from Apollo...")
        accounts = fetch_updated_accounts(since, stats)

        if accounts:
            logger.info(f"Step 3: Syncing {len(accounts)} companies to Notion...")
            company_lookup = sync_companies(accounts, company_lookup, stats)

        # Save checkpoint: companies done
        save_checkpoint({
            "since": since.isoformat(),
            "companies_done": True,
            "companies_count": len(accounts) if accounts else 0,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
    else:
        logger.info("Step 2-3: Skipped (companies already synced)")

    # Fetch and sync contacts
    logger.info("Step 4: Fetching ALL updated contacts from Apollo...")
    contacts = fetch_updated_contacts(since, stats)

    # Filter contacts: must have owner + email sent
    if contacts:
        contacts = filter_qualified_contacts(contacts, stats)

    if contacts:
        logger.info(f"Step 5: Syncing {len(contacts)} contacts to Notion...")
        sync_contacts(contacts, company_lookup, contact_lookup, stats)

        # Step 6-8: Company-Centric post-sync (v5.0)
        logger.info("Step 6: Computing Company Ownership (Primary + Supporting)...")
        compute_company_ownership(contacts, company_lookup, accounts=accounts)
        logger.info("Step 7: Computing Company Metrics...")
        compute_company_metrics(contacts, company_lookup)
        logger.info("Step 8: Computing Company Stage...")
        compute_company_stage(contacts, company_lookup)

    # Clear checkpoint on success
    clear_checkpoint()


def run_full(stats: SyncStats):
    """
    Full mode: fetch ALL records from Apollo (no date filter) and sync everything.
    Uses alphabetical partitioning to bypass pagination limits.
    Complete rebuild of Notion data from Apollo.
    """
    logger.info("MODE: FULL — complete sync of ALL Apollo records to Notion")
    logger.info("WARNING: This will take a long time. Estimated: 2-4 hours for ~45k contacts + ~15k companies.")

    # Pre-load Notion data (for dedup / update-vs-create decisions)
    logger.info("Step 1: Pre-loading Notion data...")
    company_lookup = preload_companies()
    contact_lookup = preload_contacts()
    logger.info(f"  Notion index: {len(company_lookup)} company keys, {len(contact_lookup)} contact keys")

    # Fetch ALL accounts
    logger.info("Step 2: Fetching ALL accounts from Apollo (no date filter)...")
    accounts = fetch_all_accounts(stats)

    if accounts:
        logger.info(f"Step 3: Syncing {len(accounts)} companies to Notion...")
        company_lookup = sync_companies(accounts, company_lookup, stats)

    # Fetch ALL contacts
    logger.info("Step 4: Fetching ALL contacts from Apollo (no date filter)...")
    contacts = fetch_all_contacts(stats)

    # Filter contacts: must have owner + email sent
    if contacts:
        contacts = filter_qualified_contacts(contacts, stats)

    if contacts:
        logger.info(f"Step 5: Syncing {len(contacts)} contacts to Notion...")
        sync_contacts(contacts, company_lookup, contact_lookup, stats)

        # Step 6-8: Company-Centric post-sync (v5.0)
        logger.info("Step 6: Computing Company Ownership (Primary + Supporting)...")
        compute_company_ownership(contacts, company_lookup, accounts=accounts)
        logger.info("Step 7: Computing Company Metrics...")
        compute_company_metrics(contacts, company_lookup)
        logger.info("Step 8: Computing Company Stage...")
        compute_company_stage(contacts, company_lookup)


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Apollo → Notion Sync (v3.0 — Company-Centric)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Modes:
  incremental  Pull recently updated records (default: last 24h)
  backfill     Pull a wider historical range with checkpoint support
  full         Pull ALL records from Apollo (no date filter)

Examples:
  python daily_sync.py --mode incremental --days 7
  python daily_sync.py --mode backfill --days 365
  python daily_sync.py --mode full
  python daily_sync.py                          # defaults to incremental --hours 24
        """,
    )
    parser.add_argument(
        "--mode",
        choices=["incremental", "backfill", "full"],
        default="incremental",
        help="Sync mode (default: incremental)",
    )
    parser.add_argument("--hours", type=int, default=None, help="Sync records updated in the last N hours")
    parser.add_argument("--days", type=int, default=None, help="Sync records updated in the last N days")
    parser.add_argument(
        "--gate",
        choices=["strict", "review", "audit", "off"],
        default="off",
        help="Ingestion gate mode: strict=block, review=flag, audit=log only, off=disabled (default: off)",
    )
    args = parser.parse_args()

    # Validate args
    if args.mode == "full" and (args.hours or args.days):
        logger.warning("--hours/--days ignored in full mode (fetches everything)")

    if args.mode in ("incremental", "backfill"):
        if args.days:
            since = datetime.now(timezone.utc) - timedelta(days=args.days)
        elif args.hours:
            since = datetime.now(timezone.utc) - timedelta(hours=args.hours)
        else:
            since = datetime.now(timezone.utc) - timedelta(hours=24)

    if not APOLLO_API_KEY:
        logger.error("APOLLO_API_KEY not set")
        sys.exit(1)

    stats = SyncStats()
    stats.mode = args.mode
    stats.started_at = datetime.now(timezone.utc).isoformat()
    start_time = time.time()

    logger.info("=" * 80)
    if args.mode == "full":
        logger.info(f"APOLLO → NOTION SYNC v2.0 | Mode: FULL")
    else:
        logger.info(f"APOLLO → NOTION SYNC v2.0 | Mode: {args.mode.upper()} | Since: {since.strftime('%Y-%m-%d %H:%M')} UTC")
    logger.info("=" * 80)

    try:
        if args.mode == "incremental":
            run_incremental(since, stats, gate_mode=args.gate)
        elif args.mode == "backfill":
            run_backfill(since, stats)
        elif args.mode == "full":
            run_full(stats)
    except Exception as e:
        logger.error(f"Sync failed: {e}", exc_info=True)
        sys.exit(1)
    finally:
        elapsed = time.time() - start_time
        stats.duration_seconds = round(elapsed, 2)
        stats.completed_at = datetime.now(timezone.utc).isoformat()
        logger.info("=" * 80)
        logger.info(f"Sync finished in {elapsed/60:.1f} min")
        try:
            stats.save()
        except Exception as e:
            logger.warning(f"Could not write last_sync_stats.json: {e}")
        logger.info("=" * 80)


if __name__ == "__main__":
    main()