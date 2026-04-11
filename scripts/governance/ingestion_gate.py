#!/usr/bin/env python3
"""
AI Sales OS — Ingestion Gate (v6.0)

Controlled data ingestion: NO company or contact enters the system without
passing a justified ingestion gate.

Company Gate (must pass >= 2 of 5 criteria):
  1. ICP Match (industry + country + size)
  2. Has Senior Contact (C-Suite/VP/Director)
  3. Has Intent Signal (email open/reply/meeting)
  4. Has Trigger Event (funding/headcount growth/hiring)
  5. Has been contacted (email sent / meeting / call)

Contact Gate (must pass ALL):
  1. Linked to a company in the system
  2. Has valid email
  3. Has clear role (Decision Maker / Influencer / End User)
  4. Has an owner assigned

Usage:
    # Gate companies before sync
    from governance.ingestion_gate import CompanyGate, ContactGate

    gate = CompanyGate()
    result = gate.evaluate(apollo_account, contacts_at_company)
    if result.passed:
        # sync to Notion

    # Gate contacts
    cgate = ContactGate(company_lookup)
    result = cgate.evaluate(apollo_contact)
    if result.passed:
        # sync to Notion

CLI:
    python ingestion_gate.py --dry-run          # Audit mode: show what would pass/fail
    python ingestion_gate.py --mode strict      # Block non-qualifying records
    python ingestion_gate.py --report           # Generate gate report
"""

import sys as _sys, os as _os; _sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
import os
import sys
import json
import logging
import argparse
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

