# AI Sales OS v6.0 — Project Map

> **Version:** 6.0 | **Last Updated:** 7 April 2026 | **Phase 3.7 Complete (Company-Centric) + Modular Architecture**

---

## Folder Structure

```
AI Sales OS/
│
├── CLAUDE.md                           ← AI instructions & system reference
├── README.md                           ← Project overview
├── AI_Sales_OS_MindMap.html            ← Interactive mind map v8.2 (Arabic)
├── Muhide.png                          ← Brand logo
├── .gitignore
│
├── start_here/                         ← Start here if you're new
│   ├── QUICK_START.md                  ← Setup guide (step-by-step)
│   ├── SYSTEM_OVERVIEW.md              ← Architecture and autonomous loop
│   ├── PROJECT_MAP.md                  ← This file — folder navigator
│   └── README.md                       ← Entry navigation guide
│
├── scripts/                            ← 26 production Python scripts (8 modules)
│   ├── core/                           ← Core sync + utilities (4 scripts)
│   │   ├── daily_sync.py               ← Sync engine v4.0 (Company-Centric: 3 modes + local timestamp filter)
│   │   ├── constants.py                ← Single source of truth: field names, thresholds, SLA
│   │   ├── notion_helpers.py           ← Shared Notion API utilities
│   │   ├── doc_sync_checker.py         ← Documentation drift validator [v4.1]
│   │   ├── .env                        ← API credentials (NEVER commit)
│   │   ├── .env.example                ← Credential template
│   │   └── requirements.txt            ← Python dependencies
│   │
│   ├── scoring/                        ← Lead scoring + calibration (3 scripts)
│   │   ├── lead_score.py               ← Lead Score (0-100) + Lead Tier [v1.5: 5 components]
│   │   ├── score_calibrator.py         ← Self-learning weight adjustment [v4.0]
│   │   └── action_ready_updater.py     ← Action Ready evaluator (5-condition gate)
│   │
│   ├── automation/                     ← Task automation + sequences (4 scripts)
│   │   ├── auto_tasks.py               ← Action Engine v2.0 (Company-Centric: ONE task per company per tier)
│   │   ├── auto_sequence.py            ← Auto-enroll contacts in Apollo Sequences [v4.0]
│   │   ├── outcome_tracker.py          ← Task → Contact outcome loop [v1.0]
│   │   └── cleanup_overdue_tasks.py    ← Legacy task cleanup
│   │
│   ├── governance/                     ← Data governance (5 scripts)
│   │   ├── ingestion_gate.py           ← Ingestion gate — validates data before entry [v6.0]
│   │   ├── data_governor.py            ← Data governance enforcer [v6.0]
│   │   ├── archive_unqualified.py      ← Contact archiver [v4.4]
│   │   ├── audit_ownership.py          ← Ownership audit
│   │   └── fix_seniority.py            ← Seniority normalization (one-time)
│   │
│   ├── enrichment/                     ← Intent + analytics (3 scripts)
│   │   ├── job_postings_enricher.py    ← Intent proxy — Apollo Job Postings API [v4.0]
│   │   ├── muhide_strategic_analysis.py ← MUHIDE strategic analysis engine (Claude API)
│   │   └── analytics_tracker.py        ← Apollo Analytics → Notion engagement sync [v4.0]
│   │
│   ├── meetings/                       ← Meeting → revenue pipeline (3 scripts)
│   │   ├── meeting_tracker.py          ← Meeting sync v2.0 (Company-Centric auto-link) [Phase 3.5]
│   │   ├── meeting_analyzer.py         ← AI meeting intelligence via Claude API [Phase 3.5]
│   │   └── opportunity_manager.py      ← Meetings → Opportunities v2.0 (Company-Centric, 1 opp per company)
│   │
│   ├── monitoring/                     ← Health + observability (3 scripts)
│   │   ├── health_check.py             ← Post-pipeline health validator
│   │   ├── dashboard_generator.py      ← Live Notion data → Sales Dashboard HTML [v4.2]
│   │   └── morning_brief.py            ← Daily intelligence report [v4.0]
│   │
│   └── webhooks/                       ← Webhook handlers (2 scripts)
│       ├── webhook_server.py           ← Apollo webhook receiver
│       └── verify_links.py             ← Contact-company link verifier
│
├── presentations/                      ← All presentation files (organized by audience)
│   ├── English/
│   │   └── AI_Sales_OS_Presentation.pptx       ← Technical deck v4.1 (English)
│   ├── Arabic/
│   │   ├── عرض_تقديمي_AI_Sales_OS_v4.1.pptx   ← Arabic technical deck (latest)
│   │   └── عرض_تقديمي_v2.pptx                 ← Arabic v2 overview
│   └── CEO Pitch/
│       └── AI_Sales_OS_CEO_Pitch_v2.pptx       ← Executive business pitch (Arabic)
│
├── data/                               ← Data files and snapshots
│   ├── Import CSVs/                    ← Original Apollo data exports
│   │   ├── IMPORT_companies_FINAL.csv  ← 15,407 companies
│   │   ├── IMPORT_contacts_FINAL.csv   ← 45,086 contacts
│   │   └── test_100_*.csv              ← Test batch samples
│   ├── Mapping Files/                  ← Apollo ↔ Notion field mappings
│   │   ├── APOLLO_TO_NOTION_MAPPING.xlsx
│   │   └── NOTION_SETUP_TRACKER.xlsx
│   ├── Notion Snapshots/               ← JSON exports for reference
│   │   ├── notion_companies.json
│   │   ├── notion_contacts.json
│   │   └── sample_100_records.json
│   ├── Logs/                           ← Runtime stats and sync logs
│   │   └── Sync Runs/
│   └── APOLLO_NOTION_FIELD_GAP_ANALYSIS.xlsx
│
├── docs/                               ← Technical & strategic documentation
│   ├── EXECUTION_PLAN_v3.2.docx        ← Master execution plan (phases 1–4)
│   ├── AI_Sales_OS_Deep_Analysis.md    ← 12-section system analysis report (v4.1)
│   ├── AI_Sales_OS_Comprehensive_Audit.docx  ← Full audit report
│   ├── AI_Sales_OS_Revenue_Gap_Analysis.docx ← Revenue gap analysis
│   ├── MUHIDE_Brand_Identity_Guide.md  ← Brand voice and visual guidelines
│   ├── GITHUB_SETUP_GUIDE.md           ← GitHub Actions setup (Arabic + English)
│   ├── Phase 1 - Notion Setup/         ← Notion database setup docs
│   ├── Phase 2 - Data Import/          ← Data import strategy and procedures
│   ├── Phase 3 - Apollo API Pull/      ← Apollo API integration documentation
│   └── System Architecture/            ← Technical reference and field mapping
│       ├── FIELD_MAPPING_RULES.md      ← Apollo → Notion field mapping (key reference)
│       ├── TECHNICAL_REFERENCE.md      ← Technical implementation details
│       └── Meeting_Call_Intelligence_Architecture_Assessment.md
│
├── pipelines/                          ← Specialized data pipelines
│   ├── file_sync/                      ← Tri-directional sync (Local ↔ Drive ↔ GitHub)
│   │   ├── 00_START_HERE.md            ← Setup & usage guide
│   │   ├── sync_engine.py              ← Master orchestrator
│   │   ├── scan_local.py / scan_drive.py / scan_github.py
│   │   ├── sync_to_drive.py / sync_to_github.py / sync_to_local.py
│   │   ├── build_manifest.py / detect_conflicts.py / resolve_conflicts.py
│   │   └── backup_manager.py
│   │
│   ├── muqawil/                        ← Contractors pipeline (14,089 records)
│   │   └── [pipeline-specific scripts]
│   │
│   └── engineering_offices/            ← Ministry offices pipeline (inactive — all zeros)
│       └── [pipeline-specific scripts]
│
├── dashboards/                         ← Live HTML dashboards + visualizations
│   ├── Sales_Dashboard_Accounts.html   ← Live sales dashboard (auto-regenerated daily)
│   └── AI_Sales_OS_MindMap.html        ← Interactive mind map v8.2
│
├── assets/                             ← Brand + media files
│   └── Muhide.png                      ← Brand logo
│
├── .claude/skills/                     ← 12 Claude Skills (100% eval pass rate)
│   ├── shared-sales-os-rules/          ← Foundation rules (loaded by all skills)
│   ├── apollo-sync-operator/           ← Sync pipeline operations
│   ├── notion-schema-manager/          ← Notion DB schema management
│   ├── lead-scoring-analyst/           ← Score analysis & calibration
│   ├── data-integrity-guardian/        ← Data quality and dedup
│   ├── action-engine-builder/          ← Task automation
│   ├── pipeline-health-monitor/        ← Health monitoring
│   ├── meeting-intelligence-summarizer/ ← Meeting → CRM bridge
│   ├── revenue-loop-tracker/           ← Score-to-revenue correlation
│   ├── apollo-icp-strategist/          ← ICP & market targeting
│   ├── apollo-sequence-builder/        ← Outbound messaging & sequences
│   └── exec-brief-writer/              ← Executive summaries & status updates
│
├── .github/workflows/
│   └── daily_sync.yml                  ← 2-job daily pipeline (9h capacity) + weekly calibration
│
└── archive/                            ← Superseded files (historical reference only)
    ├── Presentations/                  ← Old presentation versions
    ├── Legacy Code/                    ← Superseded Python scripts
    ├── Legacy Integrations/
    ├── Old Documentation/
    ├── Temp Scripts/                   ← One-time build scripts
    └── [numbered phase archives]
```

