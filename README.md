# AI Sales OS v4.3

**Apollo + Notion + Python + GitHub Actions** — Autonomous Sales Operating System.

44,875 contacts | 15,407 companies | 19 production scripts | Autonomous Loop | Self-learning scoring | Live Dashboard

[![Daily Pipeline](https://github.com/ragheeda-boop/ai-sales-os/actions/workflows/daily_sync.yml/badge.svg)](https://github.com/ragheeda-boop/ai-sales-os/actions/workflows/daily_sync.yml)

## 📊 Live Sales Dashboard

**[→ Open Sales Dashboard](https://ragheeda-boop.github.io/ai-sales-os/Sales_Dashboard_Accounts.html)** — auto-regenerated daily from live Notion data

## Architecture

```
Apollo.io  ──►  Python Engine (19 scripts)  ──►  Notion  ──►  GitHub Actions  ──►  Odoo (Phase 4)
(Data)          Sync + Enrich + Score +          (CRM Hub)    2-job pipeline       (ERP)
                Action + Sequence + Meet +        7 DBs        + weekly calibration
                Dashboard + Signals + AI
```

**Autonomous Loop:** Score → Task → Sequence → Track → Meet → Analyze → Opportunity → Calibrate → Better Score

**Design:** No middleware. No n8n, no Make.com, no Zapier. Pure Python + GitHub Actions = full control, zero cost.

## What's New in v4.3

- **Apollo Signals in Sync** — Intent Strength, Job Change Event/Date extracted directly during daily sync
- **Apollo AI Fields** — AI Decision (contacts), AI Qualification Status/Detail (companies) from `typed_custom_fields`
- **Headcount Growth** — 6M/12M/24M company growth signals synced automatically
- **Live Sales Dashboard** — Account-based HTML dashboard, auto-regenerated daily via GitHub Actions
- **Meeting Intelligence** — AI-powered meeting analysis via Claude API (Phase 3.5)
- **Opportunity Pipeline** — Meetings → Opportunities + stale deal detection

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

# 9. Sync meetings + analyze
python meeting_tracker.py --days 7
python meeting_analyzer.py --limit 10

# 10. Generate dashboard
python dashboard_generator.py

# 11. Validate pipeline
python health_check.py

# 12. Daily sync (after setup)
python daily_sync.py --mode incremental --days 1
```

## Core Scripts (19 Production)

| Script | Purpose | Status |
|--------|---------|--------|
| `daily_sync.py` | Apollo → Notion sync (v2.3, 3 modes, signals + AI fields) | **ACTIVE** |
| `lead_score.py` | Lead Score (0-100) + Lead Tier (HOT/WARM/COLD) | **ACTIVE** |
| `constants.py` | Unified field names, thresholds, SLA hours, Apollo AI field IDs | **ACTIVE** |
| `action_ready_updater.py` | 5-condition Action Ready evaluator | **ACTIVE** |
| `auto_tasks.py` | SLA-based task automation engine | **ACTIVE** |
| `health_check.py` | Post-pipeline health validator | **ACTIVE** |
| `notion_helpers.py` | Shared Notion API utilities | **ACTIVE** |
| `job_postings_enricher.py` | Intent proxy — Apollo Job Postings API | **ACTIVE** |
| `auto_sequence.py` | Auto-enroll contacts in Apollo Sequences | **ACTIVE** |
| `analytics_tracker.py` | Apollo Analytics → Notion engagement sync | **ACTIVE** |
| `score_calibrator.py` | Self-learning weight adjustment | **ACTIVE** |
| `morning_brief.py` | Daily intelligence report generator | **ACTIVE** |
| `meeting_tracker.py` | Notion-native meeting sync + contact stage update | **ACTIVE (v4.1)** |
| `meeting_analyzer.py` | Claude AI meeting intelligence | **ACTIVE (v4.1)** |
| `opportunity_manager.py` | Meetings → Opportunities + stale deal detection | **ACTIVE (v4.1)** |
| `dashboard_generator.py` | Live Notion data → Sales Dashboard HTML | **ACTIVE (v4.2)** |
| `doc_sync_checker.py` | Documentation drift validator | **ACTIVE (v4.1)** |
| `webhook_server.py` | Apollo webhook receiver | **ACTIVE** |
| `verify_links.py` | Contact-company link verifier | **ACTIVE** |

## Sync Modes

| Mode | Description | When to Use |
|------|-------------|-------------|
| **incremental** | Last N hours/days (local timestamp filter) | Daily automated sync |
| **backfill** | Historical with checkpoint resume | Gap recovery, catch-up |
| **full** | All records (A-Z alphabetical partitioning) | First-time setup, full rebuild |

## Lead Score Formula (v1.1 — current)

```
Score = (Intent × 10%) + (Engagement × 10%) + (Company Size × 45%) + (Seniority × 35%)
```

**Why?** Intent and Engagement are sparse in cold Apollo data. Size and Seniority are available for nearly all records.

| Tier | Score | Action | SLA |
|------|-------|--------|-----|
| **HOT** | ≥ 80 | CALL today | 24 hours |
| **WARM** | 50–79 | FOLLOW-UP email | 48 hours |
| **COLD** | < 50 | Monitor only | — |

**Future v2.0 weights** (activate only when signals data > 50% coverage): Intent(30%) + Engagement(25%) + Signals(25%) + Size(10%) + Seniority(10%)

## GitHub Actions Pipeline

**Schedule:** Daily at 7:00 AM KSA (04:00 UTC) | **Manual trigger:** Available from UI

### Job 1: Sync & Score (timeout 5h 50min)
1. `daily_sync.py --mode incremental --hours 26` — sync + signals + AI fields
2. `job_postings_enricher.py --limit 50` — intent enrichment
3. `lead_score.py` — score + Lead Tier
4. `action_ready_updater.py` — evaluate Action Ready

### Job 2: Action & Track (timeout 3h)
5. `auto_tasks.py` — create SLA tasks
6. `auto_sequence.py --limit 50` — sequence enrollment
7. `meeting_tracker.py --days 7` — sync meetings
8. `meeting_analyzer.py --limit 10` — AI meeting intelligence
9. `opportunity_manager.py` — meetings → opportunities
10. `analytics_tracker.py --days 7` — engagement sync
11. `health_check.py` — validate pipeline
12. `morning_brief.py --output file` — daily report
13. `dashboard_generator.py` — regenerate live dashboard
14. Auto-commit dashboard + upload logs

**Weekly (Sundays):** `score_calibrator.py --days 30 --export` (review-only, no auto-apply)

**Required Secrets:** `APOLLO_API_KEY`, `NOTION_API_KEY`, `NOTION_DATABASE_ID_CONTACTS`, `NOTION_DATABASE_ID_COMPANIES`, `NOTION_DATABASE_ID_TASKS`, `NOTION_DATABASE_ID_MEETINGS`, `NOTION_DATABASE_ID_OPPORTUNITIES`, `ANTHROPIC_API_KEY` (optional)

**Cost:** ~900 min/month (free tier = 2,000 min/month)

## Folder Structure

```
AI Sales OS/
├── 💻 CODE/Phase 3 - Sync/       → All 19 production scripts
│   ├── daily_sync.py              → Sync engine v2.3 (signals + AI fields)
│   ├── lead_score.py              → Lead scorer + Lead Tier writer
│   ├── constants.py               → Unified field names, thresholds, Apollo AI IDs
│   ├── auto_tasks.py              → Action Engine (SLA task creator)
│   ├── meeting_tracker.py         → Meeting sync + contact stage [v4.1]
│   ├── meeting_analyzer.py        → AI meeting intelligence [v4.1]
│   ├── opportunity_manager.py     → Opportunity pipeline [v4.1]
│   ├── dashboard_generator.py     → Live dashboard generator [v4.2]
│   └── ...                        → 11 more production scripts
├── Sales_Dashboard_Accounts.html  → Live Sales Dashboard (auto-regenerated)
├── .claude/skills/                → 12 Claude Skills for operations
├── .github/workflows/             → daily_sync.yml (2-job pipeline + weekly calibration)
├── 📊 DATA/                       → CSVs, mappings, snapshots, logs
├── 📚 DOCUMENTATION/              → Execution plan, audits, guides
├── 🎯 PRESENTATIONS/              → English, Arabic, CEO Pitch decks
├── 🚀 START HERE/                 → Quick start & system overview
└── 🗂️ ARCHIVED/                  → Superseded files
```

## Execution Status

| Phase | Status | Details |
|-------|--------|---------|
| **Phase 1: ACTIVATE** | ✅ COMPLETE | Full sync, scoring, seniority normalization, safe booleans |
| **Phase 2: ACTION** | ✅ COMPLETE | auto_tasks.py + action_ready_updater.py + health_check.py |
| **Phase 3: ENRICH** | ✅ COMPLETE | Job postings, auto sequences, analytics, self-learning calibration |
| **Phase 3.5: MEET** | ✅ COMPLETE | Meeting tracker, AI analyzer, opportunity manager, dashboard |
| **Phase 4: OPTIMIZE** | 🔜 Planned | Odoo ERP integration, revenue tracking, advanced analytics |

**Claude Skills:** 12 built and evaluated at 100% pass rate

**Version:** 4.3 | **Updated:** 30 March 2026 | **Contacts:** 44,875 | **Companies:** 15,407

**Full documentation:** See `📚 DOCUMENTATION/` or open `AI_Sales_OS_MindMap.html`
