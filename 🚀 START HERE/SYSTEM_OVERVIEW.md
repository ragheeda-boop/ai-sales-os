# AI Sales OS v4.0 — System Overview

## Architecture

```
┌──────────────┐     ┌──────────────────────────┐     ┌──────────────┐     ┌───────────────┐
│  Apollo.io   │────►│  Python Scripts (15)      │────►│   Notion     │────►│ GitHub Actions│
│  (Data)      │     │  Sync + Enrich + Score +  │     │  (CRM Hub)   │     │ (Daily Cron)  │
└──────────────┘     │  Action + Sequence + Learn│     └──────────────┘     └───────────────┘
 44,875 contacts     └──────────────────────────┘      7 Databases          14-step pipeline
 15,407 companies                                      HOT/WARM/COLD Views  + weekly calibration
```

## Autonomous Sales Loop (v4.0)

```
Score → Task → Sequence → Track → Calibrate → Better Score
  ↑                                               │
  └───────────────────────────────────────────────┘
```

The system runs itself. Your job is to close deals, not manage data.

## Data Pipeline

```
Apollo API
    │
    ▼
daily_sync.py (v2.1)
    ├─ Fetch contacts (contacts/search)
    │  ├─ Triple dedup (Apollo ID + Email + seen_ids)
    │  ├─ Normalize seniority & engagement booleans
    │  ├─ Link to Company (by Apollo Account ID)
    │  └─ Create or Update in Notion
    │
    ├─ Fetch companies (accounts/search)
    │  ├─ Dedup by Apollo Account ID
    │  └─ Create or Update in Notion
    │
    └─ 3 Modes:
       ├─ incremental (last N hours/days, daily use)
       ├─ backfill (historical, with checkpoint resume)
       └─ full (all records, alphabetical partitioning)
    │
    ▼
job_postings_enricher.py (v4.0)
    ├─ Fetch job postings from Apollo for HOT/WARM companies
    ├─ Score intent (0-100): Volume + Recency + Relevance + Growth
    ├─ Write "Job Postings Intent" to Companies DB
    └─ Propagate to linked Contacts' "Primary Intent Score"
    │
    ▼
lead_score.py (v1.1)
    ├─ Intent Score x 10% (from Apollo)
    ├─ Engagement x 10% (email/meeting activity)
    ├─ Company Size x 45% (employee count)
    └─ Seniority x 35% (job level)
    │
    ├─ Output: Lead Score (0-100) + Lead Tier (HOT/WARM/COLD)
    │
    ▼
action_ready_updater.py
    ├─ Evaluate 5 conditions:
    │  ├─ Score >= 50
    │  ├─ Do Not Call = False
    │  ├─ Outreach Status NOT (Do Not Contact | Bounced | Bad Data)
    │  ├─ Stage NOT (Customer | Churned)
    │  └─ Has email OR phone
    │
    └─ Set Action Ready checkbox
    │
    ▼
auto_tasks.py (Action Engine)
    ├─ HOT leads (Score >= 80)
    │  └─ Create CALL task (SLA: 24 hours, Priority: Critical)
    │
    └─ WARM leads (Score 50-79)
       └─ Create FOLLOW-UP task (SLA: 48 hours, Priority: High)
    │
    ▼
auto_sequence.py (v4.0)
    ├─ Map (Tier, Role) → Apollo Sequence
    ├─ Role detection: CEO, CFO, Sales, Legal, General
    ├─ Round-robin sender rotation (ragheed, ibrahim)
    └─ Update Outreach Status → "In Sequence"
    │
    ▼
analytics_tracker.py (v4.0)
    ├─ Pull engagement data from Apollo
    ├─ Update Notion: Replied, Email Opened, Email Sent
    └─ Generate analytics report (seniority, size, trends)
    │
    ▼
health_check.py
    ├─ Check sync stats (zero records = CRITICAL)
    ├─ Check duplicate rate (>5% = WARNING)
    ├─ Check action engine errors
    └─ Validate pipeline health
    │
    ▼
morning_brief.py (v4.0)
    ├─ Urgent Calls: HOT leads not contacted
    ├─ Today's Tasks: Due today + overdue
    ├─ Recent Replies: Contacts that responded
    ├─ Pipeline Summary: HOT/WARM/COLD counts
    └─ Email Performance: Last 7 days
    │
    ▼  (Weekly — Sundays)
score_calibrator.py (v4.0)
    ├─ Analyze outcomes vs assigned scores
    ├─ Detect OVERSCORED / UNDERSCORED patterns
    ├─ Recommend weight adjustments
    └─ Safety: max 10% change per cycle, min 5% per component
    │
    ▼
Notion Views
    ├─ HOT LEADS (Score >= 80) → 24h CALL tasks + sequence enrollment
    ├─ WARM LEADS (Score 50-79) → 48h FOLLOW-UP tasks + email sequences
    └─ COLD LEADS (Score < 50) → Monitor only
```

## Notion Databases

| Database | Records | Key Fields |
|----------|---------|------------|
| **Contacts** | 44,875 | Name, Email, Title, Seniority, Lead Score, Lead Tier, Action Ready, Intent Score, Outreach Status |
| **Companies** | 15,407 | Name, Domain, Industry, Employee Count, Job Postings Intent, Apollo Account ID |
| **Tasks** | Active | Title, Priority, Status (status type), Due Date, Contact, Company, Auto Created |
| **Opportunities** | Active | Name, Value, Stage, Company, Contact, Deal Health |
| **Meetings** | Active | Date, Attendees, Status, Outcome |
| **Campaigns** | Active | Apollo Sequences (24 total across tiers and roles) |
| **Email Hub** | Active | Subject, Status, Contact |

## Key Technical Details

**Sync Engine:** daily_sync.py handles Apollo's 50,000 record pagination limit using time-window splitting (incremental/backfill) and alphabetical partitioning (full mode). Built-in retry with 5x exponential backoff.

**Dedup Strategy:** Triple dedup prevents duplicates — checks Apollo ID, then Email, then in-memory seen_ids set. Pre-loads all existing Notion records before sync to minimize API calls.

**Lead Score:** Calculated by lead_score.py using 4 weighted components. Score range 0-100. 80% COLD is normal for cold Apollo data — this is expected, not a problem.

**Intent Proxy:** job_postings_enricher.py uses Apollo Job Postings API to score company hiring intent (0-100). Companies actively hiring in relevant roles = higher buying intent.

**Auto Sequences:** auto_sequence.py maps (Lead Tier, Role Category) → specific Apollo sequence. 24 sequences total across 2 tiers x 5 roles x sender variants.

**Self-Learning:** score_calibrator.py analyzes actual engagement outcomes and recommends weight adjustments. Safety rails prevent sudden jumps (max 10% change per cycle).

**Automation:** GitHub Actions runs 14-step pipeline daily + weekly calibration. No external tools (n8n, Make, Zapier). Pure Python + GitHub Actions.

## Execution Plan (v4.0)

| Phase | Name | Status |
|-------|------|--------|
| Phase 1 | **ACTIVATE** — Full Sync + Lead Score + Calibration | Complete |
| Phase 2 | **ACTION** — auto_tasks.py + Action Ready + Health Check | Complete |
| Phase 3 | **ENRICH** — Job Postings + Sequences + Analytics + Calibration | Complete (v4.0) |
| Phase 4 | **OPTIMIZE** — Odoo ERP + Revenue Tracking + Advanced Analytics | Planned |

Full details in `📚 DOCUMENTATION/EXECUTION_PLAN_v3.2.docx`

---
**Version:** 4.0 | **Last Updated:** 28 March 2026 | **Owner:** Ragheed
