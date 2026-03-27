# AI Sales OS — System Overview

## Architecture

```
┌──────────────┐     ┌──────────────────────────┐     ┌──────────────┐     ┌───────────────┐
│  Apollo.io   │────►│  Python Scripts           │────►│   Notion     │────►│ GitHub Actions│
│  (Data)      │     │  (Sync + Score + Action)  │     │  (CRM Hub)   │     │ (Daily Cron)  │
└──────────────┘     └──────────────────────────┘     └──────────────┘     └───────────────┘
 44,875 contacts      daily_sync.py v2.1               7 Databases          7 AM KSA daily
 15,407 companies     lead_score.py v1.1               HOT/WARM/COLD Views  10-step pipeline
                     action_ready_updater.py
                     auto_tasks.py
                     health_check.py
```

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
lead_score.py (v1.1)
    ├─ Intent Score × 10% (from Apollo)
    ├─ Engagement × 10% (email/meeting activity)
    ├─ Company Size × 45% (employee count)
    └─ Seniority × 35% (job level)
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
    └─ Set Action Ready checkbox ✓
    │
    ▼
auto_tasks.py (Action Engine)
    ├─ HOT leads (Score >= 80)
    │  └─ Create CALL task (SLA: 24 hours)
    │
    └─ WARM leads (Score 50-79)
       └─ Create FOLLOW-UP task (SLA: 48 hours)
    │
    ▼
health_check.py
    ├─ Check sync stats (zero records = CRITICAL)
    ├─ Check duplicate rate (>5% = WARNING)
    ├─ Check action engine errors
    └─ Validate pipeline health
    │
    ▼
Notion Views
    ├─ HOT LEADS (Score >= 80) → 24h CALL tasks
    ├─ WARM LEADS (Score 50-79) → 48h FOLLOW-UP tasks
    └─ COLD LEADS (Score < 50) → Monitor only
```

## Notion Databases

| Database | Records | Key Fields |
|----------|---------|------------|
| **Companies** | 15,407 | Name, Domain, Industry, Employee Count, Apollo Account ID |
| **Contacts** | 44,875 | Name, Email, Title, Seniority, Lead Score, Intent Score, Company (relation) |
| **Opportunities** | — | Name, Value, Stage, Company, Contact |
| **Tasks** | — | Title, Priority, Due Date, Contact, Company |
| **Meetings** | — | Date, Attendees, Status |
| **Activities** | — | Type, Date, Contact |
| **Email Hub** | — | Subject, Status, Contact |

## Key Technical Details

**Sync Engine:** daily_sync.py handles Apollo's 50,000 record pagination limit using time-window splitting (incremental/backfill) and alphabetical partitioning (full mode). Built-in retry with 5x exponential backoff.

**Dedup Strategy:** Triple dedup prevents duplicates — checks Apollo ID, then Email, then in-memory seen_ids set. Pre-loads all existing Notion records before sync to minimize API calls.

**Lead Score:** Calculated by lead_score.py using 4 weighted components. Score range 0-100. Contacts with no outreach history (majority) will score low — this is expected behavior for cold Apollo data.

**Automation:** GitHub Actions runs daily pipeline (sync → score). No external tools (n8n, Make, Zapier). Pure Python + GitHub Actions.

## Execution Plan (v3.2)

| Phase | Name | Status |
|-------|------|--------|
| Phase 1 | **ACTIVATE** — Full Sync + Lead Score + Calibration | Complete |
| Phase 2 | **ACTION** — auto_tasks.py + Action Ready + Health Check | Code Complete |
| Phase 3 | **ENRICH** — Job Postings + Job Change + Intent Trend | Next |
| Phase 4 | **OPTIMIZE** — Lead Score v2.0 + Odoo Integration | Future |

Full details in `📚 DOCUMENTATION/EXECUTION_PLAN_v3.2.docx`

---
**Version:** 3.2 | **Last Updated:** 27 March 2026 | **Owner:** Ragheed
