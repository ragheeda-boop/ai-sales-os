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

import os
import sys
import json
import logging
import argparse
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple
from collections import Counter

sys.path.insert(0, os.path.dirname(__file__))
from notion_helpers import (
    NOTION_DATABASE_ID_CONTACTS,
    NOTION_DATABASE_ID_COMPANIES,
    notion_request,
    update_page,
    NOTION_BASE_URL,
)
from constants import (
    FIELD_COMPANY_STAGE, FIELD_CONTACT_OWNER, FIELD_PRIMARY_COMPANY_OWNER,
    FIELD_SALES_OS_ACTIVE, FIELD_ARCHIVE_REASON, FIELD_ACTIVE_IN_SALES_OS,
    FIELD_STAGE, FIELD_EMAIL_SENT, FIELD_REPLIED, FIELD_EMAIL_OPENED,
    FIELD_MEETING_BOOKED, FIELD_LEAD_SCORE, FIELD_ACTION_READY,
    COMPANY_STAGE_ARCHIVED, COMPANY_STAGE_PROSPECT,
    ARCHIVE_REASON_NO_OWNER, ARCHIVE_REASON_NO_EMAIL,
    ARCHIVE_REASON_NO_OUTREACH, ARCHIVE_REASON_GATE_FAIL,
    ARCHIVE_REASON_NO_COMPANY,
    OUTREACH_BLOCKED, SOFT_DELETE_DAYS,
    ICP_INDUSTRIES, ICP_COUNTRIES, ICP_MIN_EMPLOYEES,
    SENIOR_SENIORITIES, APOLLO_OWNER_MAP,
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
            "contacts_audited": 0,
            "contacts_healthy": 0,
            "contacts_archived": 0,
            "contacts_no_company": 0,
            "contacts_no_owner": 0,
            "contacts_no_email": 0,
            "contacts_no_outreach": 0,
            "orphan_contacts_found": 0,
            "unowned_companies_found": 0,
            "links_fixed": 0,
            "already_archived": 0,
        }
        self.actions_log: List[Dict] = []

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
            "",
            f"  Contacts: {self.stats['contacts_audited']} audited",
            f"    ✅ Healthy:     {self.stats['contacts_healthy']}",
            f"    📦 To Archive:  {self.stats['contacts_archived']}",
            f"    Issues Found:",
            f"      • No Company:   {self.stats['contacts_no_company']} (orphans)",
            f"      • No Owner:     {self.stats['contacts_no_owner']}",
            f"      • No Email:     {self.stats['contacts_no_email']}",
            f"      • No Outreach:  {self.stats['contacts_no_outreach']}",
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
