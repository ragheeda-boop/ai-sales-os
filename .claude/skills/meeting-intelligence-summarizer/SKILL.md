---
name: meeting-intelligence-summarizer
description: "Turn sales meetings, calls, and conversations into structured intelligence and CRM updates for AI Sales OS. Use this skill when the user shares meeting notes, call transcripts, conversation summaries, or says things like 'I just had a call with...', 'meeting recap', 'what should I do after this meeting?', 'update the CRM from this meeting', or 'summarize this call'. This skill bridges the gap between what happens in real conversations and what the system knows."
---

# Meeting Intelligence Summarizer — AI Sales OS

You turn raw meeting information into structured sales intelligence and actionable CRM updates. This is the most critical human-to-system bridge in the entire pipeline — without it, the system only knows what Apollo tells it, not what actually happened in conversations.

## Why This Matters

The AI Sales OS scoring and automation layer runs on data. But the highest-value data comes from actual human conversations — pain points, buying signals, objections, timelines, decision-maker dynamics. If this data doesn't make it into Notion, the system operates on incomplete information and tasks become disconnected from reality.

## Standard Output Format

For every meeting or call, produce all of the following:

### 1. Meeting Summary (3-5 sentences)
What was discussed, who was present, what was the energy/tone.

### 2. Key Findings
- **Pain points identified:** What problems did the prospect mention?
- **Buying signals:** Anything indicating interest, urgency, or readiness
- **Objections raised:** Concerns, blockers, or pushback
- **Timeline indicators:** When are they looking to move? Budget cycle?
- **Decision dynamics:** Who decides? Who influences? Who blocks?

### 3. Stakeholders
For each person mentioned:
- Name, title, role in decision
- Attitude (champion / neutral / skeptic / blocker)

### 4. CRM Updates to Make
Specific field updates for Notion:

```
Contact: [name]
- Stage → [new stage if changed]
- Qualification Status → [if changed]
- Reply Status → [Positive/Neutral/Negative]
- Contact Responded → True
- Meeting Booked → True (if this was a booked meeting)
- Last Contacted → [today's date]
- Notes: [key quote or insight]
```

### 5. Tasks to Create
For each follow-up needed:

```
Task Title: [action + person + context]
Priority: [Critical/High/Medium]
Due Date: [specific date based on discussion]
Task Type: [Follow-up/Demo/Proposal/Review]
Context: [why this task, based on what was said]
Expected Outcome: [what success looks like]
```

### 6. Opportunity Assessment
- Is this a real opportunity? (Yes / Maybe / No)
- Estimated deal size (if mentioned)
- Likelihood (High / Medium / Low)
- Next milestone

### 7. Follow-up Email Draft
A short, professional follow-up email based on the conversation. Reference specific points discussed. Include a clear next step.

## Notion Fields Available for Updates

From the Contacts database:
- `Stage` — Lead / Prospect / Engaged / Customer
- `Qualification Status` — Qualified / In Progress
- `Reply Status` — Positive / Neutral / Negative
- `Contact Responded` — checkbox
- `Meeting Booked` — checkbox
- `Opportunity Created` — checkbox
- `Last Contacted` — date
- `First Contact Attempt` — date (if this was first contact)

From the Tasks database:
- All task fields are available (see action-engine-builder skill)
- Set `Auto Created = False` for human-created follow-up tasks

## When Processing Meeting Notes

1. Extract every actionable item — don't let anything fall through
2. Be specific about CRM field updates — use exact Notion property names
3. If the meeting reveals the lead should be upgraded or downgraded, say so explicitly
4. If the meeting reveals a new stakeholder, note that they may need their own contact record
5. Always draft a follow-up email — this is the most immediately useful output

## Integration with AI Sales OS

After meeting intelligence is captured:
- Updated `Contact Responded = True` and `Last Contacted` feed back into scoring
- New tasks appear in the sales workflow
- Stage changes affect Action Ready eligibility
- The revenue loop tracker uses `Opportunity Created` to measure conversion

Always follow the shared rules in `shared-sales-os-rules`.
