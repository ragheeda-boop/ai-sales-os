"""
ai_sequence_generator.py — Apollo AI Fields → 3-email personalized sequence

Generates role-aware outbound sequences from:
  • Pain Points
  • Message Angle
  • Research Context
  • Buyer Role

Output: 3 emails (Intro, Value Reminder, Break-up) customized per role.

Roles supported: CEO, CFO, COO, CTO, Sales, Ops, Legal, Generic.

Used by:
  • automation/auto_sequence.py — to push custom copy into Apollo Sequences
  • automation/ai_action_executor.py — orchestrator
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Optional


ROLE_PATTERNS = {
    "CEO":   [r"\bceo\b", r"founder", r"chief executive", r"managing director"],
    "CFO":   [r"\bcfo\b", r"finance", r"treasury", r"controller"],
    "COO":   [r"\bcoo\b", r"operations", r"\bops\b"],
    "CTO":   [r"\bcto\b", r"technology", r"engineering", r"\bit\b"],
    "Sales": [r"sales", r"revenue", r"growth", r"business development", r"\bbd\b"],
    "Legal": [r"legal", r"counsel", r"compliance", r"risk"],
}

ROLE_HOOKS = {
    "CEO": {
        "angle": "strategic — growth, margin, competitive position",
        "metric": "revenue per employee, time-to-market",
        "pain_reframe": "the {pain} is quietly eroding your ability to scale past the next stage",
    },
    "CFO": {
        "angle": "financial — cost, risk, reporting accuracy",
        "metric": "days to close, audit prep time, manual reconciliation hours",
        "pain_reframe": "{pain} is currently costing you unreported labor hours and audit exposure",
    },
    "COO": {
        "angle": "operational — throughput, SLA, team capacity",
        "metric": "cycle time, error rate, headcount per transaction",
        "pain_reframe": "{pain} is the #1 throughput bottleneck teams your size hit at scale",
    },
    "CTO": {
        "angle": "technical — integration, reliability, API-first",
        "metric": "uptime, integration coverage, eng-hours saved",
        "pain_reframe": "{pain} means eng is spending cycles on glue code instead of product",
    },
    "Sales": {
        "angle": "pipeline — conversion, speed-to-lead",
        "metric": "close rate, cycle length, pipeline velocity",
        "pain_reframe": "{pain} is the reason reps are losing deals they should win",
    },
    "Legal": {
        "angle": "compliance — audit trail, regulatory, risk",
        "metric": "compliance coverage, audit prep, regulatory deadlines",
        "pain_reframe": "{pain} creates gaps in your audit trail that compound at renewal",
    },
    "Generic": {
        "angle": "efficiency",
        "metric": "time saved, cost reduction, accuracy",
        "pain_reframe": "{pain} is a hidden tax on your team",
    },
}


@dataclass
class EmailSequence:
    role: str
    email_1_subject: str
    email_1_body: str
    email_2_subject: str
    email_2_body: str
    email_3_subject: str
    email_3_body: str

    def as_markdown(self) -> str:
        return (
            f"# Sequence ({self.role})\n\n"
            f"## Email 1\n**Subject:** {self.email_1_subject}\n\n{self.email_1_body}\n\n"
            f"## Email 2 (Day +3)\n**Subject:** {self.email_2_subject}\n\n{self.email_2_body}\n\n"
            f"## Email 3 (Day +7 — break-up)\n**Subject:** {self.email_3_subject}\n\n{self.email_3_body}\n"
        )


def detect_role(title: str, seniority: str = "", buyer_role: str = "") -> str:
    haystack = f"{title} {seniority} {buyer_role}".lower()
    for role, patterns in ROLE_PATTERNS.items():
        if any(re.search(p, haystack) for p in patterns):
            return role
    return "Generic"


def _first_pain(pain_points: str) -> str:
    if not pain_points:
        return "operational efficiency"
    parts = re.split(r"[,\n•;|]", pain_points)
    for p in parts:
        p = p.strip()
        if len(p) > 3:
            return p.lower()
    return "operational efficiency"


def _research_one_liner(research_context: str) -> str:
    if not research_context:
        return ""
    sentences = re.split(r"(?<=[.!?])\s+", research_context.strip())
    if sentences:
        return sentences[0].strip().rstrip(".") + "."
    return ""


def generate_sequence(
    contact_name: str,
    company: str,
    title: str,
    pain_points: str = "",
    message_angle: str = "",
    research_context: str = "",
    seniority: str = "",
    buyer_role: str = "",
) -> EmailSequence:
    role = detect_role(title, seniority, buyer_role)
    hook = ROLE_HOOKS.get(role, ROLE_HOOKS["Generic"])
    first_name = (contact_name or "there").split()[0]
    pain = _first_pain(pain_points)
    research_line = _research_one_liner(research_context)
    angle_line = (message_angle or hook["angle"]).strip()

    # ── Email 1 — Intro (relevance + hook) ──
    e1_subj = f"{first_name} — quick thought on {pain}"
    e1_body = (
        f"Hi {first_name},\n\n"
        f"{research_line + ' ' if research_line else ''}"
        f"The reason I'm reaching out: most {role.lower() if role != 'Generic' else 'leaders'} "
        f"at companies like {company} tell us the same thing — "
        f"{hook['pain_reframe'].format(pain=pain)}.\n\n"
        f"{angle_line}\n\n"
        f"We help teams measure this in {hook['metric']}. Worth a 15-min call "
        f"next week to see if it applies to {company}?\n\n"
        f"— Ragheed\nMUHIDE"
    )

    # ── Email 2 — Value reminder (proof + specificity) ──
    e2_subj = f"Re: {first_name} — 3 numbers from a similar team"
    e2_body = (
        f"Hi {first_name},\n\n"
        f"Quick follow-up. I don't want to waste your inbox, so here's the "
        f"shortest version: a team in your space fixed {pain} and saw:\n\n"
        f"  • 60% reduction in {hook['metric'].split(',')[0]}\n"
        f"  • 2-week payback on the rollout\n"
        f"  • Zero additional headcount required\n\n"
        f"Same playbook would apply to {company}. Worth 15 minutes?\n\n"
        f"— Ragheed"
    )

    # ── Email 3 — Break-up (permission to close loop) ──
    e3_subj = f"Closing the loop, {first_name}"
    e3_body = (
        f"Hi {first_name},\n\n"
        f"I don't want to keep filling your inbox, so this is my last note "
        f"unless you tell me otherwise.\n\n"
        f"If {pain} isn't a priority right now, no problem — just reply "
        f"\"not now\" and I'll circle back in Q3. If it is, reply \"yes\" "
        f"and I'll send you a 15-minute slot.\n\n"
        f"Either way, thanks for reading.\n\n"
        f"— Ragheed"
    )

    return EmailSequence(
        role=role,
        email_1_subject=e1_subj, email_1_body=e1_body,
        email_2_subject=e2_subj, email_2_body=e2_body,
        email_3_subject=e3_subj, email_3_body=e3_body,
    )


if __name__ == "__main__":
    seq = generate_sequence(
        contact_name="Ahmed Al-Saud",
        company="FinCorp KSA",
        title="Chief Financial Officer",
        pain_points="manual reconciliation, excel-based reporting, audit prep time",
        message_angle="You just closed Series B — the reconciliation process will break within 90 days",
        research_context="FinCorp raised $40M Series B last month and announced expansion into UAE.",
    )
    print(seq.as_markdown())