---

## Quick File Finder

| What you need | Location |
|---|---|
| Main sync script | `scripts/core/daily_sync.py` |
| Lead scoring engine | `scripts/scoring/lead_score.py` |
| Action Engine (task creation) | `scripts/automation/auto_tasks.py` |
| Action Ready evaluator | `scripts/scoring/action_ready_updater.py` |
| Meeting intelligence | `scripts/meetings/meeting_analyzer.py` |
| All constants & field names | `scripts/core/constants.py` |
| Documentation drift check | `scripts/core/doc_sync_checker.py` |
| Execution plan | `docs/EXECUTION_PLAN_v3.2.docx` |
| Field mapping reference | `docs/System Architecture/FIELD_MAPPING_RULES.md` |
| Deep analysis report | `docs/AI_Sales_OS_Deep_Analysis.md` |
| GitHub Actions pipeline | `.github/workflows/daily_sync.yml` |
| API credentials | `scripts/core/.env` |
| Mind map | `dashboards/AI_Sales_OS_MindMap.html` |
| English tech deck | `presentations/English/AI_Sales_OS_Presentation.pptx` |
| CEO pitch | `presentations/CEO Pitch/AI_Sales_OS_CEO_Pitch_v2.pptx` |

---

## Active Scripts — 26 Production Scripts (8 Modules)

