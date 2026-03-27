---
name: revenue-loop-tracker
description: "Track and analyze the revenue feedback loop — from lead score to action to outcome to revenue. Use this skill when the user asks about conversion rates, meeting rates, pipeline performance, 'are HOT leads actually converting?', 'what happened after we contacted them?', outcome tracking, feedback loop analysis, score-to-revenue correlation, or wants to understand if the scoring system is actually working. Also trigger for ROI analysis of the sales pipeline."
---

# Revenue Loop Tracker — AI Sales OS

You track whether the intelligence layer (scoring) actually produces business results. This is the feedback loop that closes the gap between "we identified a lead" and "we closed a deal."

## The Revenue Loop

```
Score → Tier → Action Ready → Task Created → Contact Attempted → Response → Meeting → Opportunity → Revenue
```

Right now the system handles the left side well (Score → Task). Your job is to track and analyze the right side (Contact → Revenue) and feed insights back to improve scoring.

## Tracking Fields (in Contacts Database)

| Field | Type | Purpose |
|-------|------|---------|
| Lead Score | number | Starting intelligence |
| Lead Tier | select | HOT / WARM / COLD |
| Action Ready | checkbox | Gating for task creation |
| First Contact Attempt | date | When first outreach happened |
| Last Contacted | date | Most recent outreach |
| Contact Responded | checkbox | Did they reply? |
| Meeting Booked | checkbox | Was a meeting scheduled? |
| Opportunity Created | checkbox | Did this become a real opportunity? |
| Outreach Status | select | Current outreach state |
| Reply Status | select | Quality of response |
| Qualification Status | select | Sales qualification level |

## Current Baseline (March 2026)

From the first 100 HOT contacts:
- **Meeting Booked = True:** 24 contacts (24%)
- **Replied = True:** ~36 contacts (~36%)
- **Outreach Status "Replied":** 36 contacts
- **Outreach Status "Meeting Booked":** 24 contacts
- **Qualification Status "Qualified":** ~99%
- **Opportunity Created:** Not yet tracked (field just added)
- **Tasks created:** 0 at baseline (auto_tasks newly built)

## KPIs to Track

### Conversion Funnel by Tier

For each tier (HOT / WARM / COLD), measure:

| Stage | KPI | Target |
|-------|-----|--------|
| Task Created → First Contact | Contact Rate | 90%+ for HOT |
| First Contact → Response | Response Rate | 20%+ for HOT |
| Response → Meeting | Meeting Rate | 10%+ for HOT |
| Meeting → Opportunity | Opportunity Rate | 5%+ |
| Opportunity → Close | Win Rate | TBD |

### SLA Compliance

| Tier | SLA | Metric |
|------|-----|--------|
| HOT | 24 hours | % of HOT tasks with first contact within 24h |
| WARM | 48 hours | % of WARM tasks with first contact within 48h |

### Scoring Accuracy

The most important long-term metric:
- Do HOT leads convert better than WARM?
- Do WARM convert better than COLD?
- If not, the scoring formula needs recalibration.

## How to Analyze

### Quick Health Check
1. Count contacts by Lead Tier
2. For each tier, count: Contact Responded = True, Meeting Booked = True, Opportunity Created = True
3. Calculate conversion rates per tier
4. Compare across tiers — is HOT actually better?

### Score Correlation Analysis
1. Group contacts by score ranges (90-100, 80-89, 70-79, 60-69, 50-59)
2. For each range, calculate response rate and meeting rate
3. Plot or compare — higher scores should correlate with better outcomes
4. If they don't, the scoring weights need adjustment

### Time Analysis
1. Calculate average days from Task Created to First Contact Attempt
2. Compare against SLA (24h for HOT, 48h for WARM)
3. Calculate average days from First Contact to Meeting
4. Identify bottlenecks — where does the pipeline slow down?

## When Reporting

Always structure findings as:
1. **Executive summary:** One sentence — is the pipeline healthy?
2. **Funnel metrics:** Conversion rates at each stage
3. **Score validation:** Does score predict outcomes?
4. **Bottlenecks:** Where leads stall or drop out
5. **Recommendations:** What to change (scoring weights, SLA, targeting)

## Feeding Back to Scoring

After 4-8 weeks of outcome data:
- If C-Suite converts much better → seniority weight is correct
- If large companies convert better → company size weight is correct
- If engaged contacts (replied/opened) convert better → increase engagement weight
- If Intent data becomes available and correlates → increase intent weight
- If no difference between HOT and WARM → scoring needs fundamental rework

Always follow the shared rules in `shared-sales-os-rules`.
