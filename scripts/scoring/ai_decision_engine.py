"""
ai_decision_engine.py — Apollo AI Fields → Final Lead Score + Tier

Converts Apollo AI Custom Fields (AI Decision, Reasoning, Pain Points,
Message Angle, Call Script, Research Context, Qualification Level, Buyer Role)
into a deterministic Lead Score (0-100) and Lead Tier (HOT/WARM/COLD).

This module REPLACES the purely demographic v1.5 weighting for contacts that
have Apollo AI fields populated. For contacts without AI fields, it falls
back to the existing lead_score.py engine.

Design:
- Pure functions. No I/O inside decide_*().
- Deterministic. Same input → same output.
- Composable with scoring/lead_score.py (fallback) and automation/auto_tasks.py.

Integration points:
- scoring/lead_score.py: import `score_from_ai_fields` and call when
  `ai_decision` is present; otherwise fall back to existing weighted formula.
- automation/auto_tasks.py: import `decide_action` to pick task type / SLA.
- automation/ai_action_executor.py: the orchestrator calls this module for
  every Action Ready contact.

Author: RevOps Architect — AI Sales OS v6.1
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from core import constants as C

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# Constants (tier thresholds + weight distribution for AI-driven scoring)
# ──────────────────────────────────────────────────────────────────────────────

# AI-driven score weights — used ONLY when AI fields exist
AI_WEIGHTS = {
    "ai_decision": 40,       # YES/NO from Apollo = strongest signal
    "buyer_role": 25,        # Decision Maker > Influencer > User
    "qualification": 15,     # Apollo Qualification Level (1-5 / High/Med/Low)
    "pain_density": 10,      # # of distinct pain points mentioned
    "research_signal": 10,   # research context contains intent triggers
}
assert sum(AI_WEIGHTS.values()) == 100, "AI_WEIGHTS must sum to 100"

# Buyer role → numeric strength (0-1)
ROLE_STRENGTH = {
    "decision maker": 1.0,
    "c-suite": 1.0,
    "ceo": 1.0,
    "cfo": 1.0,
    "cto": 1.0,
    "founder": 1.0,
    "vp": 0.85,
    "director": 0.75,
    "head": 0.75,
    "influencer": 0.6,
    "manager": 0.5,
    "end user": 0.25,
    "user": 0.25,
    "unknown": 0.3,
}

# Pain points that signal strong intent (keyword hints inside research/pain text)
PAIN_KEYWORDS = {
    "compliance", "risk", "fraud", "audit", "regulatory", "sama", "cma",
    "reconciliation", "manual process", "excel", "legacy system", "scaling",
    "hiring", "funding", "ipo", "expansion", "integration", "reporting",
    "data silo", "efficiency", "cost", "margin", "growth", "automation",
    "ai", "digital transformation", "kyc", "aml", "onboarding",
}

# Research context intent triggers
RESEARCH_TRIGGERS = {
    "recently funded", "series", "launched", "expansion", "new office",
    "hiring", "acquired", "partnership", "ipo", "earnings", "quarterly",
    "cto hired", "cfo hired", "new product", "rebrand", "restructuring",
}

# Override — research has these "kill signals" → force WARM or below
KILL_SIGNALS = {
    "not a fit", "out of market", "competitor", "consumer brand only",
    "shut down", "bankrupt", "acquired by",
}


# ──────────────────────────────────────────────────────────────────────────────
# Dataclass — unified input envelope
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class AIFields:
    """Apollo AI fields extracted from a Notion contact page.

    Use `from_notion_props(props)` to build this from a fetched page dict.
    """
    ai_decision: Optional[str] = None          # "YES" / "NO" / None
    ai_reasoning: str = ""
    pain_points: str = ""
    message_angle: str = ""
    call_script: str = ""
    research_context: str = ""
    qualification_level: Optional[str] = None  # "High"/"Medium"/"Low" or "1".."5"
    buyer_role: Optional[str] = None           # "Decision Maker"/"Influencer"/etc.
    seniority: Optional[str] = None            # fallback for role strength
    title: str = ""
    industry: str = ""

    @classmethod
    def from_notion_props(cls, props: Dict[str, Any]) -> "AIFields":
        """Build from a Notion page `properties` dict. Safe against missing fields."""
        def _text(key: str) -> str:
            p = props.get(key)
            if not p:
                return ""
            t = p.get("type")
            if t == "rich_text":
                return "".join(r.get("plain_text", "") for r in (p.get("rich_text") or []))
            if t == "title":
                return "".join(r.get("plain_text", "") for r in (p.get("title") or []))
            if t == "select":
                s = p.get("select")
                return (s or {}).get("name", "") if s else ""
            if t == "formula":
                f = p.get("formula", {})
                return str(f.get("string") or f.get("number") or "")
            return ""

        return cls(
            ai_decision=_text(C.FIELD_AI_DECISION) or None,
            ai_reasoning=_text("AI Reasoning"),
            pain_points=_text("Pain Points"),
            message_angle=_text("Message Angle"),
            call_script=_text("Call Script"),
            research_context=_text("Research Context"),
            qualification_level=_text("Qualification Level") or None,
            buyer_role=_text("Buyer Role") or None,
            seniority=_text(C.FIELD_SENIORITY) or None,
            title=_text(C.FIELD_TITLE),
            industry=_text("Industry"),
        )

    def has_ai_data(self) -> bool:
        """True if ANY Apollo AI field is populated — the engine will fire."""
        return bool(
            self.ai_decision
            or self.pain_points
            or self.call_script
            or self.message_angle
            or self.research_context
        )


@dataclass
class ScoreResult:
    score: int                          # 0-100
    tier: str                           # HOT / WARM / COLD
    source: str                         # "ai_engine" / "fallback_v1.5" / "hybrid"
    reasons: List[str] = field(default_factory=list)
    action: str = "none"                # "urgent_call" / "follow_up" / "none"
    sla_hours: Optional[int] = None
    priority: str = "Low"               # Notion Priority select
    override_applied: Optional[str] = None


# ──────────────────────────────────────────────────────────────────────────────
# Pure scoring functions
# ──────────────────────────────────────────────────────────────────────────────

def _norm(s: Optional[str]) -> str:
    return (s or "").strip().lower()


def _role_strength(fields: AIFields) -> float:
    """Return 0-1 score for buyer role. Falls back to Seniority/Title."""
    candidates = [fields.buyer_role, fields.seniority, fields.title]
    for c in candidates:
        n = _norm(c)
        if not n:
            continue
        # exact match
        if n in ROLE_STRENGTH:
            return ROLE_STRENGTH[n]
        # substring match
        for k, v in ROLE_STRENGTH.items():
            if k in n:
                return v
    return 0.3  # unknown default


def _qualification_strength(level: Optional[str]) -> float:
    if not level:
        return 0.4
    n = _norm(level)
    mapping = {
        "high": 1.0, "5": 1.0, "qualified": 1.0, "strong": 1.0,
        "medium": 0.6, "4": 0.8, "3": 0.6, "possible fit": 0.6,
        "low": 0.2, "2": 0.4, "1": 0.2, "disqualified": 0.0,
    }
    for k, v in mapping.items():
        if k in n:
            return v
    return 0.4


def _pain_density(text: str) -> float:
    """Count distinct pain keywords found. Scale to 0-1 (saturates at 5 hits)."""
    if not text:
        return 0.0
    t = text.lower()
    hits = sum(1 for kw in PAIN_KEYWORDS if kw in t)
    return min(hits / 5.0, 1.0)


def _research_signal(text: str) -> Tuple[float, bool]:
    """Return (0-1 strength, kill_signal_detected)."""
    if not text:
        return 0.0, False
    t = text.lower()
    kill = any(ks in t for ks in KILL_SIGNALS)
    hits = sum(1 for trig in RESEARCH_TRIGGERS if trig in t)
    return min(hits / 3.0, 1.0), kill


def score_from_ai_fields(fields: AIFields) -> ScoreResult:
    """Compute Lead Score + Tier from Apollo AI fields.

    Returns ScoreResult with score, tier, action, sla_hours, priority, reasons.
    """
    reasons: List[str] = []

    if not fields.has_ai_data():
        return ScoreResult(
            score=0, tier="COLD", source="fallback_v1.5",
            reasons=["no AI fields — caller should use lead_score.py"],
        )

    # ── Component 1: AI Decision (40 pts) ──
    ai_dec = _norm(fields.ai_decision)
    if ai_dec == "yes":
        ai_component = 1.0
        reasons.append("AI Decision = YES (+40)")
    elif ai_dec == "no":
        ai_component = 0.0
        reasons.append("AI Decision = NO (+0)")
    else:
        ai_component = 0.4  # unknown / missing
        reasons.append("AI Decision unknown (+16)")

    # ── Component 2: Buyer Role (25 pts) ──
    role = _role_strength(fields)
    reasons.append(f"Role strength {role:.2f} (+{int(role * AI_WEIGHTS['buyer_role'])})")

    # ── Component 3: Qualification level (15 pts) ──
    qual = _qualification_strength(fields.qualification_level)
    reasons.append(f"Qualification {qual:.2f} (+{int(qual * AI_WEIGHTS['qualification'])})")

    # ── Component 4: Pain density (10 pts) ──
    pain_text = f"{fields.pain_points}\n{fields.ai_reasoning}"
    pain = _pain_density(pain_text)
    reasons.append(f"Pain density {pain:.2f} (+{int(pain * AI_WEIGHTS['pain_density'])})")

    # ── Component 5: Research signal (10 pts) + kill override ──
    research, kill = _research_signal(fields.research_context)
    reasons.append(f"Research signal {research:.2f} (+{int(research * AI_WEIGHTS['research_signal'])})")

    # Weighted sum
    raw = (
        ai_component * AI_WEIGHTS["ai_decision"]
        + role * AI_WEIGHTS["buyer_role"]
        + qual * AI_WEIGHTS["qualification"]
        + pain * AI_WEIGHTS["pain_density"]
        + research * AI_WEIGHTS["research_signal"]
    )
    score = int(round(raw))

    override: Optional[str] = None

    # ── Override 1: KILL signals force COLD ──
    if kill:
        score = min(score, 35)
        override = "kill_signal_detected"
        reasons.append(f"KILL SIGNAL in research → score capped at 35")

    # ── Override 2: AI Decision = NO + low pain → force COLD ──
    if ai_dec == "no" and pain < 0.2:
        score = min(score, 40)
        override = override or "ai_no_low_pain"
        reasons.append("AI=NO + low pain → capped at 40")

    # ── Override 3: Strong research + Decision Maker bumps borderline WARM→HOT ──
    if 70 <= score < 80 and role >= 0.85 and research >= 0.66:
        score = 82
        override = override or "dm_strong_research_bump"
        reasons.append("DM + strong research → bumped to 82")

    score = max(0, min(100, score))
    tier = classify_tier(score, role, ai_dec)
    action, sla, priority = decide_action(tier)

    return ScoreResult(
        score=score,
        tier=tier,
        source="ai_engine",
        reasons=reasons,
        action=action,
        sla_hours=sla,
        priority=priority,
        override_applied=override,
    )


def classify_tier(score: int, role_strength: float, ai_decision: str) -> str:
    """HOT/WARM/COLD classification with role-aware rules.

    Rules (in order):
      AI=YES + Decision Maker          → HOT
      AI=YES + other role              → WARM  (unless score also >= 80)
      AI=NO                            → COLD  (unless score >= 50 overrode)
      Score >= SCORE_HOT               → HOT
      Score >= SCORE_WARM              → WARM
      else                             → COLD
    """
    ai = _norm(ai_decision)
    if ai == "yes" and role_strength >= 0.85:
        return "HOT"
    if ai == "yes" and score >= C.SCORE_HOT:
        return "HOT"
    if ai == "yes":
        return "WARM"
    if ai == "no" and score < C.SCORE_WARM:
        return "COLD"
    if score >= C.SCORE_HOT:
        return "HOT"
    if score >= C.SCORE_WARM:
        return "WARM"
    return "COLD"


def decide_action(tier: str) -> Tuple[str, Optional[int], str]:
    """Return (task_type, sla_hours, priority) for a tier.

    Aligns with automation/auto_tasks.py v2.0 company-centric task model.
    """
    if tier == "HOT":
        return ("Urgent Call", C.SLA_HOT_HOURS, "Critical")
    if tier == "WARM":
        return ("Follow-up", C.SLA_WARM_HIGH_HOURS, "High")
    return ("none", None, "Low")


# ──────────────────────────────────────────────────────────────────────────────
# Hybrid scorer — combine AI result with demographic v1.5 when useful
# ──────────────────────────────────────────────────────────────────────────────

def hybrid_score(
    ai_result: ScoreResult,
    demographic_score: Optional[int],
) -> ScoreResult:
    """If AI and demographic both present, return the MAX with source='hybrid'.

    Rationale: demographic v1.5 captures Size+Seniority+Industry well; the AI
    engine captures Decision+Intent+Role. Taking the max prevents the engines
    from cancelling each other out, and lets either signal lift a contact.
    """
    if demographic_score is None or ai_result.source != "ai_engine":
        return ai_result
    if demographic_score <= ai_result.score:
        return ai_result
    # Demographic wins — promote its score but keep AI tier logic
    new_score = demographic_score
    new_tier = classify_tier(new_score, 1.0 if ai_result.tier == "HOT" else 0.5, "")
    action, sla, prio = decide_action(new_tier)
    return ScoreResult(
        score=new_score,
        tier=new_tier,
        source="hybrid",
        reasons=ai_result.reasons + [f"demographic v1.5 override → {new_score}"],
        action=action,
        sla_hours=sla,
        priority=prio,
        override_applied="demographic_higher",
    )


# ──────────────────────────────────────────────────────────────────────────────
# Edge case handlers
# ──────────────────────────────────────────────────────────────────────────────

def handle_edge_cases(fields: AIFields, result: ScoreResult) -> ScoreResult:
    """Apply defensive rules AFTER scoring.

    Returns a potentially modified ScoreResult.
    """
    # No decision maker → cap at WARM
    role = _role_strength(fields)
    if role < 0.6 and result.tier == "HOT":
        result.tier = "WARM"
        result.action, result.sla_hours, result.priority = decide_action("WARM")
        result.reasons.append("no DM detected → demoted HOT→WARM")

    # Missing all AI fields is handled upstream, but double-check
    if not fields.has_ai_data() and result.source == "ai_engine":
        result.source = "fallback_v1.5"
        result.reasons.append("no AI data found — source reset to fallback")

    return result


# ──────────────────────────────────────────────────────────────────────────────
# Public API — single entry point for the orchestrator
# ──────────────────────────────────────────────────────────────────────────────

def score_contact(
    props: Dict[str, Any],
    demographic_fallback_score: Optional[int] = None,
) -> ScoreResult:
    """Top-level: take a Notion contact page's `properties` dict and return a ScoreResult.

    Use this from ai_action_executor.py for each contact being processed.
    """
    fields = AIFields.from_notion_props(props)

    if not fields.has_ai_data():
        # No AI data — return shell result that the caller fills from lead_score.py
        score = demographic_fallback_score or 0
        tier = classify_tier(score, _role_strength(fields), "")
        action, sla, prio = decide_action(tier)
        return ScoreResult(
            score=score, tier=tier, source="fallback_v1.5",
            reasons=["no AI fields — demographic v1.5"],
            action=action, sla_hours=sla, priority=prio,
        )

    result = score_from_ai_fields(fields)
    result = hybrid_score(result, demographic_fallback_score)
    result = handle_edge_cases(fields, result)
    return result


# ──────────────────────────────────────────────────────────────────────────────
# CLI — dry-run against a sample or a Notion DB ID
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    p = argparse.ArgumentParser(description="AI Decision Engine — dry scorer")
    p.add_argument("--self-test", action="store_true", help="Run built-in examples")
    args = p.parse_args()

    if args.self_test:
        samples = [
            ("HOT — CEO + YES + pain", AIFields(
                ai_decision="YES", buyer_role="Decision Maker", title="CEO",
                pain_points="manual reconciliation, excel-based reporting, compliance with SAMA",
                qualification_level="High",
                research_context="Series B funded, expansion, hiring CTO",
            )),
            ("WARM — Manager + YES", AIFields(
                ai_decision="YES", buyer_role="Manager", title="Ops Manager",
                pain_points="onboarding bottleneck",
                qualification_level="Medium",
            )),
            ("COLD — NO + no pain", AIFields(
                ai_decision="NO", buyer_role="End User",
                research_context="consumer brand only, not a fit",
            )),
            ("HOT — v1.5 bump override", AIFields(
                ai_decision="YES", buyer_role="VP", title="VP Finance",
                pain_points="audit, fraud risk",
                research_context="recently funded series C, new CFO hired, launched new product",
                qualification_level="High",
            )),
        ]
        for name, f in samples:
            r = score_from_ai_fields(f)
            r = handle_edge_cases(f, r)
            print(f"\n── {name} ──")
            print(f"  score={r.score}  tier={r.tier}  action={r.action}  sla={r.sla_hours}h")
            for reason in r.reasons:
                print(f"    • {reason}")
            if r.override_applied:
                print(f"  override: {r.override_applied}")
