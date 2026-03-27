---
name: apollo-sequence-builder
description: "Create outbound sales sequences, email copy, LinkedIn messages, and call scripts for AI Sales OS. Use this skill when the user wants to write sales emails, outbound sequences, follow-up messages, cold outreach, LinkedIn messages, call scripts, or asks things like 'write me a sequence for CEOs', 'draft a follow-up email', 'what should I say to this lead?', or 'create messaging for this segment'. Also trigger for A/B test copy variants or any sales messaging work."
---

# Apollo Sequence Builder — AI Sales OS

You create outbound sales messaging that converts. The scoring system identifies who to contact — this skill determines what to say and how to say it.

## Context: Where Messaging Fits

```
ICP (who to target) → Score (who's ready) → Action (task created) → Sequence (what to say) → Outcome (response)
```

Every sequence should be informed by what we know about the lead from Notion:
- Lead Score and Tier (urgency level)
- Seniority (tone and framing)
- Industry / Company Size (relevance)
- Engagement history (what they've already seen)
- Outreach Status (where they are in the journey)

## Sequence Design Principles

### Structure
A standard outbound sequence has 5-7 touches across 2-3 weeks:

| Touch | Channel | Timing | Purpose |
|-------|---------|--------|---------|
| 1 | Email | Day 0 | Open the conversation |
| 2 | LinkedIn | Day 2 | Social proof / different channel |
| 3 | Email | Day 4 | New angle, add value |
| 4 | Call | Day 7 | Direct conversation attempt |
| 5 | Email | Day 10 | Case study or proof point |
| 6 | LinkedIn | Day 14 | Breakup / last value offer |
| 7 | Email | Day 18 | Breakup email |

### Writing Style
- **Executive tone:** Confident, direct, no fluff
- **Business-first:** Lead with the problem, not the product
- **Short:** Emails under 100 words, LinkedIn under 50
- **Specific:** Reference their industry, company size, or role
- **Clear CTA:** One ask per message, low friction

### Persona Adaptation

**CEO / Founder:**
Focus on: strategic growth, market control, competitive advantage, revenue predictability
Tone: Peer-to-peer, strategic, respect their time

**CFO / Finance:**
Focus on: cash flow impact, risk reduction, financial visibility, working capital
Tone: Numbers-driven, precise, ROI-oriented

**VP Sales / Sales Director:**
Focus on: win rates, conversion improvement, pipeline velocity, team efficiency
Tone: Results-oriented, practical, metric-based

**Director / Manager:**
Focus on: operational efficiency, time savings, process improvement
Tone: Helpful, solution-oriented, collaborative

### CTA Rules
Always use low-friction CTAs:
- "Worth a 15-minute look?"
- "Open to a quick comparison with your current process?"
- "Would it make sense to explore this?"
- "Happy to share how [similar company] handled this"

Never use high-pressure CTAs like "Book a demo now" or "Ready to get started?"

## Output Format for Sequences

For each sequence provide:

1. **Sequence name and goal**
2. **Target persona** (seniority + department + industry)
3. **Trigger** (what makes now the right time)
4. **Emails** (subject line + body for each touch)
5. **LinkedIn messages** (connection request + follow-ups)
6. **Call opener** (first 30 seconds script)
7. **Objection responses** (top 3-5 objections with answers)
8. **Personalization variables** (what to customize per lead)

## What NOT to Do

- Don't write generic "just checking in" follow-ups
- Don't use hype words (revolutionary, game-changing, disruptive)
- Don't over-personalize to the point of being creepy
- Don't ignore the prospect's likely objections
- Don't make the email about you — make it about their problem
- Don't use overly casual language for C-Suite targets
- Don't write walls of text — short paragraphs, clear structure

## Integration with AI Sales OS

When the Action Engine creates a task for a HOT lead:
- The task includes Context explaining why the lead is HOT
- Use that context to select the right sequence and personalize it
- Match the Channel recommendation (Phone for HOT, Email for WARM)
- Respect the SLA deadline (24h for HOT, 48h for WARM)

Always follow the shared rules in `shared-sales-os-rules`.
