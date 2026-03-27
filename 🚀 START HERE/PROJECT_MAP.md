# AI Sales OS — Project Map

## Folder Structure

```
AI Sales OS/
│
├── 🚀 START HERE/                      ← Entry point
│   ├── README.md                       ← Navigation guide
│   ├── QUICK_START.md                  ← 5-minute setup guide
│   ├── SYSTEM_OVERVIEW.md              ← Architecture and data flow
│   └── PROJECT_MAP.md                  ← This file
│
├── 💻 CODE/Phase 3 - Sync/            ← Production scripts
│   ├── daily_sync.py                   ← Main sync engine v2.1 (3 modes)
│   ├── lead_score.py                   ← Lead scoring engine v1.1
│   ├── action_ready_updater.py         ← Action Ready evaluator (5 conditions)
│   ├── auto_tasks.py                   ← Action Engine (SLA-based task creator)
│   ├── health_check.py                 ← Pipeline health validator
│   ├── constants.py                    ← Unified field names & thresholds
│   ├── notion_helpers.py               ← Shared Notion API utilities
│   ├── webhook_server.py               ← Apollo webhook receiver
│   ├── verify_links.py                 ← Contact-company link verifier
│   ├── initial_load_from_csv.py        ← One-time CSV import (completed)
│   ├── sync_companies.py               ← Legacy company sync (superseded)
│   ├── sync_contacts.py                ← Legacy contact sync (superseded)
│   ├── apollo_sync_scheduler.py        ← Legacy scheduler (superseded)
│   ├── requirements.txt                ← Python dependencies
│   ├── .env.example                    ← Credential template
│   └── .env                            ← API credentials (not in git)
│
├── 📊 DATA/
│   ├── Import CSVs/                    ← Original import files
│   │   ├── IMPORT_companies_FINAL.csv  ← 15,407 companies
│   │   ├── IMPORT_contacts_FINAL.csv   ← 44,875 contacts
│   │   └── test_100_*.csv              ← Test import samples
│   ├── Mapping Files/                  ← Apollo ↔ Notion field maps
│   │   ├── APOLLO_TO_NOTION_MAPPING.xlsx
│   │   └── NOTION_SETUP_TRACKER.xlsx
│   ├── Notion Snapshots/               ← Database JSON exports
│   │   ├── notion_companies.json
│   │   ├── notion_contacts.json
│   │   └── sample_100_records.json
│   ├── Logs/                           ← Operation logs
│   │   └── Sync Runs/                  ← Sync and score logs
│   └── APOLLO_NOTION_FIELD_GAP_ANALYSIS.xlsx
│
├── 📚 DOCUMENTATION/
│   ├── EXECUTION_PLAN_v3.2.docx        ← CURRENT execution plan (4 phases)
│   ├── AI_Sales_OS_Analysis_Report.docx ← Project analysis report
│   ├── Phase 1 - Notion Setup/         ← Database setup documentation
│   │   ├── EXECUTION_PLAN_v2.0.md      ← Previous plan (superseded by v3.0)
│   │   ├── BLUEPRINT_ARCHITECTURE_v2.0.md
│   │   └── ...setup guides and checklists
│   ├── Phase 2 - Data Import/          ← Import procedures
│   ├── Phase 3 - Apollo API Pull/      ← Sync implementation docs
│   └── System Architecture/            ← Technical reference
│       ├── FIELD_MAPPING_RULES.md      ← Field mapping (key reference)
│       ├── TECHNICAL_REFERENCE.md      ← Technical details
│       ├── CLAUDE.md                   ← AI assistant guidelines
│       └── ...audit reports and summaries
│
├── .github/workflows/
│   └── daily_sync.yml                  ← GitHub Actions (daily pipeline)
│
├── AI_Sales_OS_MindMap.html            ← Interactive mind map v4.0
├── README.md                           ← Project README
├── .gitignore                          ← Git ignore rules
│
└── 🗂️ ARCHIVED/                       ← Superseded files
    ├── 03_PHASE3_WEBHOOK_INTEGRATION/
    ├── 03_PHASE3_WEBHOOK_remaining/
    ├── 03_SETUP/
    ├── 04_EXECUTIVE_DOCS/
    ├── 04_PHASE3_APOLLO_API_PULL/
    ├── 06_UTILITIES/
    └── EXECUTION_PLAN_v2.0.md          ← Previous execution plan
```

## Quick File Finder

| What you need | File |
|--------------|------|
| Main sync script | `💻 CODE/Phase 3 - Sync/daily_sync.py` |
| Lead scoring | `💻 CODE/Phase 3 - Sync/lead_score.py` |
| Action Ready evaluator | `💻 CODE/Phase 3 - Sync/action_ready_updater.py` |
| Action Engine (tasks) | `💻 CODE/Phase 3 - Sync/auto_tasks.py` |
| Constants & thresholds | `💻 CODE/Phase 3 - Sync/constants.py` |
| Execution plan | `📚 DOCUMENTATION/EXECUTION_PLAN_v3.2.docx` |
| Field mapping | `📚 DOCUMENTATION/System Architecture/FIELD_MAPPING_RULES.md` |
| API credentials | `💻 CODE/Phase 3 - Sync/.env` |
| GitHub Actions | `.github/workflows/daily_sync.yml` |
| Mind map | `AI_Sales_OS_MindMap.html` |
| Gap analysis | `📊 DATA/APOLLO_NOTION_FIELD_GAP_ANALYSIS.xlsx` |

## Active vs Superseded Scripts

| Script | Status | Purpose |
|--------|--------|---------|
| `daily_sync.py` | **ACTIVE** | Main sync engine v2.1 (3 modes) |
| `lead_score.py` | **ACTIVE** | Lead Score v1.1 + Lead Tier writer |
| `action_ready_updater.py` | **ACTIVE** | Action Ready evaluator (5 conditions) |
| `auto_tasks.py` | **ACTIVE** | Action Engine (SLA task creator) |
| `health_check.py` | **ACTIVE** | Pipeline health validator |
| `constants.py` | **ACTIVE** | Unified field names, thresholds, SLA hours |
| `notion_helpers.py` | **ACTIVE** | Shared Notion API utilities |
| `webhook_server.py` | **ACTIVE** | Apollo webhook receiver |
| `verify_links.py` | **ACTIVE** | Contact-company link verifier |
| `sync_companies.py` | Superseded | Replaced by `daily_sync.py --mode full` |
| `sync_contacts.py` | Superseded | Replaced by `daily_sync.py --mode full` |
| `apollo_sync_scheduler.py` | Superseded | Replaced by GitHub Actions + daily_sync.py |
| `initial_load_from_csv.py` | Completed | One-time use (completed) |

---
**Version:** 3.2 | **Last Updated:** 27 March 2026
