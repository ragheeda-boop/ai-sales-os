# AI Sales OS v4.1 — Project Map

> **Version:** 4.1 | **Last Updated:** 28 March 2026 | **Phase 3.5 Complete**

---

## Folder Structure

```
AI Sales OS/
│
├── CLAUDE.md                           ← AI instructions & system reference
├── README.md                           ← Project overview
├── AI_Sales_OS_MindMap.html            ← Interactive mind map v8.0 (Arabic)
├── Muhide.png                          ← Brand logo
├── .gitignore
│
├── 🚀 START HERE/                      ← Start here if you're new
│   ├── QUICK_START.md                  ← Setup guide (step-by-step)
│   ├── SYSTEM_OVERVIEW.md              ← Architecture and autonomous loop
│   ├── PROJECT_MAP.md                  ← This file — folder navigator
│   └── README.md                       ← Entry navigation guide
│
├── 💻 CODE/Phase 3 - Sync/            ← 18 production Python scripts
│   ├── daily_sync.py                   ← Sync engine v2.1 (3 modes: incremental/backfill/full)
│   ├── lead_score.py                   ← Lead Score (0-100) + Lead Tier (HOT/WARM/COLD)
│   ├── constants.py                    ← Single source of truth: field names, thresholds, SLA
│   ├── notion_helpers.py               ← Shared Notion API utilities
│   ├── action_ready_updater.py         ← Action Ready evaluator (5-condition gate)
│   ├── auto_tasks.py                   ← Action Engine — SLA-based task creator
│   ├── health_check.py                 ← Post-pipeline health validator
│   ├── job_postings_enricher.py        ← Intent proxy — Apollo Job Postings API [v4.0]
│   ├── auto_sequence.py                ← Auto-enroll contacts in Apollo Sequences [v4.0]
│   ├── analytics_tracker.py            ← Apollo Analytics → Notion engagement sync [v4.0]
│   ├── score_calibrator.py             ← Self-learning weight adjustment [v4.0]
│   ├── morning_brief.py                ← Daily intelligence report [v4.0]
│   ├── meeting_tracker.py              ← Meeting sync + Contact stage update [Phase 3.5]
│   ├── meeting_analyzer.py             ← AI meeting intelligence via Claude API [Phase 3.5]
│   ├── opportunity_manager.py          ← Meetings → Opportunities + stale deal detection [Phase 3.5]
│   ├── doc_sync_checker.py             ← Documentation drift validator [v4.1]
│   ├── webhook_server.py               ← Apollo webhook receiver
│   ├── verify_links.py                 ← Contact-company link verifier
│   ├── requirements.txt                ← Python dependencies
│   ├── .env                            ← API credentials (NEVER commit)
│   ├── .env.example                    ← Credential template
│   └── *.log                           ← Runtime logs (auto-generated, gitignored)
│
├── 🎯 PRESENTATIONS/                   ← All presentation files (organized by audience)
│   ├── English/
│   │   └── AI_Sales_OS_Presentation.pptx       ← Technical deck v4.1 (English)
│   ├── Arabic/
│   │   ├── عرض_تقديمي_AI_Sales_OS_v4.1.pptx   ← Arabic technical deck (latest)
│   │   └── عرض_تقديمي_v2.pptx                 ← Arabic v2 overview
│   └── CEO Pitch/
│       └── AI_Sales_OS_CEO_Pitch_v2.pptx       ← Executive business pitch (Arabic)
│
├── 📊 DATA/
│   ├── Import CSVs/                    ← Original Apollo data exports
│   │   ├── IMPORT_companies_FINAL.csv  ← 15,407 companies
│   │   ├── IMPORT_contacts_FINAL.csv   ← 44,875 contacts
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
├── 📚 DOCUMENTATION/
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
│   └── daily_sync.yml                  ← 16-step daily pipeline + weekly calibration
│
└── 🗂️ ARCHIVED/                       ← Superseded files (do not delete — historical reference)
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
| Main sync script | `💻 CODE/Phase 3 - Sync/daily_sync.py` |
| Lead scoring engine | `💻 CODE/Phase 3 - Sync/lead_score.py` |
| Action Engine (task creation) | `💻 CODE/Phase 3 - Sync/auto_tasks.py` |
| Action Ready evaluator | `💻 CODE/Phase 3 - Sync/action_ready_updater.py` |
| Meeting intelligence | `💻 CODE/Phase 3 - Sync/meeting_analyzer.py` |
| All constants & field names | `💻 CODE/Phase 3 - Sync/constants.py` |
| Documentation drift check | `💻 CODE/Phase 3 - Sync/doc_sync_checker.py` |
| Execution plan | `📚 DOCUMENTATION/EXECUTION_PLAN_v3.2.docx` |
| Field mapping reference | `📚 DOCUMENTATION/System Architecture/FIELD_MAPPING_RULES.md` |
| Deep analysis report | `📚 DOCUMENTATION/AI_Sales_OS_Deep_Analysis.md` |
| GitHub Actions pipeline | `.github/workflows/daily_sync.yml` |
| API credentials | `💻 CODE/Phase 3 - Sync/.env` |
| Mind map | `AI_Sales_OS_MindMap.html` |
| English tech deck | `🎯 PRESENTATIONS/English/AI_Sales_OS_Presentation.pptx` |
| CEO pitch | `🎯 PRESENTATIONS/CEO Pitch/AI_Sales_OS_CEO_Pitch_v2.pptx` |

---

## Active Scripts — 18 Production Scripts

| Script | Version | Purpose |
|---|---|---|
| `daily_sync.py` | v2.1 | Apollo → Notion sync (3 modes) |
| `lead_score.py` | v1.1 | Lead Score + Lead Tier writer |
| `constants.py` | — | Field names, thresholds, SLA hours |
| `notion_helpers.py` | — | Shared Notion API utilities |
| `action_ready_updater.py` | — | 5-condition Action Ready gate |
| `auto_tasks.py` | — | SLA-based task creator |
| `health_check.py` | — | Post-pipeline health validator |
| `job_postings_enricher.py` | v4.0 | Intent proxy — Job Postings API |
| `auto_sequence.py` | v4.0 | Apollo Sequence enrollment |
| `analytics_tracker.py` | v4.0 | Apollo Analytics → Notion sync |
| `score_calibrator.py` | v4.0 | Self-learning weight adjustment |
| `morning_brief.py` | v4.0 | Daily intelligence report |
| `meeting_tracker.py` | v4.1 | Meeting sync + Contact stage |
| `meeting_analyzer.py` | v4.1 | AI meeting intelligence (Claude API) |
| `opportunity_manager.py` | v4.1 | Meetings → Opportunities pipeline |
| `doc_sync_checker.py` | v4.1 | Documentation drift validator |
| `webhook_server.py` | — | Apollo webhook receiver |
| `verify_links.py` | — | Contact-company link verifier |

**Superseded (in 🗂️ ARCHIVED/Temp Scripts/):** `sync_companies.py` · `sync_contacts.py` · `apollo_sync_scheduler.py` · `initial_load_from_csv.py`

---

## Phase Status

| Phase | Name | Status |
|---|---|---|
| Phase 1 | ACTIVATE — Full sync + Notion CRM | ✅ Complete |
| Phase 2 | ACTION — Tasks + Action Ready + Health Check | ✅ Complete |
| Phase 3 | ENRICH — Intent + Sequences + Analytics + Calibration | ✅ Complete |
| Phase 3.5 | MEET — Meeting Intelligence + Opportunity Pipeline | ✅ Complete |
| Phase 4 | OPTIMIZE — Odoo ERP + Revenue Tracking | 🔵 Planned |

**Overall progress: 98%**

---

## GitHub Actions Pipeline — 16 Steps

Daily at **7:00 AM KSA** (04:00 UTC):

| # | Step | Script |
|---|---|---|
| 1 | Checkout | — |
| 2 | Setup Python 3.11 | — |
| 3 | Install dependencies | — |
| 4 | Sync | `daily_sync.py --hours 26` |
| 5 | Enrich | `job_postings_enricher.py --limit 50` |
| 6 | Score | `lead_score.py` |
| 7 | Gate | `action_ready_updater.py` |
| 8 | Tasks | `auto_tasks.py` |
| 9 | Sequence | `auto_sequence.py --limit 50` |
| 10 | Meeting Tracker | `meeting_tracker.py --days 7` |
| 11 | Meeting Analyzer | `meeting_analyzer.py --limit 10` |
| 12 | Opportunity Manager | `opportunity_manager.py` |
| 13 | Analytics | `analytics_tracker.py --days 7` |
| 14 | Health Check | `health_check.py` |
| 15 | Morning Brief | `morning_brief.py --output file` |
| 16 | Upload Logs | (30-day retention) |

**Weekly (Sundays):** `score_calibrator.py --days 30 --export` — review-only, no auto-apply.