| Module | Script | Version | Purpose |
|--------|--------|---------|---------|
| **Core** | `daily_sync.py` | v4.0 | Apollo → Notion sync (Company-Centric: Primary/Supporting Owners, Company Metrics, Company Stage) |
| **Core** | `constants.py` | — | Field names, thresholds, SLA hours, seniority normalization |
| **Core** | `notion_helpers.py` | — | Shared Notion API utilities (rate limiter, preload, update) |
| **Core** | `doc_sync_checker.py` | v4.1 | Documentation drift validator |
| **Scoring** | `lead_score.py` | v1.5 | Lead Score (0-100) + Lead Tier (5-component formula) |
| **Scoring** | `score_calibrator.py` | v4.0 | Self-learning weight adjustment + outcome analysis |
| **Scoring** | `action_ready_updater.py` | — | 5-condition Action Ready gate |
| **Automation** | `auto_tasks.py` | v2.0 | Company-Centric task creator (ONE task per company per tier) |
| **Automation** | `auto_sequence.py` | v4.0 | Apollo Sequence enrollment (role + tier mapping) |
| **Automation** | `outcome_tracker.py` | v1.0 | Task → Contact outcome loop (Contact Responded, Last Contacted, Meeting Booked) |
| **Automation** | `cleanup_overdue_tasks.py` | — | Bulk-complete legacy pre-v5.0 tasks |
| **Governance** | `ingestion_gate.py` | v6.0 | Validates companies (≥2 ICP criteria) + contacts (4 gates) before entry |
| **Governance** | `data_governor.py` | v6.0 | Audits existing records, archives unqualified, enforces ownership |
| **Governance** | `archive_unqualified.py` | v4.4 | Archive contacts without owner/email |
| **Governance** | `audit_ownership.py` | — | Audit ownership gaps across all 5 Notion DBs |
| **Governance** | `fix_seniority.py` | — | One-time seniority normalization (C-Suite) |
| **Enrichment** | `job_postings_enricher.py` | v4.0 | Intent proxy — Apollo Job Postings API scoring |
| **Enrichment** | `muhide_strategic_analysis.py` | — | MUHIDE ICP analysis (Claude API: Fit Score, Priority, Best Buyer, Outreach Angle) |
| **Enrichment** | `analytics_tracker.py` | v4.0 | Apollo Analytics → Notion engagement sync |
| **Meetings** | `meeting_tracker.py` | v2.0 | Meeting sync (Company-Centric auto-link, Company Stage propagation) |
| **Meetings** | `meeting_analyzer.py` | v1.0 | AI meeting intelligence via Claude API (Key Takeaways, Next Steps, Sentiment) |
| **Meetings** | `opportunity_manager.py` | v2.0 | Company-Centric: Meeting → Opportunity pipeline (1 opp per company, stakeholder tracking) |
| **Monitoring** | `health_check.py` | — | Post-pipeline health validator (critical/warning checks) |
| **Monitoring** | `dashboard_generator.py` | v4.2 | Live Notion data → Sales Dashboard HTML (auto-regenerates daily) |
| **Monitoring** | `morning_brief.py` | v4.0 | Daily intelligence report (urgent calls, tasks, replies, stats) |
| **Webhooks** | `webhook_server.py` | — | Apollo webhook receiver |
| **Webhooks** | `verify_links.py` | — | Contact-company link verifier |

