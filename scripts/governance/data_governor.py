#!/usr/bin/env python3
"""
AI Sales OS — Data Governor (v6.0)

Enforces data governance rules on EXISTING Notion data:
1. Audit existing companies/contacts against ingestion gates
2. Archive records that fail the gate (Hybrid approach)
3. Enforce Company-Contact linking (no orphans)
4. Enforce Owner assignment (no unowned companies)
5. Generate data quality report
6. Soft-delete with protection (no hard deletes on active records)

Usage:
    python data_governor.py --dry-run                    # Audit only, no changes
    python data_governor.py --enforce                    # Apply archival + enforcement
    python data_governor.py --report                     # Generate detailed report
    python data_governor.py --enforce --limit 100        # Limit to first N records
"""

import sys as _sys, os as _os; _sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
import os
import sys
import json
import logging
import argparse
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple
from collections import Counter

sys.path.insert(0, os.path.dirname(__file__))
from core.notion_helpers import (
    NOTION_DATABASE_ID_CONTACTS,
    NOTION_DATABASE_ID_COMPANIES,
    notion_request,
    update_page,
    NOTION_BASE_URL,
)
from core.constants import (
    FIELD_COMPANY_STAGE, FIELD_CONTACT_OWNER, FIELD_PRIMARY_COMPANY_OWNER,
    FIELD_SALES_OS_ACTIVE, FIELD_ARCHIVE_REASON, FIELD_ACTIVE_IN_SALES_OS,
    FIELD_STAGE, FIELD_EMAIL_SENT, FIELD_REPLIED, FIELD_EMAIL_OPENED,
    FIELD_MEETING_BOOKED, FIELD_LEAD_SCORE, FIELD_ACTION_READY,
    FIELD_EMAIL_OPEN_COUNT, FIELD_ENGAGED_CONTACTS,
    FIELD_INTERNAL_FORWARD_DETECTED, FIELD_REPEATED_ENGAGEMENT_DETECTED,
    COMPANY_STAGE_ARCHIVED, COMPANY_STAGE_PROSPECT,
    ARCHIVE_REASON_NO_OWNER, ARCHIVE_REASON_NO_EMAIL,
    ARCHIVE_REASON_NO_OUTREACH, ARCHIVE_REASON_GATE_FAIL,
    ARCHIVE_REASON_NO_COMPANY,
    OUTREACH_BLOCKED, SOFT_DELETE_DAYS,
    ICP_INDUSTRIES, ICP_COUNTRIES, ICP_MIN_EMPLOYEES,
    SENIOR_SENIORITIES, APOLLO_OWNER_MAP,
    has_real_intent,
    check_pipeline_freshness, FRESHNESS_MAX_AGE_HOURS,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("data_governor.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


# ─── Helper: Read Notion property values ────────────────────────────────────

def _get_text(props: Dict, field: str) -> str:
    """Extract text value from Notion property."""
    prop = props.get(field, {})
    prop_type = prop.get("type", "")

    if prop_type == "rich_text":
        items = prop.get("rich_text", [])
        return items[0].get("plain_text", "").strip() if items else ""
    elif prop_type == "title":
        items = prop.get("title", [])
        return items[0].get("plain_text", "").strip() if items else ""
    elif prop_type == "select":
        sel = prop.get("select")
        return sel.get("name", "") if sel else ""
    elif prop_type == "email":
        return (prop.get("email") or "").strip()
    elif prop_type == "number":
        return str(prop.get("number", ""))
    return ""


def _get_bool(props: Dict, field: str) -> bool:
    """Extract boolean from Notion property."""
    prop = props.get(field, {})
    return prop.get("checkbox", False)


def _get_number(props: Dict, field: str) -> Optional[float]:
    """Extract number from Notion property."""
    prop = props.get(field, {})
    return prop.get("number")


def _get_relation(props: Dict, field: str) -> List[str]:
    """Extract relation page IDs."""
    prop = props.get(field, {})
    return [r.get("id", "") for r in prop.get("relation", [])]


# ─── Data Governor ──────────────────────────────────────────────────────────

class DataGovernor:
    """Enforce governance rules on existing Notion data."""

    def __init__(self, dry_run: bool = True, limit: int = 0):
        self.dry_run = dry_run
        self.limit = limit
        self.stats = {
            "companies_audited": 0,
            "companies_healthy": 0,
            "companies_archived": 0,
            "companies_no_owner": 0,
            "companies_no_contacts": 0,
            "companies_no_activity": 0,
            "companies_saved_by_intent": 0,   # archive guard hits
            "contacts_audited": 0,
            "contacts_healthy": 0,
            "contacts_archived": 0,
            "contacts_no_company": 0,
            "contacts_no_owner": 0,
            "contacts_no_email": 0,
            "contacts_no_outreach": 0,
            "contacts_saved_by_intent": 0,
            "orphan_contacts_found": 0,
            "unowned_companies_found": 0,
            "links_fixed": 0,
            "already_archived": 0,
        }
        self.actions_log: List[Dict] = []
        # Per-company intent cache, keyed by Company page ID.
        # Populated during run() before auditing companies/contacts.
        self._company_intent: Dict[str, Dict] = {}

    # ── Load all companies ──────────────────────────────────────────────

    def _load_all_companies(self) -> List[Dict]:
        """Load all companies from Notion with full properties."""
        companies = []
        has_more = True
        start_cursor = None
        count = 0

        logger.info("Loading all companies from Notion...")

        while has_more:
            body = {"page_size": 100}
            if start_cursor:
                body["start_cursor"] = start_cursor

            resp = notion_request(
                "POST",
                f"{NOTION_BASE_URL}/databases/{NOTION_DATABASE_ID_COMPANIES}/query",
                json=body,
            )
            data = resp.json()

            for page in data.get("results", []):
                companies.append(page)
                count += 1
                if self.limit and count >= self.limit:
                    has_more = False
                    break

            if not self.limit or count < self.limit:
                has_more = data.get("has_more", False)
                start_cursor = data.get("next_cursor")

        logger.info(f"Loaded {len(companies)} companies")
        return companies

    # ── Load all contacts ───────────────────────────────────────────────

    def _load_all_contacts(self) -> List[Dict]:
        """Load all contacts from Notion with full properties."""
        contacts = []
        has_more = True
        start_cursor = None
        count = 0

        logger.info("Loading all contacts from Notion...")

        while has_more:
            body = {"page_size": 100}
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
                count += 1
                if self.limit and count >= self.limit:
                    has_more = False
                    break

            if not self.limit or count < self.limit:
                has_more = data.get("has_more", False)
                start_cursor = data.get("next_cursor")

        logger.info(f"Loaded {len(contacts)} contacts")
        return contacts

    # ── Intent Signal Extraction (v6.1 — 2026-04-11) ────────────────────

    def _contact_page_to_intent_record(self, page: Dict) -> Dict:
        """Flatten a Notion contact page into the dict shape expected by
        core.constants.has_real_intent(). Only pulls the fields relevant to
        intent detection — cheap and side-effect free."""
        props = page.get("properties", {})
        return {
            "replied": _get_bool(props, FIELD_REPLIED),
            "meeting_booked": _get_bool(props, FIELD_MEETING_BOOKED),
            "email_open_count": _get_number(props, FIELD_EMAIL_OPEN_COUNT) or 0,
            "internal_forward_detected": _get_bool(props, FIELD_INTERNAL_FORWARD_DETECTED),
            "repeated_engagement_detected": _get_bool(props, FIELD_REPEATED_ENGAGEMENT_DETECTED),
        }

    def _build_company_intent_map(self, contacts: List[Dict]) -> Dict[str, Dict]:
        """Aggregate contact-level intent signals into per-company records.

        Returns a dict keyed by Company page ID with:
            {
              "has_intent": bool,
              "reasons": [str, ...],
              "contact_count_intent": int,
            }
        """
        intent_map: Dict[str, Dict] = {}

        for page in contacts:
            props = page.get("properties", {})
            company_ids = _get_relation(props, "Company")
            if not company_ids:
                continue

            record = self._contact_page_to_intent_record(page)
            hit, reasons = has_real_intent(record)
            if not hit:
                continue

            for cid in company_ids:
                entry = intent_map.setdefault(
                    cid,
                    {"has_intent": True, "reasons": [], "contact_count_intent": 0},
                )
                entry["contact_count_intent"] += 1
                entry["reasons"].extend(reasons)

        # De-dup reasons per company for readability
        for cid, entry in intent_map.items():
            seen = set()
            entry["reasons"] = [
                r for r in entry["reasons"] if not (r in seen or seen.add(r))
            ]
        return intent_map

    def _company_has_intent(self, page_id: str, page: Dict) -> Tuple[bool, List[str]]:
        """Return (True, reasons) if the company has real intent via either:
          (a) the contact-aggregated map built from Notion, or
          (b) company-level properties (Engaged Contacts > 0 or explicit flags).
        """
        # Contact-derived
        agg = self._company_intent.get(page_id)
        if agg and agg.get("has_intent"):
            return True, list(agg.get("reasons", []))

        # Company-level fallback signals
        props = page.get("properties", {})
        reasons: List[str] = []

        engaged = _get_number(props, FIELD_ENGAGED_CONTACTS) or 0
        if engaged and engaged > 0:
            reasons.append(f"engaged_contacts={int(engaged)}")

        if _get_bool(props, FIELD_INTERNAL_FORWARD_DETECTED):
            reasons.append("internal_forward")
        if _get_bool(props, FIELD_REPEATED_ENGAGEMENT_DETECTED):
            reasons.append("repeated_engagement")

        return (len(reasons) > 0), reasons

    # ── Audit Company ───────────────────────────────────────────────────

    def _audit_company(self, page: Dict, contact_count: int) -> Dict:
        """Audit a single company. Returns action dict."""
        page_id = page["id"]
        props = page.get("properties", {})

        name = _get_text(props, "Company Name")
        stage = _get_text(props, FIELD_COMPANY_STAGE)
        owner = _get_text(props, FIELD_PRIMARY_COMPANY_OWNER)
        sales_active = _get_bool(props, FIELD_SALES_OS_ACTIVE)
        apollo_id = _get_text(props, "Apollo Account Id")

        # Skip already archived
        if stage == COMPANY_STAGE_ARCHIVED:
            self.stats["already_archived"] += 1
            return {"action": "skip", "reason": "already_archived"}

        issues = []

        # Check 1: Has owner?
        if not owner:
            issues.append("no_owner")
            self.stats["companies_no_owner"] += 1

        # Check 2: Has contacts?
        if contact_count == 0:
            issues.append("no_contacts")
            self.stats["companies_no_contacts"] += 1

        # Check 3: Has any activity? (Email sent, replied, meeting)
        # We check this via contact_count (qualified contacts = contacts with outreach)
        if contact_count == 0 and not sales_active:
            issues.append("no_activity")
            self.stats["companies_no_activity"] += 1

        if issues:
            # ── Archive Guard (2026-04-11) ──────────────────────────────
            # Real intent wins over weak gate failures: if the company has
            # replies, meetings, repeated opens, or internal forwarding,
            # we NEVER archive it for "no_activity" / "no_owner" alone.
            # Owner gaps on intent-positive accounts should be fixed by
            # assigning an owner, not by archival.
            intent_hit, intent_reasons = self._company_has_intent(page_id, page)
            if intent_hit:
                self.stats["companies_saved_by_intent"] += 1
                logger.info(
                    f"[Archive Guard] Company {name} skipped from archival "
                    f"due to real intent signal ({', '.join(intent_reasons)}); "
                    f"original issues: {', '.join(issues)}"
                )
                # Undo the per-issue counters we bumped above to keep stats honest
                for iss, key in (
                    ("no_owner", "companies_no_owner"),
                    ("no_contacts", "companies_no_contacts"),
                    ("no_activity", "companies_no_activity"),
                ):
                    if iss in issues and self.stats[key] > 0:
                        self.stats[key] -= 1
                self.stats["companies_healthy"] += 1
                return {"action": "healthy", "guarded_by_intent": True}

            # Determine archive reason (worst issue)
            if "no_owner" in issues:
                archive_reason = ARCHIVE_REASON_NO_OWNER
            elif "no_contacts" in issues:
                archive_reason = "No Contacts"
            else:
                archive_reason = "No Activity"

            return {
                "action": "archive",
                "page_id": page_id,
                "name": name,
                "issues": issues,
                "archive_reason": archive_reason,
            }

        self.stats["companies_healthy"] += 1
        return {"action": "healthy"}

    # ── Audit Contact ───────────────────────────────────────────────────

    def _audit_contact(self, page: Dict) -> Dict:
        """Audit a single contact. Returns action dict."""
        page_id = page["id"]
        props = page.get("properties", {})

        name = _get_text(props, "Full Name")
        email = _get_text(props, "Email")
        owner = _get_text(props, FIELD_CONTACT_OWNER)
        stage = _get_text(props, FIELD_STAGE)
        email_sent = _get_bool(props, FIELD_EMAIL_SENT)
        company_ids = _get_relation(props, "Company")
        outreach_status = _get_text(props, "Outreach Status")

        # Skip already archived
        if stage and stage.lower() == "archived":
            self.stats["already_archived"] += 1
            return {"action": "skip", "reason": "already_archived"}

        issues = []

        # Check 1: Has company link?
        if not company_ids:
            issues.append("no_company")
            self.stats["contacts_no_company"] += 1
            self.stats["orphan_contacts_found"] += 1

        # Check 2: Has owner?
        if not owner:
            issues.append("no_owner")
            self.stats["contacts_no_owner"] += 1

        # Check 3: Has email?
        if not email:
            issues.append("no_email")
            self.stats["contacts_no_email"] += 1

        # Check 4: Has outreach?
        if not email_sent and outreach_status not in {"In Sequence", "Sent", "Opened", "Replied", "Meeting Booked"}:
            issues.append("no_outreach")
            self.stats["contacts_no_outreach"] += 1

        if issues:
            # ── Contact Archive Guard (2026-04-11) ──────────────────────
            # If the contact itself shows real intent (replied, meeting,
            # repeated opens, internal forward), we never archive them for
            # "no_outreach". Hard failures (no_company / no_email) still
            # archive because they break primary-key / linkage invariants.
            record = self._contact_page_to_intent_record(page)
            intent_hit, intent_reasons = has_real_intent(record)
            hard_failures = {"no_company", "no_email"}
            only_soft = not (set(issues) & hard_failures)
            if intent_hit and only_soft:
                self.stats["contacts_saved_by_intent"] += 1
                logger.info(
                    f"[Archive Guard] Contact {name} skipped from archival "
                    f"due to real intent ({', '.join(intent_reasons)}); "
                    f"original issues: {', '.join(issues)}"
                )
                for iss, key in (
                    ("no_owner", "contacts_no_owner"),
                    ("no_outreach", "contacts_no_outreach"),
                ):
                    if iss in issues and self.stats[key] > 0:
                        self.stats[key] -= 1
                self.stats["contacts_healthy"] += 1
                return {"action": "healthy", "guarded_by_intent": True}

            if "no_company" in issues:
                archive_reason = ARCHIVE_REASON_NO_COMPANY
            elif "no_owner" in issues:
                archive_reason = ARCHIVE_REASON_NO_OWNER
            elif "no_email" in issues:
                archive_reason = ARCHIVE_REASON_NO_EMAIL
            else:
                archive_reason = ARCHIVE_REASON_NO_OUTREACH

            return {
                "action": "archive",
                "page_id": page_id,
                "name": name,
                "issues": issues,
                "archive_reason": archive_reason,
            }

        self.stats["contacts_healthy"] += 1
        return {"action": "healthy"}

    # ── Execute Archival ────────────────────────────────────────────────

    def _archive_company(self, page_id: str, reason: str):
        """Set company stage to Archived with reason."""
        if self.dry_run:
            return
        try:
            props = {
                FIELD_COMPANY_STAGE: {"select": {"name": COMPANY_STAGE_ARCHIVED}},
                FIELD_SALES_OS_ACTIVE: {"checkbox": False},
            }
            update_page(page_id, props)
        except Exception as e:
            logger.error(f"Failed to archive company {page_id}: {e}")

    def _archive_contact(self, page_id: str, reason: str):
        """Set contact stage to Archived with reason."""
        if self.dry_run:
            return
        try:
            props = {
                FIELD_STAGE: {"select": {"name": "Archived"}},
                FIELD_ACTION_READY: {"checkbox": False},
            }
            update_page(page_id, props)
        except Exception as e:
            logger.error(f"Failed to archive contact {page_id}: {e}")

    # ── Main Run ────────────────────────────────────────────────────────

    def run(self):
        """Run full governance audit and enforcement."""
        mode_str = "DRY RUN (no changes)" if self.dry_run else "ENFORCE (will archive)"
        logger.info(f"🏛️  Data Governor starting — Mode: {mode_str}")
        logger.info("")

        # Step 0: Pipeline freshness guard
        # If upstream signal scripts (analytics_tracker, outcome_tracker,
        # meeting_tracker) haven't run within FRESHNESS_MAX_AGE_HOURS, the
        # engagement data the governor reads is stale. Archiving on stale
        # signals can wrongly delete companies that actually have real intent.
        # Policy: if stale AND enforce mode, downgrade to dry-run.
        try:
            scripts_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            freshness = check_pipeline_freshness(base_dir=scripts_dir)
        except Exception as e:
            logger.warning(f"[Timing Guard] Freshness check failed: {e}")
            freshness = {"fresh": False, "checked": [], "oldest_age_hours": None,
                         "max_age_hours": FRESHNESS_MAX_AGE_HOURS}

        if not freshness.get("fresh", False):
            oldest = freshness.get("oldest_age_hours")
            oldest_str = f"{oldest:.1f}h" if isinstance(oldest, (int, float)) else "unknown"
            logger.warning(
                f"[Timing Guard] Pipeline signal data is STALE "
                f"(oldest stats file age: {oldest_str}, max allowed: "
                f"{FRESHNESS_MAX_AGE_HOURS}h)."
            )
            if not self.dry_run:
                logger.warning(
                    "[Timing Guard] Downgrading to DRY-RUN. Archival is "
                    "suppressed because upstream analytics/outcome/meeting "
                    "stats are stale or missing. Refusing to archive on "
                    "possibly-stale engagement data."
                )
                self.dry_run = True
                self._forced_dry_run_reason = "stale_pipeline"
        else:
            logger.info(
                f"[Timing Guard] Pipeline freshness OK "
                f"(checked {len(freshness.get('checked', []))} stats files)."
            )

        # Step 1: Load all data
        companies = self._load_all_companies()
        contacts = self._load_all_contacts()

        # Step 2: Build company → contact count map
        company_contact_counts: Counter = Counter()
        for page in contacts:
            props = page.get("properties", {})
            company_ids = _get_relation(props, "Company")
            for cid in company_ids:
                company_contact_counts[cid] += 1

        # Step 2b: Build per-company real-intent aggregation (archive guard)
        self._company_intent = self._build_company_intent_map(contacts)
        logger.info(
            f"  Intent aggregation: {len(self._company_intent)} companies "
            f"have at least one intent-positive contact"
        )

        # Step 3: Audit companies
        logger.info(f"\n📊 Auditing {len(companies)} companies...")
        for page in companies:
            self.stats["companies_audited"] += 1
            page_id = page["id"]
            contact_count = company_contact_counts.get(page_id, 0)

            result = self._audit_company(page, contact_count)

            if result["action"] == "archive":
                self.stats["companies_archived"] += 1
                name = result.get("name", "?")
                reason = result.get("archive_reason", "?")
                issues = result.get("issues", [])
                logger.info(f"  📦 Archive company: {name} — reason: {reason} (issues: {', '.join(issues)})")

                self._archive_company(page_id, reason)
                self.actions_log.append({
                    "type": "archive_company",
                    "page_id": page_id,
                    "name": name,
                    "reason": reason,
                    "issues": issues,
                })

        # Step 4: Audit contacts
        logger.info(f"\n📊 Auditing {len(contacts)} contacts...")
        for page in contacts:
            self.stats["contacts_audited"] += 1
            result = self._audit_contact(page)

            if result["action"] == "archive":
                self.stats["contacts_archived"] += 1
                name = result.get("name", "?")
                reason = result.get("archive_reason", "?")
                issues = result.get("issues", [])

                if self.stats["contacts_archived"] <= 20:  # Limit log spam
                    logger.info(f"  📦 Archive contact: {name} — reason: {reason}")

                self._archive_contact(result["page_id"], reason)
                self.actions_log.append({
                    "type": "archive_contact",
                    "page_id": result["page_id"],
                    "name": name,
                    "reason": reason,
                    "issues": issues,
                })

        # Step 5: Summary
        logger.info("")
        logger.info(self.summary())

    def summary(self) -> str:
        """Generate governance summary."""
        lines = [
            "═══ DATA GOVERNOR SUMMARY ═════════════════════════════════",
            f"  Mode: {'DRY RUN' if self.dry_run else 'ENFORCE'}",
            "",
            f"  Companies: {self.stats['companies_audited']} audited",
            f"    ✅ Healthy:     {self.stats['companies_healthy']}",
            f"    📦 To Archive:  {self.stats['companies_archived']}",
            f"    ⏭️  Already Archived: (included in total)",
            f"    Issues Found:",
            f"      • No Owner:     {self.stats['companies_no_owner']}",
            f"      • No Contacts:  {self.stats['companies_no_contacts']}",
            f"      • No Activity:  {self.stats['companies_no_activity']}",
            f"    🛡️  Saved by Intent Guard: {self.stats['companies_saved_by_intent']}",
            "",
            f"  Contacts: {self.stats['contacts_audited']} audited",
            f"    ✅ Healthy:     {self.stats['contacts_healthy']}",
            f"    📦 To Archive:  {self.stats['contacts_archived']}",
            f"    Issues Found:",
            f"      • No Company:   {self.stats['contacts_no_company']} (orphans)",
            f"      • No Owner:     {self.stats['contacts_no_owner']}",
            f"      • No Email:     {self.stats['contacts_no_email']}",
            f"      • No Outreach:  {self.stats['contacts_no_outreach']}",
            f"    🛡️  Saved by Intent Guard: {self.stats['contacts_saved_by_intent']}",
            "",
            f"  Data Quality Score: {self._quality_score():.0%}",
            "═══════════════════════════════════════════════════════════",
        ]
        return "\n".join(lines)

    def _quality_score(self) -> float:
        """Calculate overall data quality score."""
        total = self.stats["companies_audited"] + self.stats["contacts_audited"]
        healthy = self.stats["companies_healthy"] + self.stats["contacts_healthy"]
        return healthy / max(total, 1)

    def save_report(self, filepath: str = "data_governor_report.json"):
        """Save detailed report."""
        report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "dry_run": self.dry_run,
            "stats": self.stats,
            "actions": self.actions_log[:500],  # Cap at 500 actions
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        logger.info(f"Report saved to {filepath}")


# ─── CLI ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="AI Sales OS — Data Governor")
    parser.add_argument("--dry-run", action="store_true", default=True,
                        help="Audit only, no changes (default)")
    parser.add_argument("--enforce", action="store_true",
                        help="Apply archival and enforcement")
    parser.add_argument("--report", action="store_true",
                        help="Save detailed report to JSON")
    parser.add_argument("--limit", type=int, default=0,
                        help="Limit records to audit (0 = all)")
    args = parser.parse_args()

    dry_run = not args.enforce

    governor = DataGovernor(dry_run=dry_run, limit=args.limit)
    governor.run()

    if args.report:
        governor.save_report()


if __name__ == "__main__":
    main()
