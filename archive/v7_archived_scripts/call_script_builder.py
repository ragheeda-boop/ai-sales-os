"""
call_script_builder.py — Apollo AI Call Script → structured CALL template

Transforms the raw `Call Script` text from Apollo AI into a clean,
rep-ready structure with:
  • OPENING     — 15-second hook
  • DISCOVERY   — 3 qualifying questions
  • PAIN PITCH  — value mapped to pain points
  • OBJECTIONS  — 3 standard objections with responses
  • CTA         — next step (meeting book / demo)

Output can be written to Notion Tasks.Description or Contacts.Call Script Clean.

Usage:
  from automation.call_script_builder import build_call_script
  template = build_call_script(ai_call_script, pain_points, contact_name, company)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional


OBJECTION_BANK = {
    "budget": (
        "Totally understand. Most clients we work with said the same before "
        "seeing the 3-month ROI. Can I show you the numbers from a similar "
        "company in your space — takes 15 minutes?"
    ),
    "timing": (
        "Makes sense. Would it be easier if I sent you a 2-minute Loom so you "
        "can review it when things calm down, and we reconnect in 2 weeks?"
    ),
    "competitor": (
        "That's great to hear — at least the category is validated. What I'd "
        "love to show you is the one thing we do that no one else does: {diff}. "
        "Worth 10 minutes to see if it's worth a comparison?"
    ),
    "not interested": (
        "Fair enough — I won't push. Before I go, can I ask what would have "
        "had to be true for this to be a yes? That'd help me know whether to "
        "stay in touch or move on."
    ),
    "send email": (
        "Happy to — but so I send the right thing, can I ask just 2 quick "
        "questions about how you handle {pain} today?"
    ),
}


@dataclass
class CallScript:
    opening: str
    discovery: List[str]
    pain_pitch: str
    objections: Dict[str, str]
    cta: str
    short_version: str
    full_markdown: str


def _first_pain(pain_points: str) -> str:
    if not pain_points:
        return "efficiency"
    # Split on common separators
    parts = re.split(r"[,\n•;|]", pain_points)
    for p in parts:
        p = p.strip()
        if len(p) > 3:
            return p.lower()
    return "efficiency"


def _clean_ai_script(raw: str) -> str:
    """Strip markdown artifacts, preserve core sentences."""
    if not raw:
        return ""
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", raw)
    text = re.sub(r"#+ ", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _extract_opening(cleaned: str, contact_name: str, company: str) -> str:
    """Pull first 1-2 sentences; fall back to template."""
    if cleaned:
        sentences = re.split(r"(?<=[.!?])\s+", cleaned)
        if sentences:
            opener = " ".join(sentences[:2]).strip()
            if 20 < len(opener) < 400:
                return opener
    first_name = (contact_name or "there").split()[0]
    return (
        f"Hi {first_name}, this is Ragheed from MUHIDE. I know you weren't "
        f"expecting my call — do you have 30 seconds and I'll tell you exactly "
        f"why I'm calling, and you can tell me if it's worth continuing?"
    )


def _discovery_questions(pain_points: str, industry: str = "") -> List[str]:
    pain = _first_pain(pain_points)
    return [
        f"How are you handling {pain} today — is it a manual process or "
        f"have you already put a system in place?",
        f"When was the last time {pain} actually cost you money or time this "
        f"quarter, and who on your team felt it the most?",
        f"If we could fix this in the next 30 days, what would that mean for "
        f"your numbers this quarter?",
    ]


def _pain_pitch(pain_points: str, message_angle: str, company: str) -> str:
    pain = _first_pain(pain_points)
    angle = (message_angle or "").strip()
    if angle:
        return (
            f"The reason I called {company or 'your team'} specifically: {angle} "
            f"— and the #1 thing we solve for teams like yours is {pain}."
        )
    return (
        f"We work with teams in your space that were struggling with {pain}, "
        f"and we cut it down by 60-80% in the first 90 days — without adding "
        f"headcount. That's the exact reason I wanted to reach out to "
        f"{company or 'you'} today."
    )


def _cta(tier: str = "HOT") -> str:
    if tier == "HOT":
        return (
            "Can I grab 25 minutes on your calendar this week — I'll walk you "
            "through exactly how it would work for your team and you can decide "
            "from there. Does Thursday at 2pm or Friday at 11am work better?"
        )
    return (
        "Would it be useful if I sent you a 2-minute Loom showing how this "
        "works for a team like yours, and we reconnect next week?"
    )


def build_call_script(
    ai_call_script: str,
    pain_points: str,
    contact_name: str = "",
    company: str = "",
    message_angle: str = "",
    industry: str = "",
    tier: str = "HOT",
) -> CallScript:
    """Return a structured CallScript from raw AI inputs."""
    cleaned = _clean_ai_script(ai_call_script)
    opening = _extract_opening(cleaned, contact_name, company)
    discovery = _discovery_questions(pain_points, industry)
    pitch = _pain_pitch(pain_points, message_angle, company)
    cta = _cta(tier)

    pain = _first_pain(pain_points)
    objections = {
        "Budget / too expensive": OBJECTION_BANK["budget"],
        "Bad timing / too busy": OBJECTION_BANK["timing"],
        "Already using a competitor": OBJECTION_BANK["competitor"].replace(
            "{diff}", "integrated execution inside your existing workflow"
        ),
        "Not interested": OBJECTION_BANK["not interested"],
        "Just send me an email": OBJECTION_BANK["send email"].replace(
            "{pain}", pain
        ),
    }

    short = f"{opening}\n\n→ {pitch}\n\n→ {cta}"

    md_parts = [
        f"# Call Script — {contact_name or 'Prospect'} ({company or '-'})",
        "",
        "## 1. Opening (15s)",
        opening,
        "",
        "## 2. Discovery Questions",
        *[f"{i+1}. {q}" for i, q in enumerate(discovery)],
        "",
        "## 3. Pain → Value Pitch",
        pitch,
        "",
        "## 4. Objection Handling",
        *[f"**{k}**\n{v}\n" for k, v in objections.items()],
        "",
        "## 5. CTA — Next Step",
        cta,
        "",
        "---",
        "## SHORT VERSION (if voicemail / <30s)",
        short,
    ]

    return CallScript(
        opening=opening,
        discovery=discovery,
        pain_pitch=pitch,
        objections=objections,
        cta=cta,
        short_version=short,
        full_markdown="\n".join(md_parts),
    )


if __name__ == "__main__":
    demo = build_call_script(
        ai_call_script="Hi {name}, I noticed you're scaling rapidly post-Series B...",
        pain_points="manual reconciliation, excel-based reporting, compliance gaps",
        contact_name="Ahmed Al-Saud",
        company="FinCorp KSA",
        message_angle="You just closed Series B — scaling ops will hit the wall in 90 days without automation",
        tier="HOT",
    )
    print(demo.full_markdown)
