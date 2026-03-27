# AI Sales OS v3.2

**Apollo + Notion + Python + GitHub Actions** — Production-grade sales operating system.

44,875 contacts | 15,407 companies | 3 sync modes | Lead scoring (0-100) | SLA-based task automation | Health checks

## Architecture

```
Apollo.io  ──►  Python Engine  ──►  Notion  ──►  GitHub Actions  ──►  Odoo (Phase 4)
(Data)          (Sync + Score)     (CRM Hub)    (Daily Cron)        (ERP)
```

**Design:** No middleware. Pure Python + GitHub Actions = full control, zero cost.

## Quick Start

```bash
# 1. Configure credentials
cd "💻 CODE/Phase 3 - Sync"
cp .env.example .env
# Edit .env with your API keys

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run full sync (first time)
python daily_sync.py --mode full

# 4. Calculate lead scores
python lead_score.py --force

# 5. Daily sync (after initial setup)
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
Score = (Intent × 10%) + (Engagement × 10%) + (Company Size × 45%) + (Seniority × 35%)
```

**Why?** Intent and Engagement are sparse in cold Apollo data. Size and Seniority are available for nearly all records.

| Tier | Score | Action | SLA |
|------|-------|--------|-----|
| **HOT** | >= 80 | CALL today | 24 hours |
| **WARM** | 50-79 | FOLLOW-UP email | 48 hours |
| **COLD** | < 50 | Monitor only | — |

**Future v2.0 weights** (activate only when signals data exists): Intent(30%) + Engagement(25%) + Signals(25%) + Size(10%) + Seniority(10%)

## Folder Structure

```
AI Sales OS/
├── 💻 CODE/Phase 3 - Sync/       → Production scripts (all 9 core engines)
│   ├── daily_sync.py              → Sync engine v2.1 (incremental/backfill/full)
│   ├── lead_score.py              → Lead scorer + Lead Tier writer
│   ├── constants.py               → Unified field names, thresholds, SLA hours
│   ├── action_ready_updater.py    → 5-condition Action Ready evaluator
│   ├── auto_tasks.py              → SLA-based task automation
│   ├── health_check.py            → Post-pipeline health validator
│   ├── notion_helpers.py          → Shared Notion API utilities
│   ├── webhook_server.py          → Apollo webhook receiver
│   ├── verify_links.py            → Contact-company link verifier
│   ├── requirements.txt           → Python dependencies
│   ├── .env                       → API credentials (not in git)
│   └── .env.example               → Credential template
├── .claude/skills/                → 12 Claude Skills (claude.ai evaluate)
├── packaged-skills/               → Distributed skill packages
├── 📊 DATA/                       → CSVs, mappings, snapshots, logs
├── 📚 DOCUMENTATION/              → EXECUTION_PLAN_v3.2.docx, phase docs
├── .github/workflows/             → daily_sync.yml (10-step CI/CD pipeline)
├── 🚀 START HERE/                 → Quick start & system overview
├── AI_Sales_OS_MindMap.html       → Interactive mind map v4.0
└── 🗂️ ARCHIVED/                  → Superseded scripts
```

## GitHub Actions Pipeline

**Schedule:** Daily at 7:00 AM KSA (04:00 UTC) | **Manual trigger:** Available from UI

**10-step pipeline:**
1. Checkout code
2. Setup Python 3.11 + cache
3. Install dependencies
4. `daily_sync.py --mode incremental --hours 26` (sync)
5. `lead_score.py` (score + Lead Tier)
6. `action_ready_updater.py` (evaluate Action Ready)
7. `auto_tasks.py` (create tasks for qualified leads)
8. `health_check.py` (validate results)
9. Upload logs (30-day retention)
10. Notify on failure

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
| **Phase 1: ACTIVATE** | COMPLETE | Full sync, scoring, seniority normalization, safe booleans all working |
| **Phase 2: ACTION** | CODE COMPLETE | auto_tasks.py + action_ready_updater.py built; first run pending |
| **Phase 3: ENRICH** | NEXT | Job postings, job change detection, intent trends, v2.0 weights |
| **Phase 4: OPTIMIZE** | Planned | Odoo ERP integration, revenue tracking, advanced analytics |

**Claude Skills:** 12 built and evaluated (.claude/skills/ directory)

**Version:** 3.2 | **Updated:** 27 March 2026 | **Contacts:** 44,875 | **Companies:** 15,407

**Full documentation:** See `EXECUTION_PLAN_v3.2.docx` or open `AI_Sales_OS_MindMap.html`
