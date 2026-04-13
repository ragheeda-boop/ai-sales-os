# AI Sales OS v7.0 — Decision Layer Architecture

**Apollo + Notion + Python + GitHub Actions** — Autonomous Sales Operating System.

45,086 contacts | 15,407 companies | 30 production scripts | 8 modules | Decision Layer | Autonomous Loop | Self-learning scoring | Live Dashboard

[![Daily Pipeline](https://github.com/ragheeda-boop/ai-sales-os/actions/workflows/daily_sync.yml/badge.svg)](https://github.com/ragheeda-boop/ai-sales-os/actions/workflows/daily_sync.yml)

## Live Sales Dashboard

**[Open Sales Dashboard](https://ragheeda-boop.github.io/ai-sales-os/dashboards/active/Sales_Dashboard_Accounts.html)** — auto-regenerated daily from live Notion data

## Architecture

```
Apollo.io  ──►  Python Engine (8 modules, 22 scripts)  ──►  Notion  ──►  GitHub Actions  ──►  Odoo (Phase 4)
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

# 7. Compute company priority scores
python scoring/company_priority_scorer.py --execute --force

# 8. Create SLA-based tasks
python automation/auto_tasks.py

# 9. Enroll in Apollo sequences
python automation/auto_sequence.py --dry-run

# 10. Sync meetings + analyze
python meetings/meeting_tracker.py --days 7
python meetings/meeting_analyzer.py --limit 10

# 11. Generate dashboard
python monitoring/dashboard_generator.py

# 12. Validate pipeline
python monitoring/health_check.py

# 13. Daily sync (after setup)
python core/daily_sync.py --mode incremental --days 1
```

## Module Architecture (22 Production Scripts)

| Module | Scripts | Purpose |
|--------|---------|---------|
| **core/** | constants.py, notion_helpers.py, daily_sync.py, doc_sync_checker.py, ai_sales_actions_parser.py | Engine fundamentals |
| **scoring/** | lead_score.py, score_calibrator.py, action_ready_updater.py, company_priority_scorer.py | Intelligence layer |
| **automation/** | auto_tasks.py, auto_sequence.py, outcome_tracker.py, lead_inbox_mover.py | Execution layer |
| **governance/** | ingestion_gate.py, data_governor.py, audit_ownership.py, full_reset_notion.py | Data quality |
| **enrichment/** | job_postings_enricher.py, muhide_strategic_analysis.py, analytics_tracker.py, ai_sales_actions_enricher.py, reply_intelligence.py | Signal collection |
| **meetings/** | meeting_tracker.py, meeting_analyzer.py, opportunity_manager.py | Revenue pipeline |
| **monitoring/** | health_check.py, dashboard_generator.py, morning_brief.py | Observability |
| **webhooks/** | webhook_server.py, verify_links.py | Integration |

## Folder Structure

```
AI Sales OS/
├── scripts/                     → 30 production scripts in 8 modules
│   ├── core/                    → Engine: sync, constants, Notion helpers, AI Sales Actions parser
│   ├── scoring/                 → Lead Score, Calibrator, Action Ready, Company Priority Scorer
│   ├── automation/              → Tasks, Sequences, Outcome Tracker, Lead Inbox Mover
│   ├── governance/              → Ingestion Gate, Data Governor, Audit, Full Reset
│   ├── enrichment/              → Job Postings, MUHIDE Analysis, Analytics, Reply Intelligence
│   ├── meetings/                → Meeting Tracker, Analyzer, Opportunity Manager
│   ├── monitoring/              → Health Check, Dashboard, Morning Brief
│   └── webhooks/                → Webhook Server, Verify Links
├── pipelines/                   → Separate data pipelines
│   ├── muqawil/                 → Contractors pipeline (scraper + pipeline + output)
│   ├── engineering_offices/     → Ministry offices pipeline
│   └── file_sync/               → Tri-directional sync engine
├── dashboards/                  → HTML dashboards and reports
│   ├── active/                  → Live dashboards (Sales_Dashboard_Accounts.html)
│   └── archived/                → Historical dashboards and reports
├── data/                        → CSVs, mappings, snapshots, logs
├── docs/                        → Architecture, reports, ops, setup, Notion ops
├── presentations/               → English, Arabic, CEO Pitch decks
├── assets/                      → Brand logos
├── commands/                    → CLI command reference (6 shell scripts)
├── archive/                     → Superseded files
├── .claude/skills/              → 12 Claude Skills for operations
└── .github/workflows/           → daily_sync.yml (2-job pipeline + weekly calibration)
```

## GitHub Actions Pipeline (v3.1 — Safe Execution Order)

**Schedule:** Daily at 7:00 AM KSA (04:00 UTC) | **Manual trigger:** Available from UI

### Job 1: Sync → Signals → Score → Decide (timeout 5h 50min)
1. `core/daily_sync.py --mode incremental --hours 26` — sync + signals + AI fields
2. `enrichment/analytics_tracker.py --days 7` — engagement sync (signals before scoring)
3. `automation/outcome_tracker.py --execute` — close task → contact loop
4. `meetings/meeting_tracker.py --days 7` — sync meetings + Company Stage
5. `meetings/opportunity_manager.py` — meetings → opportunities + Company Stage
6. `enrichment/job_postings_enricher.py --limit 50` — intent enrichment
7. `scoring/lead_score.py` — score + Lead Tier (reads fresh signals from steps 2-5)
8. `scoring/action_ready_updater.py` — evaluate Action Ready
9. `scoring/company_priority_scorer.py --execute` — rank companies by strategic value (Decision Layer)

### Job 2: Action & Track (timeout 3h)
10. `automation/auto_tasks.py` — create SLA tasks
11. `automation/auto_sequence.py --limit 50` — sequence enrollment
12. `meetings/meeting_analyzer.py --limit 10` — AI meeting intelligence (non-blocking)
13. `monitoring/health_check.py` — validate pipeline
14. `monitoring/morning_brief.py --output file` — daily report (frozen v2.0)
15. `monitoring/dashboard_generator.py` — regenerate live dashboard (frozen v2.0)
16. Auto-commit dashboard + upload logs

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
| **Phase 3.8: MODULAR** | COMPLETE | v6.0 → v6.2 — 8-module architecture + safe execution order + governance guards |
| **Phase 3.9: DECISION LAYER** | COMPLETE | v7.0 — Company Priority Scorer + strategic ranking (Signals removed: AI Executor, AI Sequence Generator, Call Script Builder, Cleanup Tasks, Archive Unqualified, Fix Seniority) |
| **Phase 4: OPTIMIZE** | Planned | Odoo ERP integration, revenue tracking |

**Claude Skills:** 12 built and evaluated at 100% pass rate

**Version:** 7.0 | **Updated:** 14 April 2026 | **Contacts:** 45,086 | **Companies:** 15,407

**Full documentation:** See `docs/` or open `dashboards/archived/AI_Sales_OS_MindMap.html`
