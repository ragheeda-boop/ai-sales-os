"""
ai_action_executor.py — Orchestrator: Apollo AI fields → Notion execution

The single entry point that converts Apollo AI Custom Fields into
live sales actions with ZERO manual decision making.

Flow per contact:
  1. Fetch Notion contact page (and linked company, if any)
  2. Extract Apollo AI fields via ai_decision_engine.AIFields.from_notion_props()
  3. Score → Tier via ai_decision_engine.score_contact()
  4. Write Score / Tier / Action Ready back to Contact
  5. If tier in {HOT, WARM}: dedup & create ONE company-level task (v5.0 model)
     • Task description = call_script_builder output for HOT
     • Task description = ai_sequence_generator email 1 preview for WARM
  6. Write Priority (P1/P2/P3) to linked Company
  7. Idempotent: skip contacts with recent Action Ready = True that already
     have an open task for the same company.

Integration with existing pipeline (GitHub Actions v3.0):
  Inject as Job 1 step 4a (after action_ready_updater.py) OR run standalone
  after-hours. Defaults to --dry-run.

CLI:
  python automation/ai_action_executor.py --dry-run
  python automation/ai_action_executor.py --execute
  python automation/ai_action_executor.py --execute --limit 50
  python automation/ai_action_executor.py --execute --tier HOT
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

# Local imports — assume scripts/ is on sys.path (matches existing convention)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import constants as C  # noqa: E402
from core.notion_helpers import (  # noqa: E402
    NotionClient,
    safe_select,
    safe_number,
    safe_checkbox,
    safe_rich_text,
)
from scoring.ai_decision_engine import (  # noqa: E402
    AIFields,
    ScoreResult,
    score_contact,
    decide_action,
)
from automation.call_script_builder import build_call_script  # noqa: E402
from automation.ai_sequence_generator import generate_sequence  # noqa: E402


logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# Env vars (fail loudly — no hardcoded fallbacks, per Decision #23)
# ──────────────────────────────────────────────────────────────────────────────

REQUIRED_ENV = [
    "NOTION_API_KEY",
    "NOTION_DATABASE_ID_CONTACTS",
    "NOTION_DATABASE_ID_COMPANIES",
    "NOTION_DATABASE_ID_TASKS",
]


def _require_env() -> Dict[str, str]:
    missing = [k for k in REQUIRED_ENV if not os.getenv(k)]
    if missing:
        raise EnvironmentError(
            f"ai_action_executor.py requires env vars: {', '.join(missing)}"
        )
    return {k: os.environ[k] for k in REQUIRED_ENV}


# ──────────────────────────────────────────────────────────────────────────────
# Data classes
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class RunStats:
    processed: int = 0
    scored_ai: int = 0
    scored_fallback: int = 0
    tasks_created: int = 0
    tasks_skipped_dedup: int = 0
    tasks_skipped_not_ready: int = 0
    companies_prioritized: int = 0
    errors: int = 0
    dry_run: bool = True

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CompanyTaskKey:
    company_id: str
    task_type: str  # "Urgent Call" or "Follow-up"


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _get_relation_ids(props: Dict[str, Any], key: str) -> List[str]:
    p = props.get(key) or {}
    if p.get("type") != "relation":
        return []
    return [r.get("id") for r in (p.get("relation") or []) if r.get("id")]


def _get_title(props: Dict[str, Any]) -> str:
    for k, v in props.items():
        if isinstance(v, dict) and v.get("type") == "title":
            return "".join(r.get("plain_text", "") for r in (v.get("title") or []))
    return ""


def _select_name(props: Dict[str, Any], key: str) -> str:
    p = props.get(key) or {}
    if p.get("type") == "select" and p.get("select"):
        return p["select"].get("name", "")
    return ""


def _checkbox(props: Dict[str, Any], key: str) -> bool:
    p = props.get(key) or {}
    return bool(p.get("checkbox")) if p.get("type") == "checkbox" else False


def priority_from_tier(tier: str) -> str:
    return {"HOT": "P1", "WARM": "P2", "COLD": "P3"}.get(tier, "P3")


# ──────────────────────────────────────────────────────────────────────────────
# Core executor
# ──────────────────────────────────────────────────────────────────────────────

class AIActionExecutor:
    def __init__(self, notion: NotionClient, dry_run: bool = True):
        self.n = notion
        self.dry_run = dry_run
        self.stats = RunStats(dry_run=dry_run)
        self.contacts_db = os.environ["NOTION_DATABASE_ID_CONTACTS"]
        self.companies_db = os.environ["NOTION_DATABASE_ID_COMPANIES"]
        self.tasks_db = os.environ["NOTION_DATABASE_ID_TASKS"]

        # Dedup keys seen during this run (in-memory)
        self._created_task_keys: set[Tuple[str, str]] = set()
        self._open_task_keys: set[Tuple[str, str]] = set()

    # ── Phase 1: Load open tasks for dedup ──
    def preload_open_tasks(self) -> None:
        """Load ALL currently open tasks keyed by (company_id, task_type)."""
        logger.info("Preloading open tasks for dedup …")
        filter_ = {
            "and": [
                {"property": C.FIELD_TASK_STATUS if hasattr(C, "FIELD_TASK_STATUS") else "Status",
                 "status": {"does_not_equal": "Completed"}},
            ]
        }
        count = 0
        for page in self.n.query_all(self.tasks_db, filter_=filter_):
            props = page.get("properties", {})
            task_type = _select_name(props, "Task Type")
            company_ids = _get_relation_ids(props, "Company")
            for cid in company_ids:
                self._open_task_keys.add((cid, task_type))
                count += 1
        logger.info("Open-task dedup cache: %d (company, type) keys", count)

    # ── Phase 2: Stream Action Ready contacts ──
    def iter_action_ready(self, tier_filter: Optional[str] = None, limit: Optional[int] = None) -> Iterable[Dict[str, Any]]:
        filter_ = {
            "and": [
                {"property": C.FIELD_ACTION_READY, "checkbox": {"equals": True}},
            ]
        }
        if tier_filter:
            filter_["and"].append(
                {"property": C.FIELD_LEAD_TIER, "select": {"equals": tier_filter}}
            )
        n = 0
        for page in self.n.query_all(self.contacts_db, filter_=filter_):
            yield page
            n += 1
            if limit and n >= limit:
                return

    # ── Phase 3: Process one contact ──
    def process_contact(self, contact: Dict[str, Any]) -> None:
        self.stats.processed += 1
        contact_id = contact["id"]
        props = contact.get("properties", {})
        contact_name = _get_title(props)

        # Current demographic score, if any — used as fallback baseline
        demo_score = None
        lead_score_prop = props.get(C.FIELD_LEAD_SCORE) or {}
        if lead_score_prop.get("type") == "number":
            demo_score = lead_score_prop.get("number")

        try:
            result = score_contact(props, demographic_fallback_score=demo_score)
        except Exception as e:
            logger.exception("Scoring failed for %s: %s", contact_id, e)
            self.stats.errors += 1
            return

        if result.source == "ai_engine" or result.source == "hybrid":
            self.stats.scored_ai += 1
        else:
            self.stats.scored_fallback += 1

        # Build enrichments once (used for contact write + company write + task desc)
        contact_enrichment = self._build_contact_enrichment(props, result, contact_name)
        company_enrichment = self._build_company_enrichment(props, result)

        # Only HOT/WARM get action. COLD gets scored-and-forget (still enriched).
        if result.tier not in {"HOT", "WARM"}:
            self._write_contact_result(contact_id, result, None, contact_enrichment)
            return

        # Resolve linked company for company-centric dedup
        company_ids = _get_relation_ids(props, "Company")
        if not company_ids:
            self.stats.tasks_skipped_not_ready += 1
            self._write_contact_result(contact_id, result, None, contact_enrichment)
            logger.debug("No company link on %s — score written, no task", contact_name)
            return

        company_id = company_ids[0]
        task_type = result.action  # "Urgent Call" / "Follow-up"

        key = (company_id, task_type)
        if key in self._open_task_keys or key in self._created_task_keys:
            self.stats.tasks_skipped_dedup += 1
            self._write_contact_result(contact_id, result, None, contact_enrichment)
            self._write_company_enrichment(company_id, result.tier, company_enrichment)
            return

        # Build description (call script for HOT, email 1 for WARM)
        description_md = self._build_task_description(props, result, contact_name)

        # Create task
        task_id = self._create_company_task(
            company_id=company_id,
            contact_id=contact_id,
            task_type=task_type,
            priority=result.priority,
            sla_hours=result.sla_hours or 48,
            description=description_md,
            tier=result.tier,
        )
        if task_id:
            self.stats.tasks_created += 1
            self._created_task_keys.add(key)

        # Write score + enrichment back
        self._write_contact_result(contact_id, result, task_id, contact_enrichment)
        self._write_company_enrichment(company_id, result.tier, company_enrichment)

    # ── Sub-phase: enrichment payloads for Contact + Company writes ──
    def _build_contact_enrichment(
        self, props: Dict[str, Any], result: ScoreResult, contact_name: str
    ) -> Dict[str, Any]:
        """Return the Email Draft + Call Script Clean text for a contact."""
        fields = AIFields.from_notion_props(props)
        if result.tier == "HOT":
            script = build_call_script(
                ai_call_script=fields.call_script,
                pain_points=fields.pain_points,
                contact_name=contact_name,
                company="",
                message_angle=fields.message_angle,
                industry=fields.industry,
                tier="HOT",
            )
            return {
                "call_script_clean": script.full_markdown,
                "email_draft": "",  # HOT = call-first
            }
        if result.tier == "WARM":
            seq = generate_sequence(
                contact_name=contact_name,
                company="",
                title=fields.title,
                pain_points=fields.pain_points,
                message_angle=fields.message_angle,
                research_context=fields.research_context,
                seniority=fields.seniority or "",
                buyer_role=fields.buyer_role or "",
            )
            return {
                "call_script_clean": "",
                "email_draft": (
                    f"Subject: {seq.email_1_subject}\n\n{seq.email_1_body}"
                ),
            }
        return {"call_script_clean": "", "email_draft": ""}

    def _build_company_enrichment(
        self, props: Dict[str, Any], result: ScoreResult
    ) -> Dict[str, str]:
        """Derive Strategic Fit / Pain Summary / Sales Angle from AI fields."""
        fields = AIFields.from_notion_props(props)
        # Strategic Fit = tier-based narrative
        if result.tier == "HOT":
            fit = (
                f"P1 — strong strategic fit. {result.source}={result.score}/100. "
                f"Decision Maker engaged, pain mapped to MUHIDE solution."
            )
        elif result.tier == "WARM":
            fit = (
                f"P2 — qualified but requires nurture. {result.source}={result.score}/100. "
                f"Influencer-level contact or incomplete decision signal."
            )
        else:
            fit = f"P3 — monitor only. {result.source}={result.score}/100."

        # Pain Summary = top pain points condensed
        pain = (fields.pain_points or "").strip()
        if not pain and fields.ai_reasoning:
            pain = fields.ai_reasoning.strip()
        pain_summary = pain[:800] if pain else "No pain points identified by Apollo AI."

        # Sales Angle = message angle or reconstructed from research
        angle = (fields.message_angle or "").strip()
        if not angle:
            research = (fields.research_context or "").strip()
            angle = (
                f"Lead with: {research[:500]}" if research
                else "Standard outreach — pain-first discovery."
            )
        sales_angle = angle[:800]

        return {
            "strategic_fit": fit[:1900],
            "pain_summary": pain_summary,
            "sales_angle": sales_angle,
        }

    # ── Sub-phase: build task description from AI + builders ──
    def _build_task_description(self, props: Dict[str, Any], result: ScoreResult, contact_name: str) -> str:
        fields = AIFields.from_notion_props(props)
        # Fetch company name if possible — but we only have ID here.
        # Keeping it lightweight: just pass empty company, rep knows from link.
        company = ""
        if result.tier == "HOT":
            script = build_call_script(
                ai_call_script=fields.call_script,
                pain_points=fields.pain_points,
                contact_name=contact_name,
                company=company,
                message_angle=fields.message_angle,
                industry=fields.industry,
                tier="HOT",
            )
            header = (
                f"## AI-Driven Urgent Call\n"
                f"**Score:** {result.score} ({result.tier})\n"
                f"**Source:** {result.source}\n"
                f"**Reasons:** {'; '.join(result.reasons[:4])}\n\n"
            )
            return header + script.full_markdown
        # WARM → sequence preview
        seq = generate_sequence(
            contact_name=contact_name,
            company=company,
            title=fields.title,
            pain_points=fields.pain_points,
            message_angle=fields.message_angle,
            research_context=fields.research_context,
            seniority=fields.seniority or "",
            buyer_role=fields.buyer_role or "",
        )
        header = (
            f"## AI-Driven Follow-up\n"
            f"**Score:** {result.score} ({result.tier})\n"
            f"**Detected Role:** {seq.role}\n"
            f"**Reasons:** {'; '.join(result.reasons[:4])}\n\n"
        )
        return header + seq.as_markdown()

    # ── Notion writers ──
    def _write_contact_result(
        self,
        contact_id: str,
        result: ScoreResult,
        task_id: Optional[str],
        enrichment: Optional[Dict[str, str]] = None,
    ) -> None:
        """Write Lead Score, Tier, plus optional Call Script Clean / Email Draft."""
        update: Dict[str, Any] = {
            C.FIELD_LEAD_SCORE: safe_number(result.score),
            C.FIELD_LEAD_TIER: safe_select(result.tier),
        }
        if enrichment:
            if enrichment.get("call_script_clean"):
                update["Call Script Clean"] = safe_rich_text(
                    enrichment["call_script_clean"][:1950]
                )
            if enrichment.get("email_draft"):
                update["Email Draft"] = safe_rich_text(
                    enrichment["email_draft"][:1950]
                )
        if self.dry_run:
            logger.debug("[DRY] Would update contact %s → %s", contact_id, result.tier)
            return
        try:
            self.n.update_page(contact_id, properties=update)
        except Exception as e:
            self.stats.errors += 1
            logger.exception("Failed to update contact %s: %s", contact_id, e)

    def _write_company_enrichment(
        self, company_id: str, tier: str, enrichment: Dict[str, str]
    ) -> None:
        """Write Priority + Strategic Fit + Pain Summary + Sales Angle to a Company."""
        priority = priority_from_tier(tier)
        update = {
            "Priority": safe_select(priority),
            "Strategic Fit": safe_rich_text(enrichment["strategic_fit"]),
            "Pain Summary": safe_rich_text(enrichment["pain_summary"]),
            "Sales Angle": safe_rich_text(enrichment["sales_angle"]),
        }
        if self.dry_run:
            logger.debug("[DRY] Would enrich company %s (priority=%s)", company_id, priority)
            self.stats.companies_prioritized += 1
            return
        try:
            self.n.update_page(company_id, properties=update)
            self.stats.companies_prioritized += 1
        except Exception as e:
            logger.exception("Failed to enrich company %s: %s", company_id, e)

    def _create_company_task(
        self,
        company_id: str,
        contact_id: str,
        task_type: str,
        priority: str,
        sla_hours: int,
        description: str,
        tier: str,
    ) -> Optional[str]:
        due = datetime.now(timezone.utc) + timedelta(hours=sla_hours)
        title = f"[{tier}] {task_type} — company {company_id[:8]}"
        props = {
            "Task Title": {"title": [{"text": {"content": title}}]},
            "Priority": safe_select(priority),
            "Status": {"status": {"name": "Not Started"}},
            "Due Date": {"date": {"start": due.isoformat()}},
            "Task Type": safe_select(task_type),
            "Company": {"relation": [{"id": company_id}]},
            "Contact": {"relation": [{"id": contact_id}]},
            "Auto Created": safe_checkbox(True),
            "Automation Type": safe_select("AI Decision Engine"),
            "Description": safe_rich_text(description[:1950]),  # Notion 2000-char cap
        }
        if self.dry_run:
            logger.info("[DRY] Would create task %s", title)
            return "dry-run"
        try:
            page = self.n.create_page(parent_db=self.tasks_db, properties=props)
            return page.get("id")
        except Exception as e:
            self.stats.errors += 1
            logger.exception("Failed to create task %s: %s", title, e)
            return None

    # ── Run loop ──
    def run(self, tier_filter: Optional[str] = None, limit: Optional[int] = None) -> RunStats:
        self.preload_open_tasks()
        for contact in self.iter_action_ready(tier_filter=tier_filter, limit=limit):
            self.process_contact(contact)
        return self.stats


# ──────────────────────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(description="AI Action Executor — Apollo AI → Notion execution")
    parser.add_argument("--execute", action="store_true", help="Apply changes (default is dry-run)")
    parser.add_argument("--tier", choices=["HOT", "WARM"], help="Filter to a single tier")
    parser.add_argument("--limit", type=int, help="Limit to first N contacts (testing)")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--stats-out", default="data/logs/ai_action_executor_stats.json")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    _require_env()
    notion = NotionClient(os.environ["NOTION_API_KEY"])
    executor = AIActionExecutor(notion=notion, dry_run=not args.execute)
    stats = executor.run(tier_filter=args.tier, limit=args.limit)

    stats_path = Path(args.stats_out)
    stats_path.parent.mkdir(parents=True, exist_ok=True)
    stats_path.write_text(json.dumps(stats.as_dict(), indent=2))
    logger.info("── Run complete ──")
    logger.info(json.dumps(stats.as_dict(), indent=2))
    return 0 if stats.errors == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