**Superseded:** `sync_companies.py`, `sync_contacts.py`, `apollo_sync_scheduler.py`, `initial_load_from_csv.py`, `outcome_tracker_backup.py` (in `archive/`)

---

## Module Architecture

| Module | Location | Purpose | Scripts |
|--------|----------|---------|---------|
| **Core** | `scripts/core/` | Sync engine + utilities | 4 |
| **Scoring** | `scripts/scoring/` | Lead intelligence | 3 |
| **Automation** | `scripts/automation/` | Task execution | 4 |
| **Governance** | `scripts/governance/` | Data quality | 5 |
| **Enrichment** | `scripts/enrichment/` | Signal generation | 3 |
| **Meetings** | `scripts/meetings/` | Revenue pipeline | 3 |
| **Monitoring** | `scripts/monitoring/` | Health + observability | 3 |
| **Webhooks** | `scripts/webhooks/` | Real-time integrations | 2 |

---

## Phase Status

| Phase | Name | Status |
|---|---|---|
| Phase 1 | ACTIVATE — Full sync + Notion CRM | ✅ Complete |
| Phase 2 | ACTION — Tasks + Action Ready + Health Check | ✅ Complete |
| Phase 3 | ENRICH — Intent + Sequences + Analytics + Calibration | ✅ Complete |
| Phase 3.5 | MEET — Meeting Intelligence + Opportunity Pipeline | ✅ Complete |
| Phase 3.7 | COMPANY-CENTRIC — v5.0 Operating Model + v5.1 Refinements | ✅ Complete |
| Phase 4 | OPTIMIZE — Odoo ERP + Revenue Tracking | 🔵 Planned |

**Overall progress: 99%** | **Architecture: Modular v6.0** | **Scripts: 26 Active**

---

## GitHub Actions Pipeline — 2 Jobs (9h capacity)

Daily at **7:00 AM KSA** (04:00 UTC):

**JOB 1 — sync-and-score (timeout: 5h 50min)**

| # | Step | Script |
|---|---|---|
| 1 | Sync | `core/daily_sync.py --hours 26` (Company-Centric ownership + metrics + stage) |
| 2 | Enrich | `enrichment/job_postings_enricher.py --limit 50` |
| 3 | Score | `scoring/lead_score.py` (v1.5: 5 components) |
| 4 | Gate | `scoring/action_ready_updater.py` |

**JOB 2 — action-and-track (timeout: 3h, runs after Job 1)**

| # | Step | Script |
|---|---|---|
| 5 | Tasks | `automation/auto_tasks.py` (Company-Centric: ONE per company per tier) |
| 6 | Sequence | `automation/auto_sequence.py --limit 50` |
| 7 | Meeting Tracker | `meetings/meeting_tracker.py --days 7` |
| 8 | Meeting Analyzer | `meetings/meeting_analyzer.py --limit 10` |
| 9 | Opportunity Manager | `meetings/opportunity_manager.py` (Company-Centric: ONE opp per company) |
| 10 | Analytics | `enrichment/analytics_tracker.py --days 7` |
| 11 | Outcome Tracker | `automation/outcome_tracker.py --execute` |
| 12 | Health Check | `monitoring/health_check.py` |
| 13 | Morning Brief | `monitoring/morning_brief.py --output file` |
| 14 | Dashboard | `monitoring/dashboard_generator.py` |
| 15 | Upload Logs | (30-day retention) |

**Weekly (Sundays):** `scoring/score_calibrator.py --days 30 --export` — review-only, no auto-apply.
