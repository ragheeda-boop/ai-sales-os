# AI Sales OS v4.0

**Apollo + Notion + Python + GitHub Actions** — Autonomous Sales Operating System.

44,875 contacts | 15,407 companies | 15 production scripts | Autonomous Loop | Self-learning scoring

## Architecture

```
Apollo.io  ──►  Python Engine (15 scripts)  ──►  Notion  ──►  GitHub Actions  ──►  Odoo (Phase 4)
(Data)          Sync + Enrich + Score +          (CRM Hub)    14-step pipeline      (ERP)
                Action + Sequence + Learn         7 DBs        + weekly calibration
```

**Autonomous Loop:** Score → Task → Sequence → Track → Calibrate → Better Score

**Design:** No middleware. No n8n, no Make.com, no Zapier. Pure Python + GitHub Actions = full control, zero cost.

## Quick Start

```bash
# 1. Configure credentials
cd "💻 CODE/Phase 3 - Sync"
cp .env.example .env
# Edit .env with your API keys

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run full sync (first time — 2-4 hours)
python daily_sync.py --mode full

# 4. Enrich companies with job postings intent
python job_postings_enricher.py --limit 50

# 5. Calculate lead scores + assign tiers
python lead_score.py --force

# 6. Set Action Ready flags
python action_ready_updater.py

# 7. Create SLA-based tasks
python auto_tasks.py

# 8. Enroll in Apollo sequences
python auto_sequence.py --dry-run

# 9. Validate pipeline
python health_check.py

# 10. Daily sync (after setup)
python daily_sync.py --mode incremental --days 1
```

## Core Scripts

| Script | Purpose | Status |
|--------|---------|--------|
| `daily_sync.py` | Apollo → Notion sync (v2.1, 3 modes) | **ACTIVE** |
| `lead_score.py` | Lead Score (0-100) + Lead Tier (HOT/WARM/COLD) | **ACTIVE** |
| `constants.py` | Unified field names, thresholds, SLA hours | **ACTIVE** |
| `action_ready_updater.py` | 5-condition Action Ready evaluator | **ACTIVE** |
| `auto_tasks.py` | SLA-based task automation engine | **ACTIVE** |
| `health_check.py` | Post-pipeline health validator | **ACTIVE** |
| `notion_helpers.py` | Shared Notion API utilities | **ACTIVE** |
| `job_postings_enricher.py` | Intent proxy — Apollo Job Postings API | **ACTIVE (v4.0)** |
| `auto_sequence.py` | Auto-enroll contacts in Apollo Sequences | **ACTIVE (v4.0)** |
| `analytics_tracker.py` | Apollo Analytics → Notion engagement sync | **ACTIVE (v4.0)** |
| `score_calibrator.py` | Self-learning weight adjustment | **ACTIVE (v4.0)** |
| `morning_brief.py` | Daily intelligence report generator | **ACTIVE (v4.0)** |
| `webhook_server.py` | Apollo webhook receiver | **ACTIVE** |
| `verify_links.py` | Contact-company link verifier | **ACTIVE** |

## Sync Modes

| Mode | Description | When to Use |
|------|-------------|-------------|
| **incremental** | Last N hours/days | Daily automated sync |
| **backfill** | Historical with checkpoint | Gap recovery, catch-up |
| **full** | All records (alphabetical partitioning) | First-time setup, full rebuild |

## Lead Score Formula (v1.1 — current)

```
Score = (Intent x 10%) + (Engagement x 10%) + (Company Size x 45%) + (Seniority x 35%)
```

**Why?** Intent and Engagement are sparse in cold Apollo data. Size and Seniority are available for nearly all records.

| Tier | Score | Action | SLA |
|------|-------|--------|-----|
| **HOT** | >= 80 | CALL today | 24 hours |
| **WARM** | 50-79 | FOLLOW-UP email | 48 hours |
| **COLD** | < 50 | Monitor only | — |

**Future v2.0 weights** (activate only when signals data exists): Intent(30%) + Engagement(25%) + Signals(25%) + Size(10%) + Seniority(10%)

## v4.0 — Autonomous Loop

The system runs itself. Every morning at 7:00 AM KSA, the pipeline automatically:

1. **Sync** — Pulls new/updated records from Apollo
2. **Enrich** — Job postings intent scoring for companies
3. **Score** — Calculates Lead Score (0-100) + assigns Lead Tier
4. **Gate** — Evaluates 5-condition Action Ready check
5. **Task** — Creates SLA-based tasks for HOT/WARM leads
6. **Sequence** — Auto-enrolls contacts in Apollo email sequences
7. **Track** — Syncs engagement data (opens, replies, bounces) back from Apollo
8. **Brief** — Generates daily morning intelligence report