sys.path.insert(0, os.path.dirname(__file__))
from core.constants import (
    # ICP
    ICP_INDUSTRIES, ICP_COUNTRIES, ICP_MIN_EMPLOYEES,
    # Seniority / Roles
    SENIOR_SENIORITIES, SENIOR_TITLE_KEYWORDS,
    ROLE_DECISION_MAKER_KEYWORDS, ROLE_INFLUENCER_KEYWORDS,
    SENIORITY_NORMALIZE,
    # Engagement / Triggers
    ENGAGEMENT_SIGNALS, TRIGGER_HEADCOUNT_GROWTH_THRESHOLD,
    TRIGGER_FUNDING_RECENCY_DAYS,
    # Real Intent (2026-04-11)
    has_real_intent, company_has_real_intent,
    # Gate config
    COMPANY_GATE_MIN_SCORE, COMPANY_KEY_FIELDS, MIN_DATA_COMPLETENESS,
    # Contact
    CONTACT_REQUIRED_FIELDS,
    # Archive reasons
    ARCHIVE_REASON_GATE_FAIL, ARCHIVE_REASON_NO_COMPANY,
    ARCHIVE_REASON_NO_OWNER, ARCHIVE_REASON_NO_EMAIL,
    # Modes
    GOVERNANCE_MODE_STRICT, GOVERNANCE_MODE_REVIEW, GOVERNANCE_MODE_AUDIT,
    # Owner
    APOLLO_OWNER_MAP, CAMPAIGN_FAILED_STATUSES,
    # Outreach
    OUTREACH_BLOCKED,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("ingestion_gate.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


# ─── Gate Result Data Classes ───────────────────────────────────────────────

@dataclass
class GateCriterion:
    """A single gate criterion evaluation."""
    name: str
    passed: bool
    detail: str = ""
    weight: float = 1.0


@dataclass
class GateResult:
    """Result of a gate evaluation."""
    entity_id: str
    entity_name: str
    entity_type: str  # "company" or "contact"
    passed: bool
    score: int  # Number of criteria passed
    min_score: int  # Minimum required
    criteria: List[GateCriterion] = field(default_factory=list)
    reject_reason: str = ""
    classification: str = ""  # "Qualified" / "Review" / "Rejected"

    def summary(self) -> str:
        status = "✅ PASS" if self.passed else "❌ FAIL"
        criteria_str = " | ".join(
            f"{'✓' if c.passed else '✗'} {c.name}"
            for c in self.criteria
        )
        return (
            f"{status} [{self.entity_type.upper()}] {self.entity_name} "
            f"(score: {self.score}/{self.min_score} min) — {criteria_str}"
        )


# ─── Company Gate ───────────────────────────────────────────────────────────

class CompanyGate:
    """
    Evaluate whether a company should be ingested into the system.

    Must pass at least COMPANY_GATE_MIN_SCORE (default: 2) of 5 criteria:
    1. ICP Match (industry + country + size)
    2. Has Senior Contact
    3. Has Intent/Engagement Signal
    4. Has Trigger Event (funding, growth, hiring)
    5. Has been contacted (outreach activity)
    """

    def __init__(self, mode: str = GOVERNANCE_MODE_STRICT):
        self.mode = mode
        self.min_score = COMPANY_GATE_MIN_SCORE

    def evaluate(
        self,
        account: Dict,
        contacts_at_company: Optional[List[Dict]] = None,
    ) -> GateResult:
        """Evaluate a company against all gate criteria."""
        contacts_at_company = contacts_at_company or []
        account_id = account.get("id", "unknown")
        account_name = account.get("name", "Unknown Company")

        criteria = []

        # ── Criterion 1: ICP Match ──────────────────────────────────────
        icp_result = self._check_icp(account)
        criteria.append(icp_result)

        # ── Criterion 2: Has Senior Contact ─────────────────────────────
        senior_result = self._check_senior_contact(contacts_at_company)
        criteria.append(senior_result)

        # ── Criterion 3: Has Engagement Signal ──────────────────────────
        engagement_result = self._check_engagement(contacts_at_company)
        criteria.append(engagement_result)

        # ── Criterion 4: Has Trigger Event ──────────────────────────────
        trigger_result = self._check_trigger_events(account)
        criteria.append(trigger_result)

        # ── Criterion 5: Has Been Contacted ─────────────────────────────
        contacted_result = self._check_contacted(contacts_at_company)
        criteria.append(contacted_result)

        # ── Data Completeness Check (bonus, not counted in score) ───────
        completeness = self._check_data_completeness(account)

        # Calculate score
        score = sum(1 for c in criteria if c.passed)
        passed = score >= self.min_score

        # Classification
        if passed and completeness >= MIN_DATA_COMPLETENESS:
            classification = "Qualified"
        elif passed and completeness < MIN_DATA_COMPLETENESS:
            classification = "Review"  # Passed gate but low data quality
        else:
            classification = "Rejected"

        # In review mode, "Review" classifications pass
        if self.mode == GOVERNANCE_MODE_REVIEW and classification == "Review":
            passed = True

        # In audit mode, everything passes (we just log)
        if self.mode == GOVERNANCE_MODE_AUDIT:
            passed = True

        reject_reason = ""
        if not passed:
            failed_criteria = [c.name for c in criteria if not c.passed]
            reject_reason = f"Failed gate: only {score}/{self.min_score} criteria met. Missing: {', '.join(failed_criteria)}"

        return GateResult(
            entity_id=account_id,
            entity_name=account_name,
            entity_type="company",
            passed=passed,
            score=score,
            min_score=self.min_score,
            criteria=criteria,
            reject_reason=reject_reason,
            classification=classification,
        )

    def _check_icp(self, account: Dict) -> GateCriterion:
        """Check if company matches Ideal Customer Profile."""
        industry = (account.get("industry") or "").strip().lower()
        country = (account.get("country") or "").strip()
        employees = account.get("num_employees") or 0

        icp_industry = any(ind.lower() in industry for ind in ICP_INDUSTRIES) if industry else False
        icp_country = country in ICP_COUNTRIES if country else False
        icp_size = employees >= ICP_MIN_EMPLOYEES if employees else False

        # ICP = at least industry match + one of (country or size)
        passed = icp_industry and (icp_country or icp_size)

        detail_parts = []
        if icp_industry:
            detail_parts.append(f"industry={industry}")
        if icp_country:
            detail_parts.append(f"country={country}")
        if icp_size:
            detail_parts.append(f"employees={employees}")

        return GateCriterion(
            name="ICP Match",
            passed=passed,
            detail=", ".join(detail_parts) if detail_parts else "No ICP match",
        )

    def _check_senior_contact(self, contacts: List[Dict]) -> GateCriterion:
        """Check if company has at least one senior contact."""
        senior_found = []

        for c in contacts:
            seniority_raw = (c.get("seniority") or "").strip().lower()
            seniority = SENIORITY_NORMALIZE.get(seniority_raw, seniority_raw.title())

            title = (c.get("title") or "").lower()

            is_senior_by_seniority = seniority in SENIOR_SENIORITIES
            is_senior_by_title = any(kw in title for kw in SENIOR_TITLE_KEYWORDS)

            if is_senior_by_seniority or is_senior_by_title:
                senior_found.append(
                    f"{c.get('name', '?')} ({c.get('title', '?')})"
                )

        return GateCriterion(
            name="Senior Contact",
            passed=len(senior_found) > 0,
            detail=f"{len(senior_found)} found: {', '.join(senior_found[:3])}" if senior_found else "No senior contacts",
        )

    def _check_engagement(self, contacts: List[Dict]) -> GateCriterion:
        """Check if the company has a REAL intent signal (2026-04-11).

        Real intent = any of:
          • Replied
          • Meeting booked
          • Email Open Count >= 2 (repeated opens, not a one-off)
          • Internal forwarding / multiple unique openers
          • Explicit repeated_engagement_detected flag

        Aggregated at the company level — any single contact passing triggers
        the company criterion. A single one-time open is intentionally
        excluded to avoid false positives from preview pixels.
        """
        is_intent, reasons = company_has_real_intent(contacts)

        # Per-contact detail for debugging
        per_contact = []
        for c in contacts:
            hit, rs = has_real_intent(c)
            if hit:
                per_contact.append(f"{c.get('name', '?')}: {','.join(rs)}")

        detail = (
            f"{len(per_contact)} intent-positive contacts ({', '.join(reasons)})"
            if is_intent else "No real intent signal"
        )

        if is_intent:
            logger.info(
                f"[Intent] Company marked as intent-positive: {', '.join(reasons)}"
            )

        return GateCriterion(
            name="Intent Signal",
            passed=is_intent,
            detail=detail,
        )

    def _check_trigger_events(self, account: Dict) -> GateCriterion:
        """Check for trigger events: funding, headcount growth, hiring."""
        triggers = []

        # Headcount growth (any period > threshold)
        for period in ["organization_headcount_six_month_growth",
                       "headcount_six_month_growth",
                       "organization_headcount_twelve_month_growth",
                       "headcount_twelve_month_growth"]:
            growth = account.get(period)
            if growth is not None:
                try:
                    if float(growth) >= TRIGGER_HEADCOUNT_GROWTH_THRESHOLD:
                        triggers.append(f"growth={float(growth):.0%}")
                        break
                except (ValueError, TypeError):
                    pass

        # Recent funding
        last_raised = account.get("last_funding_date") or account.get("latest_funding_date")
        if last_raised:
            try:
                funding_date = datetime.strptime(str(last_raised)[:10], "%Y-%m-%d")
                if (datetime.now() - funding_date).days <= TRIGGER_FUNDING_RECENCY_DAYS:
                    amount = account.get("latest_funding_amount")
                    triggers.append(f"funding=${amount:,.0f}" if amount else "recent funding")
            except (ValueError, TypeError):
                pass

        # AI Qualification = Qualified (from Apollo AI)
        typed_fields = account.get("typed_custom_fields") or {}
        ai_qual = typed_fields.get("6913a64c52c2780001146d22", "")
        if isinstance(ai_qual, str) and "Qualified" in ai_qual and "Disqualified" not in ai_qual:
            triggers.append("AI Qualified")

        return GateCriterion(
            name="Trigger Event",
            passed=len(triggers) > 0,
            detail=", ".join(triggers) if triggers else "No triggers detected",
        )

    def _check_contacted(self, contacts: List[Dict]) -> GateCriterion:
        """Check if any contact at this company has been contacted."""
        contacted = []

        for c in contacts:
            campaigns = c.get("emailer_campaign_ids") or []
            email_sent = c.get("email_sent")
            last_activity = c.get("last_activity_date")

            if campaigns or email_sent or last_activity:
                contacted.append(c.get("name", "?"))

        return GateCriterion(
            name="Contacted",
            passed=len(contacted) > 0,
            detail=f"{len(contacted)} contacts reached" if contacted else "No outreach activity",
        )

    def _check_data_completeness(self, account: Dict) -> float:
        """Check what percentage of key fields are populated."""
        populated = 0
        for field_name in COMPANY_KEY_FIELDS:
            val = account.get(field_name)
            if val and str(val).strip():
                populated += 1
        return populated / len(COMPANY_KEY_FIELDS) if COMPANY_KEY_FIELDS else 0


# ─── Contact Gate ───────────────────────────────────────────────────────────

class ContactGate:
    """
    Evaluate whether a contact should be ingested.

    Must pass ALL criteria:
    1. Linked to a company that exists in the system
    2. Has valid email
    3. Has identifiable role (Decision Maker / Influencer / End User)
    4. Has an owner assigned
    """

    def __init__(self, company_lookup: Dict = None, mode: str = GOVERNANCE_MODE_STRICT):
        self.company_lookup = company_lookup or {}
        self.mode = mode

    def evaluate(self, contact: Dict) -> GateResult:
        """Evaluate a contact against all gate criteria."""
        contact_id = contact.get("id", "unknown")
        contact_name = contact.get("name", "Unknown Contact")

        criteria = []

        # ── Criterion 1: Linked to Company ──────────────────────────────
        account_id = contact.get("account_id", "")
        has_company = bool(account_id and self.company_lookup.get(f"aid:{account_id}"))
        criteria.append(GateCriterion(
            name="Company Link",
            passed=has_company,
            detail=f"account_id={account_id}" if has_company else "No company link",
        ))

        # ── Criterion 2: Valid Email ────────────────────────────────────
        email = (contact.get("email") or "").strip()
        email_status = (contact.get("email_status") or "").lower()
        has_email = bool(email) and email_status not in {"bounced", "invalid"}
        criteria.append(GateCriterion(
            name="Valid Email",
            passed=has_email,
            detail=f"email={email}" if has_email else f"Missing/invalid email (status={email_status})",
        ))

        # ── Criterion 3: Identifiable Role ──────────────────────────────
        role = self._classify_role(contact)
        has_role = role != "Unknown"
        criteria.append(GateCriterion(
            name="Role Identified",
            passed=has_role,
            detail=f"role={role}" if has_role else "Cannot determine role",
        ))

        # ── Criterion 4: Has Owner ──────────────────────────────────────
        owner_id = contact.get("owner_id")
        has_owner = bool(owner_id and APOLLO_OWNER_MAP.get(owner_id))
        criteria.append(GateCriterion(
            name="Has Owner",
            passed=has_owner,
            detail=f"owner={APOLLO_OWNER_MAP.get(owner_id, '?')}" if has_owner else "No owner",
        ))

        # All criteria must pass
        score = sum(1 for c in criteria if c.passed)
        min_score = len(criteria)
        passed = score == min_score

        if self.mode == GOVERNANCE_MODE_AUDIT:
            passed = True

        reject_reason = ""
        if not passed:
            failed = [c.name for c in criteria if not c.passed]
            reject_reason = f"Contact gate failed: {', '.join(failed)}"

        return GateResult(
            entity_id=contact_id,
            entity_name=contact_name,
            entity_type="contact",
            passed=passed,
            score=score,
            min_score=min_score,
            criteria=criteria,
            reject_reason=reject_reason,
            classification="Qualified" if passed else "Rejected",
        )

    def _classify_role(self, contact: Dict) -> str:
        """Classify contact role based on seniority and title."""
        seniority_raw = (contact.get("seniority") or "").strip().lower()
        seniority = SENIORITY_NORMALIZE.get(seniority_raw, seniority_raw.title())
        title = (contact.get("title") or "").lower()

        # Decision Maker
        if seniority in {"C-Suite", "Owner", "Founder", "Partner"}:
            return "Decision Maker"
        if any(kw in title for kw in ROLE_DECISION_MAKER_KEYWORDS):
            return "Decision Maker"

        # Influencer
        if seniority in {"VP", "Director"}:
            return "Influencer"
        if any(kw in title for kw in ROLE_INFLUENCER_KEYWORDS):
            return "Influencer"

        # End User (has title but not senior)
        if seniority in {"Manager", "Senior"} or title:
            return "End User"

        return "Unknown"


# ─── Batch Gate Evaluation ──────────────────────────────────────────────────

class IngestionGateRunner:
    """Run gates on batches of Apollo data."""

    def __init__(self, mode: str = GOVERNANCE_MODE_STRICT):
        self.mode = mode
        self.company_gate = CompanyGate(mode=mode)
        self.stats = {
            "companies_evaluated": 0,
            "companies_passed": 0,
            "companies_rejected": 0,
            "companies_review": 0,
            "contacts_evaluated": 0,
            "contacts_passed": 0,
            "contacts_rejected": 0,
            "reject_reasons": {},
        }

    def gate_companies(
        self,
        accounts: List[Dict],
        contacts: List[Dict],
    ) -> Tuple[List[Dict], List[GateResult]]:
        """
        Evaluate all companies and return only those that pass the gate.

        Returns:
            (passed_accounts, all_results) — filtered list + full audit trail
        """
        # Group contacts by account_id
        contacts_by_account: Dict[str, List[Dict]] = {}
        for c in contacts:
            aid = c.get("account_id")
            if aid:
                contacts_by_account.setdefault(aid, []).append(c)

        passed = []
        results = []

        for account in accounts:
            aid = account.get("id", "")
            company_contacts = contacts_by_account.get(aid, [])

            result = self.company_gate.evaluate(account, company_contacts)
            results.append(result)

            self.stats["companies_evaluated"] += 1

            if result.passed:
                passed.append(account)
                if result.classification == "Review":
                    self.stats["companies_review"] += 1
                else:
                    self.stats["companies_passed"] += 1
            else:
                self.stats["companies_rejected"] += 1
                reason = result.reject_reason.split(". Missing:")[0] if result.reject_reason else "Unknown"
                self.stats["reject_reasons"][reason] = self.stats["reject_reasons"].get(reason, 0) + 1

        return passed, results

    def gate_contacts(
        self,
        contacts: List[Dict],
        company_lookup: Dict,
    ) -> Tuple[List[Dict], List[GateResult]]:
        """
        Evaluate all contacts and return only those that pass.
        """
        contact_gate = ContactGate(company_lookup=company_lookup, mode=self.mode)
        passed = []
        results = []

        for contact in contacts:
            result = contact_gate.evaluate(contact)
            results.append(result)

            self.stats["contacts_evaluated"] += 1

            if result.passed:
                passed.append(contact)
                self.stats["contacts_passed"] += 1
            else:
                self.stats["contacts_rejected"] += 1

        return passed, results

    def summary(self) -> str:
        """Generate gate summary."""
        lines = [
            "═══ INGESTION GATE SUMMARY ═══════════════════════════════",
            f"  Mode: {self.mode.upper()}",
            f"",
            f"  Companies: {self.stats['companies_evaluated']} evaluated",
            f"    ✅ Passed:   {self.stats['companies_passed']}",
            f"    🔍 Review:   {self.stats['companies_review']}",
            f"    ❌ Rejected: {self.stats['companies_rejected']}",
            f"    Pass Rate:   {self.stats['companies_passed'] / max(self.stats['companies_evaluated'], 1):.1%}",
            f"",
            f"  Contacts: {self.stats['contacts_evaluated']} evaluated",
            f"    ✅ Passed:   {self.stats['contacts_passed']}",
            f"    ❌ Rejected: {self.stats['contacts_rejected']}",
            f"    Pass Rate:   {self.stats['contacts_passed'] / max(self.stats['contacts_evaluated'], 1):.1%}",
        ]

        if self.stats["reject_reasons"]:
            lines.append("")
            lines.append("  Top Reject Reasons:")
            sorted_reasons = sorted(
                self.stats["reject_reasons"].items(),
                key=lambda x: x[1],
                reverse=True,
            )
            for reason, count in sorted_reasons[:5]:
                lines.append(f"    • {reason}: {count}")

        lines.append("═══════════════════════════════════════════════════════════")
        return "\n".join(lines)

    def save_report(self, results: List[GateResult], filepath: str = "ingestion_gate_report.json"):
        """Save detailed gate report to JSON."""
        report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "mode": self.mode,
            "stats": self.stats,
            "results": [
                {
                    "id": r.entity_id,
                    "name": r.entity_name,
                    "type": r.entity_type,
                    "passed": r.passed,
                    "score": r.score,
                    "classification": r.classification,
                    "reject_reason": r.reject_reason,
                    "criteria": [
                        {"name": c.name, "passed": c.passed, "detail": c.detail}
                        for c in r.criteria
                    ],
                }
                for r in results
            ],
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        logger.info(f"Gate report saved to {filepath}")


# ─── CLI ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="AI Sales OS — Ingestion Gate")
    parser.add_argument("--mode", choices=["strict", "review", "audit"], default="audit",
                        help="Gate enforcement mode (default: audit)")
    # FIX C-04: --enforce is a documented alias for --mode strict.
    # Previously only --mode strict existed, but CLAUDE.md referenced --enforce.
    parser.add_argument("--enforce", action="store_true",
                        help="Apply gate decisions (alias for --mode strict)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Run in audit mode regardless of --mode (safe, no writes)")
    parser.add_argument("--report", action="store_true",
                        help="Save detailed report to JSON")
    parser.add_argument("--limit", type=int, default=0,
                        help="Limit number of companies to evaluate (0 = all)")
    args = parser.parse_args()

    # Priority: --dry-run overrides everything → --enforce = strict → --mode
    if args.dry_run:
        mode = GOVERNANCE_MODE_AUDIT
    elif args.enforce:
        mode = GOVERNANCE_MODE_STRICT
    else:
        mode = args.mode

    logger.info(f"🚪 Ingestion Gate starting (mode: {mode})")
    logger.info("  This script evaluates Apollo data against ingestion criteria.")
    logger.info("  No data will be modified in audit/dry-run mode.")

    # In standalone mode, we'd fetch from Apollo
    # When integrated with daily_sync.py, this is called as a library
    logger.info("")
    logger.info("⚠️  Standalone mode: Use --dry-run to preview gate results.")
    logger.info("    For production use, ingestion_gate is called from daily_sync.py")
    logger.info("")
    logger.info("    Integration example:")
    logger.info("      from governance.ingestion_gate import IngestionGateRunner")
    logger.info("      runner = IngestionGateRunner(mode='strict')")
    logger.info("      passed_accounts, results = runner.gate_companies(accounts, contacts)")
    logger.info("")

    runner = IngestionGateRunner(mode=mode)
    logger.info(runner.summary())


if __name__ == "__main__":
    main()
