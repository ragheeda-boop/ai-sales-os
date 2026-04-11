# AI Sales OS v6.0 — Modular Architecture

**Apollo + Notion + Python + GitHub Actions** — Autonomous Sales Operating System.

45,086 contacts | 15,407 companies | 26 production scripts | 8 modules | Autonomous Loop | Self-learning scoring | Live Dashboard

[![Daily Pipeline](https://github.com/ragheeda-boop/ai-sales-os/actions/workflows/daily_sync.yml/badge.svg)](https://github.com/ragheeda-boop/ai-sales-os/actions/workflows/daily_sync.yml)

## Live Sales Dashboard

**[Open Sales Dashboard](https://ragheeda-boop.github.io/ai-sales-os/dashboards/Sales_Dashboard_Accounts.html)** — auto-regenerated daily from live Notion data

## Architecture

```
Apollo.io  ──►  Python Engine (8 modules, 26 scripts)  ──►  Notion  ──►  GitHub Actions  ──►  Odoo (Phase 4)
(Data)          core / scoring / automation /                (CRM Hub)    2-job pipeline       (ERP)
                governance / enrichment / meetings /          7 DBs        + weekly calibration
                monitoring / webhooks                         Company-Centric
```

**Autonomous Loop:** Score → Task → Sequence → Track → Meet → Analyze → Opportunity → Calibrate → Better Score

**Design:** No middleware. No n8n, no Make.com, no Zapier. Pure Python + GitHub Actions = full control, zero cost.

## Quick Start

```bash
# 1. Configure credentials
cd scripts
cp .env.example .env
# Edit .env with your API keys

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run full sync (first time — 2-4 hours)
python core/daily_sync.py --mode full

# 4. Enrich companies with job postings intent
python enrichment/job_postings_enricher.py --limit 50

# 5. Calculate lead scores + assign tiers
python scoring/lead_score.py --force

# 6. Set Action Ready flags
python scoring/action_ready_updater.py

# 7. Create SLA-based tasks
python automation/auto_tasks.py

# 8. Enroll in Apollo sequences
python automation/auto_sequence.py --dry-run

# 9. Sync meetings + analyze
python meetings/meeting_tracker.py --days 7
python meetings/meeting_analyzer.py --limit 10

# 10. Generate dashboard
python monitoring/dashboard_generator.py

# 11. Validate pipeline
python monitoring/health_check.py

# 12. Daily sync (after setup)
python core/daily_sync.py --mode incremental --days 1
```

## Module Architecture (26 Production Scripts)

| Module | Scripts | Purpose |
|--------|---------|---------|
| **core/** | constants.py, notion_helpers.py, daily_sync.py, doc_sync_checker.py | Engine fundamentals |
| **scoring/** | lead_score.py, score_calibrator.py, action_ready_updater.py | Intelligence layer |
| **automation/** | auto_tasks.py, auto_sequence.py, outcome_tracker.py, cleanup_overdue_tasks.py | Execution layer |
| **governance/** | ingestion_gate.py, data_governor.py, archive_unqualified.py, audit_ownership.py, fix_seniority.py | Data quality |
| **enrichment/** | job_postings_enricher.py, muhide_strategic_analysis.py, analytics_tracker.py | Signal collection |
| **meetings/** | meeting_tracker.py, meeting_analyzer.py, opportunity_manager.py | Revenue pipeline |
| **monitoring/** | health_check.py, dashboard_generator.py, morning_brief.py | Observability |
| **webhooks/** | webhook_server.py, verify_links.py | Integration |

## Folder Structure

```
AI Sales OS/
├── scripts/                     → 26 production scripts in 8 modules
│   ├── core/                    → Engine: sync, constants, Notion helpers
│   ├── scoring/                 → Lead Score, Calibrator, Action Ready
│   ├── automation/              → Tasks, Sequences, Outcome Tracker
│   ├── governance/              → Ingestion Gate, Data Governor, Archival
│   ├── enrichment/              → Job Postings, MUHIDE Analysis, Analytics
│   ├── meetings/                → Meeting Tracker, Analyzer, Opportunity Manager
│   ├── monitoring/              → Health Check, Dashboard, Morning Brief
│   └── webhooks/                → Webhook Server, Verify Links
├── pipelines/                   → Separate data pipelines
│   ├── muqawil/                 → Contractors pipeline
│   ├── engineering_offices/     → Ministry offices pipeline
│   └── file_sync/               → Tri-directional sync engine
├── dashboards/                  → HTML dashboards and reports
├── data/                        → CSVs, mappings, snapshots, logs
├── docs/                        → Audits, architecture, reports, MUHIDE
├── presentations/               → English, Arabic, CEO Pitch decks
├── assets/                      → Brand logos
├── start_here/                  → Quick start & system overview
├── archive/                     → Superseded files
├── .claude/skills/              → 12 Claude Skills for operations
└── .github/workflows/           → daily_sync.yml (2-job pipeline + weekly calibration)
```

## GitHub Actions Pipeline (v3.0)

**Schedule:** Daily at 7:00 AM KSA (04:00 UTC) | **Manual trigger:** Available from UI

### Job 1: Sync & Score (timeout 5h 50min)
1. `core/daily_sync.py --mode incremental --hours 26` — sync + signals + AI fields
2. `enrichment/job_postings_enricher.py --limit 50` — intent enrichment
3. `scoring/lead_score.py` — score + Lead Tier
4. `scoring/action_ready_updater.py` — evaluate Action Ready

### Job 2: Action & Track (timeout 3h)
5. `automation/auto_tasks.py` — create SLA tasks
6. `automation/auto_sequence.py --limit 50` — sequence enrollment
7. `meetings/meeting_tracker.py --days 7` — sync meetings
8. `meetings/meeting_analyzer.py --limit 10` — AI meeting intelligence
9. `meetings/opportunity_manager.py` — meetings → opportunities
10. `enrichment/analytics_tracker.py --days 7` — engagement sync
11. `automation/outcome_tracker.py --execute` — close task → contact loop
12. `monitoring/health_check.py` — validate pipeline
13. `monitoring/morning_brief.py --output file` — daily report
14. `monitoring/dashboard_generator.py` — regenerate live dashboard
15. Auto-commit dashboard + upload logs

**Weekly (Sundays):** `scoring/score_calibrator.py --days 30 --export` (review-only, no auto-apply)

**Required Secrets:** `APOLLO_API_KEY`, `NOTION_API_KEY`, `NOTION_DATABASE_ID_CONTACTS`, `NOTION_DATABASE_ID_COMPANIES`, `NOTION_DATABASE_ID_TASKS`, `NOTION_DATABASE_ID_MEETINGS`, `NOTION_DATABASE_ID_OPPORTUNITIES`, `ANTHROPIC_API_KEY` (optional)

## Execution Status

| Phase | Status | Details |
|-------|--------|---------|
| **Phase 1: ACTIVATE** | COMPLETE | Full sync, scoring, seniority normalization |
| **Phase 2: ACTION** | COMPLETE | Action Engine, Action Ready evaluator |
| **Phase 3: ENRICH** | COMPLETE | Job postings, sequences, analytics, calibration |
| **Phase 3.5: MEET** | COMPLETE | Meeting tracker, AI analyzer, opportunity manager |
| **Phase 3.7: COMPANY-CENTRIC** | COMPLETE | v5.0 — Company as primary entity |
| **Phase 3.8: MODULAR** | COMPLETE | v6.0 — 8-module architecture restructuring |
| **Phase 4: OPTIMIZE** | Planned | Odoo ERP integration, revenue tracking |

**Claude Skills:** 12 built and evaluated at 100% pass rate

**Version:** 6.0 | **Updated:** 7 April 2026 | **Contacts:** 45,086 | **Companies:** 15,407

**Full documentation:** See `docs/` or open `dashboards/AI_Sales_OS_MindMap.html`