**Weekly (Sundays):** Self-learning calibration analyzes outcomes and recommends weight adjustments.

## Folder Structure

```
AI Sales OS/
├── 💻 CODE/Phase 3 - Sync/       → All 15 production scripts
│   ├── daily_sync.py              → Sync engine v2.1 (3 modes)
│   ├── lead_score.py              → Lead scorer + Lead Tier writer
│   ├── constants.py               → Unified field names & thresholds
│   ├── action_ready_updater.py    → 5-condition Action Ready evaluator
│   ├── auto_tasks.py              → Action Engine (SLA task creator)
│   ├── health_check.py            → Pipeline health validator
│   ├── notion_helpers.py          → Shared Notion API utilities
│   ├── job_postings_enricher.py   → Intent proxy (Job Postings API) [v4.0]
│   ├── auto_sequence.py           → Apollo Sequence enrollment [v4.0]
│   ├── analytics_tracker.py       → Engagement sync from Apollo [v4.0]
│   ├── score_calibrator.py        → Self-learning weight adjustment [v4.0]
│   ├── morning_brief.py           → Daily intelligence report [v4.0]
│   ├── webhook_server.py          → Apollo webhook receiver
│   ├── verify_links.py            → Contact-company link verifier
│   ├── requirements.txt           → Python dependencies
│   ├── .env.example               → Credential template
│   └── .env                       → API credentials (not in git)
├── .claude/skills/                → 12 Claude Skills for operations
├── .github/workflows/             → daily_sync.yml (14-step pipeline + weekly calibration)
├── 📊 DATA/                       → CSVs, mappings, snapshots, logs
├── 📚 DOCUMENTATION/              → EXECUTION_PLAN_v3.2.docx + phase docs
├── 🚀 START HERE/                 → Quick start & system overview
├── AI_Sales_OS_MindMap.html       → Interactive mind map v6.0 (Arabic)
└── 🗂️ ARCHIVED/                  → Superseded files
```

## GitHub Actions Pipeline

**Schedule:** Daily at 7:00 AM KSA (04:00 UTC) | **Manual trigger:** Available from UI

**14-step pipeline:**
1. Checkout code
2. Setup Python 3.11 + cache
3. Install dependencies
4. `daily_sync.py --mode incremental --hours 26` (sync)
5. `job_postings_enricher.py --limit 50` (intent enrichment)
6. `lead_score.py` (score + Lead Tier)
7. `action_ready_updater.py` (evaluate Action Ready)
8. `auto_tasks.py` (create SLA tasks)
9. `auto_sequence.py --limit 50` (sequence enrollment)
10. `analytics_tracker.py --days 7` (engagement sync)
11. `health_check.py` (validate pipeline)
12. `morning_brief.py --output file` (daily report)
13. Upload logs (30-day retention)
14. Notify on failure

**Weekly (Sundays):** `score_calibrator.py --days 30 --export` (review-only, no auto-apply)

**Required Secrets (5 total):**
- `APOLLO_API_KEY`
- `NOTION_API_KEY`
- `NOTION_DATABASE_ID_CONTACTS`
- `NOTION_DATABASE_ID_COMPANIES`
- `NOTION_DATABASE_ID_TASKS`

**Cost:** ~450 min/month (free tier = 2,000 min/month)

## Execution Status

| Phase | Status | Details |
|-------|--------|---------|
| **Phase 1: ACTIVATE** | COMPLETE | Full sync, scoring, seniority normalization, safe booleans |
| **Phase 2: ACTION** | COMPLETE | auto_tasks.py + action_ready_updater.py + health_check.py |
| **Phase 3: ENRICH** | COMPLETE (v4.0) | Job postings, auto sequences, analytics tracking, self-learning calibration |
| **Phase 4: OPTIMIZE** | Planned | Odoo ERP integration, revenue tracking, advanced analytics |

**Claude Skills:** 12 built and evaluated at 100% pass rate (.claude/skills/ directory)

**Version:** 4.0 | **Updated:** 28 March 2026 | **Contacts:** 44,875 | **Companies:** 15,407

**Full documentation:** See `EXECUTION_PLAN_v3.2.docx` or open `AI_Sales_OS_MindMap.html`
