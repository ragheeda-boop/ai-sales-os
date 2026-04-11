"""
ai_sales_actions_parser.py — Robust parser for Apollo "AI Sales Actions"

Apollo populates an account-level rich_text field called **AI Sales Actions**
that contains a semi-structured directive block like:

    Segment: Enterprise FinTech
    Fit: High
    Priority: P1
    Urgency: High
    Signal: Series B raise, hiring CFO
    Pain: Manual reconciliation, audit exposure
    Target Role: CFO
    Action: Call
    Tone: Direct, high-urgency
    Call Hook:
    - You just raised Series B — reconciliation will break in 90 days
    - New CFO means process rebuild is on the table right now
    - We cut audit prep 70% for a team your size in 6 weeks
    Email:
      Subject: Reconciliation bottleneck post-Series B
      Opening: Ahmed — saw the Series B close. Congrats.
      Pain: Scaling from 80 → 200 people breaks Excel reconciliation within 90 days.
      Value: We cut audit prep by 70% for FinTechs your size in under 6 weeks.
      CTA: Worth a 15-min call Thursday?

This module turns that text blob into a dict of clean fields.

Design goals
────────────
• Tolerant to missing sections, extra whitespace, inconsistent casing
• Tolerant to bullet variants (- / • / * / 1. / – )
• Tolerant to nested vs flat Email sub-block
• Never raises on malformed input — returns dict with empty strings instead
• Zero external dependencies (stdlib only)
• Pure function → easy to unit test

Public API
──────────
    parse_ai_sales_actions(text: str) -> dict
    ParsedAISalesActions (dataclass, optional typed wrapper)

Return dict keys (all strings unless noted):
    segment, fit, priority, urgency, signal, pain, target_role,
    action, tone,
    call_hook          (list[str])
    email_subject, email_opening, email_pain, email_value, email_cta,
    raw                (the original input, trimmed)
    is_valid           (bool — True if at least 3 top-level fields parsed)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional

# ─────────────────────────────────────────────────────────────────────────────
# Canonical key aliases — maps normalized label → canonical output key
# ─────────────────────────────────────────────────────────────────────────────

# Top-level single-value fields (Label: Value)
TOP_LEVEL_KEYS: Dict[str, str] = {
    "segment": "segment",
    "fit": "fit",
    "priority": "priority",
    "urgency": "urgency",
    "signal": "signal",
    "signals": "signal",
    "pain": "pain",
    "pain point": "pain",
    "pain points": "pain",
    "target role": "target_role",
    "target": "target_role",
    "role": "target_role",
    "action": "action",
    "action type": "action",
    "tone": "tone",
    "voice": "tone",
}

# Multi-line / list-based fields
LIST_KEYS = {"call hook", "call hooks", "hooks"}

# Email sub-block keys (inside `Email:` block)
EMAIL_SUB_KEYS: Dict[str, str] = {
    "subject": "email_subject",
    "subject line": "email_subject",
    "opening": "email_opening",
    "open": "email_opening",
    "intro": "email_opening",
    "pain": "email_pain",
    "problem": "email_pain",
    "value": "email_value",
    "value prop": "email_value",
    "benefit": "email_value",
    "cta": "email_cta",
    "call to action": "email_cta",
    "ask": "email_cta",
}

# Bullet markers (stripped when parsing a list item)
BULLET_RE = re.compile(r"^\s*(?:[-*•–—]|\d+[.)])\s+")

# A single Label: Value line (case-insensitive, tolerant to whitespace)
LABEL_LINE_RE = re.compile(
    r"^\s*(?P<label>[A-Za-z][A-Za-z0-9 /_-]{0,40}?)\s*[:：]\s*(?P<value>.*?)\s*$"
)


# ─────────────────────────────────────────────────────────────────────────────
# Dataclass wrapper (optional — keeps call sites typed)
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class ParsedAISalesActions:
    segment: str = ""
    fit: str = ""
    priority: str = ""
    urgency: str = ""
    signal: str = ""
    pain: str = ""
    target_role: str = ""
    action: str = ""
    tone: str = ""
    call_hook: List[str] = field(default_factory=list)
    email_subject: str = ""
    email_opening: str = ""
    email_pain: str = ""
    email_value: str = ""
    email_cta: str = ""
    raw: str = ""
    is_valid: bool = False

    def as_dict(self) -> Dict[str, object]:
        return asdict(self)

    @property
    def call_hook_joined(self) -> str:
        """Return call_hook as a single newline-joined string (for rich_text writes)."""
        return "\n".join(f"• {h}" for h in self.call_hook if h)

    @property
    def is_call_action(self) -> bool:
        return _normalize_action(self.action) == "call"

    @property
    def is_email_action(self) -> bool:
        return _normalize_action(self.action) == "email"

    @property
    def is_sequence_action(self) -> bool:
        return _normalize_action(self.action) == "sequence"


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _normalize_label(label: str) -> str:
    return re.sub(r"\s+", " ", label.strip().lower())


def _strip_bullet(line: str) -> str:
    return BULLET_RE.sub("", line).strip()


def _is_blank(line: str) -> bool:
    return not line.strip()


def _normalize_action(value: str) -> str:
    """Map action verb variants to canonical: call / email / sequence / none."""
    v = (value or "").strip().lower()
    if not v:
        return ""
    if "call" in v or "phone" in v:
        return "call"
    if "sequence" in v or "nurture" in v or "cadence" in v:
        return "sequence"
    if "email" in v or "message" in v or "send" in v:
        return "email"
    if "none" in v or "skip" in v or "no action" in v:
        return "none"
    return v


def normalize_priority(value: str) -> str:
    """Return P1 / P2 / P3 / '' — tolerant to 'p1', 'Priority 1', 'High', etc."""
    v = (value or "").strip().lower()
    if not v:
        return ""
    m = re.search(r"\bp\s*([123])\b", v)
    if m:
        return f"P{m.group(1)}"
    if v in {"high", "critical", "urgent", "top"}:
        return "P1"
    if v in {"medium", "med", "moderate"}:
        return "P2"
    if v in {"low", "monitor", "nurture"}:
        return "P3"
    m = re.match(r"^([123])$", v)
    if m:
        return f"P{m.group(1)}"
    return ""


def normalize_fit(value: str) -> str:
    """Return High / Medium / Low / '' — tolerant to variants."""
    v = (value or "").strip().lower()
    if not v:
        return ""
    if v in {"high", "strong", "excellent", "perfect", "great"}:
        return "High"
    if v in {"medium", "med", "moderate", "ok", "fair"}:
        return "Medium"
    if v in {"low", "weak", "poor", "minimal"}:
        return "Low"
    return value.strip().title()


# ─────────────────────────────────────────────────────────────────────────────
# Core parser
# ─────────────────────────────────────────────────────────────────────────────

def parse_ai_sales_actions(text: Optional[str]) -> Dict[str, object]:
    """Parse the Apollo `AI Sales Actions` block into a flat dict.

    Returns all keys always present (empty string or empty list if missing).
    Never raises on malformed input.
    """
    result = ParsedAISalesActions()
    if not text or not isinstance(text, str):
        return result.as_dict()

    result.raw = text.strip()
    lines = result.raw.splitlines()

    # State: what block are we currently filling?
    current_list: Optional[str] = None   # "call_hook" when inside a list block
    in_email_block = False
    current_email_key: Optional[str] = None  # for multi-line email sub-values

    parsed_fields_count = 0

    for raw_line in lines:
        line = raw_line.rstrip()

        # Blank line ends the current list/email-subkey capture but not the email block
        if _is_blank(line):
            current_list = None
            current_email_key = None
            continue

        # Try to match a Label: Value line (including sub-keys inside Email block)
        m = LABEL_LINE_RE.match(line)
        if m:
            label = _normalize_label(m.group("label"))
            value = m.group("value").strip()

            # ── Inside Email block: check for sub-key first ──
            if in_email_block and label in EMAIL_SUB_KEYS:
                canonical = EMAIL_SUB_KEYS[label]
                setattr(result, canonical, value)
                current_email_key = canonical
                current_list = None
                parsed_fields_count += 1
                continue

            # ── Opening of Email block ──
            if label in {"email", "email template", "email copy"}:
                in_email_block = True
                current_list = None
                current_email_key = None
                # If there's inline value after "Email:", ignore — sub-keys follow
                continue

            # ── List field opener (Call Hook:) ──
            if label in LIST_KEYS:
                current_list = "call_hook"
                in_email_block = False
                current_email_key = None
                # If value is inline after the label, capture it as first item
                if value:
                    result.call_hook.append(value)
                parsed_fields_count += 1
                continue

            # ── Top-level single-value field ──
            if label in TOP_LEVEL_KEYS:
                canonical = TOP_LEVEL_KEYS[label]
                # Exit email block when a top-level key appears
                in_email_block = False
                current_list = None
                current_email_key = None
                existing = getattr(result, canonical, "")
                # First non-empty wins — later mentions don't clobber
                if not existing:
                    setattr(result, canonical, value)
                    parsed_fields_count += 1
                continue

            # ── Unknown label inside email block: treat as continuation of prior sub-key ──
            if in_email_block and current_email_key:
                existing = getattr(result, current_email_key, "")
                setattr(result, current_email_key, f"{existing} {line.strip()}".strip())
                continue

            # Unknown label — ignore quietly
            continue

        # Non-label, non-blank line — continuation of a list, email sub-key, or prior field
        stripped = _strip_bullet(line)

        if current_list == "call_hook" and stripped:
            result.call_hook.append(stripped)
            continue

        if in_email_block and current_email_key and stripped:
            # Multi-line continuation of last email sub-key
            existing = getattr(result, current_email_key, "")
            joined = f"{existing} {stripped}".strip()
            setattr(result, current_email_key, joined)
            continue

        # Otherwise: orphan line — ignore
        continue

    # Normalize priority + fit + action
    result.priority = normalize_priority(result.priority)
    result.fit = normalize_fit(result.fit)

    # Validity = at least 3 real fields populated
    filled = sum(1 for k in ("segment", "fit", "priority", "urgency", "signal",
                             "pain", "target_role", "action", "tone")
                 if getattr(result, k))
    filled += 1 if result.call_hook else 0
    filled += 1 if result.email_subject or result.email_opening else 0
    result.is_valid = filled >= 3

    return result.as_dict()


def parse_ai_sales_actions_typed(text: Optional[str]) -> ParsedAISalesActions:
    """Typed version — returns the dataclass rather than a dict."""
    d = parse_ai_sales_actions(text)
    obj = ParsedAISalesActions()
    for k, v in d.items():
        if hasattr(obj, k):
            setattr(obj, k, v)
    return obj


# ─────────────────────────────────────────────────────────────────────────────
# CLI — self-test
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import json

    SAMPLE = """
Segment: Enterprise FinTech
Fit: High
Priority: P1
Urgency: High
Signal: Series B raise, hiring CFO
Pain: Manual reconciliation, audit exposure
Target Role: CFO
Action: Call
Tone: Direct, high-urgency
Call Hook:
- You just raised Series B — reconciliation will break in 90 days
- New CFO means process rebuild is on the table right now
- We cut audit prep 70% for a team your size in 6 weeks
Email:
  Subject: Reconciliation bottleneck post-Series B
  Opening: Ahmed — saw the Series B close. Congrats.
  Pain: Scaling from 80 → 200 people breaks Excel reconciliation within 90 days.
  Value: We cut audit prep by 70% for FinTechs your size in under 6 weeks.
  CTA: Worth a 15-min call Thursday?
"""

    MESSY = """priority: high
fit - medium
action: Send Email
email
  subject: hey
  opening: saw the news
  cta: book a call?
"""

    for label, text in [("clean", SAMPLE), ("messy", MESSY), ("empty", "")]:
        print(f"\n── {label} ──")
        print(json.dumps(parse_ai_sales_actions(text), indent=2, ensure_ascii=False))
