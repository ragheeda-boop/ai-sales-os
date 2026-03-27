---
name: lead-scoring-analyst
description: "Analyze, calibrate, and improve lead scoring for AI Sales OS. Use this skill when the user asks about lead scores, scoring formula, score distribution, HOT/WARM/COLD classification, why a contact scored high or low, score calibration, Lead Tier assignment, scoring weights, seniority scoring, engagement scoring, or wants to understand or change how leads are prioritized. Also trigger for 'how many HOT leads do we have?' or 'why is this contact HOT?'"
---

# Lead Scoring Analyst — AI Sales OS

You analyze and improve the lead scoring system. Scoring is the intelligence layer — it determines which contacts get attention and which don't. Getting it wrong means wasted effort on the wrong leads.

## Current Formula (v1.1)

```python
Score = Intent(10%) + Engagement(10%) + CompanySize(45%) + Seniority(35%)
```

Each component produces a 0-100 sub-score, then they're combined with weights.

### Why These Weights?

Most contacts are cold Apollo data with no outreach history. Intent and Engagement are mostly empty, so giving them high weight would make scores meaninglessly low. Size and Seniority are available for nearly all records and provide the best signal right now.

### Component Details

**Intent Score (10% weight):**
Takes `max(Primary Intent Score, Secondary Intent Score)`. Currently returns 0 for all contacts because these fields are empty across the entire database. This means 10% of the scoring capacity is unused.

**Engagement Score (10% weight):**
Calculated by `engagement_score()` in `lead_score.py`. Adds points for:
- Meeting Booked: +40
- Replied: +30
- Demoed: +15
- Email Opened: +10
- Email Sent: +5
- Outreach status bonuses (Meeting Booked +15, Replied +12, Opened +8, In Sequence +5, Sent +3)
- Reply status (Positive +20, Replied +10, Neutral +5)
- Qualification status (Qualified +15, In Progress +5)
Capped at 100.

**Company Size Score (45% weight):**
From `employee_score()`:
- 10,000+ → 100
- 5,000-9,999 → 90
- 1,000-4,999 → 80
- 500-999 → 70
- 200-499 → 60
- 50-199 → 45
- 10-49 → 30
- <10 or unknown → 20

**Seniority Score (35% weight):**
From `SENIORITY_SCORES` dict:
- C-Suite/C suite → 100
- Founder → 95, Owner → 95
- Partner → 90
- VP → 85, Head → 80
- Director → 75
- Senior → 65, Manager → 60
- Individual Contributor → 40
- Entry → 25, Intern → 15
- Unknown → 30

## Observed Distribution (from live data)

- **HOT (80+):** 100+ contacts (has_more=True, exact count unknown)
- Average HOT score: 93.5
- 56% of HOT have Score = exactly 100 (ceiling effect)
- 97% of HOT are C-Suite or Director
- HOT with Meeting Booked: 24%, with Replied: 36%
- WARM contacts: majority have Outreach Status = "Sent" only
- Intent Score = 0 on 100% of contacts

## Calibration Targets

| Tier | Target % | Actual |
|------|----------|--------|
| HOT | 0.5-2% | ~0.2% (100/44,875) |
| WARM | 10-20% | Unknown — needs full count |
| COLD | 80%+ | Expected, normal for cold data |

## Known Issues

1. **Ceiling effect:** 56% scoring 100 means the system can't differentiate between truly exceptional leads. This happens because C-Suite (35 points from seniority) + large company (45 points from size) + any engagement = 100.

2. **Intent weight is wasted:** 10% allocated to a component that always returns 0.

3. **Seniority bias:** System heavily favors C-Suite. This may be correct for the business (decision makers matter most), but it means Director-level leads at highly engaged companies might score lower than C-Suite at cold companies.

## Future v2.0 Weights (DO NOT ACTIVATE YET)

```python
Score = Intent(30%) + Engagement(25%) + Signals(25%) + Size(10%) + Seniority(10%)
```

Only switch when:
- Intent Score data is actually populated
- Job postings / job change signals exist
- There's enough outcome data to validate

## Commands

```bash
python lead_score.py              # score unscored contacts only
python lead_score.py --force      # recalculate ALL scores
python lead_score.py --dry-run    # calculate without writing
```

## When Analyzing Scores

1. Always check the distribution first (HOT/WARM/COLD counts)
2. Sample 20-30 HOT leads manually — are they actually high-value?
3. Check if seniority is the dominant driver or if engagement matters
4. Look for ceiling effects (clustering at 100)
5. Compare score with actual outcomes (Meeting Booked, Replied) when available

Always follow the shared rules in `shared-sales-os-rules`.
