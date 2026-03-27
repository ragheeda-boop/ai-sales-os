# AI Sales OS

**Apollo + Notion + Python + GitHub Actions** — Unified sales intelligence platform.

44,875 contacts | 15,407 companies | 3 sync modes | Lead scoring | Automated pipeline

## Architecture

```
Apollo.io  ──►  Python Scripts  ──►  Notion  ──►  GitHub Actions
(Data)          (Sync + Score)      (CRM Hub)     (Daily Cron)
```

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

## Key Scripts

| Script | Purpose | Usage |
|--------|---------|-------|
| `daily_sync.py` | Apollo → Notion sync (3 modes) | `--mode incremental/backfill/full` |
| `lead_score.py` | Calculate Lead Score (0-100) | `--force` to recalculate all |
| `notion_helpers.py` | Shared Notion API utilities | Imported by other scripts |

## Sync Modes

| Mode | Description | When to Use |
|------|-------------|-------------|
| **incremental** | Last N hours/days | Daily automated sync |
| **backfill** | Historical with checkpoint | Gap recovery, catch-up |
| **full** | All records (alphabetical partitioning) | First-time setup, full rebuild |

## Lead Score Formula

```
Score = (Intent × 40%) + (Engagement × 35%) + (Size × 15%) + (Seniority × 10%)
```

| View | Score | Purpose |
|------|-------|---------|
| HOT LEADS | >= 80 | Immediate outreach |
| WARM LEADS | 50-79 | Nurture and follow-up |
| COLD LEADS | < 50 | Monitor only |

## Folder Structure

```
AI Sales OS/
├── 💻 CODE/Phase 3 - Sync/    → Production scripts
│   ├── daily_sync.py           → Main sync engine (v2.0)
│   ├── lead_score.py           → Lead scoring engine
│   ├── notion_helpers.py       → Shared utilities
│   ├── webhook_server.py       → Apollo webhook receiver
│   └── .env                    → API credentials (not in git)
├── 📊 DATA/
│   ├── Import CSVs/            → Original import files
│   ├── Mapping Files/          → Apollo ↔ Notion field mappings
│   ├── Notion Snapshots/       → Database JSON exports
│   └── Logs/                   → Sync run logs
├── 📚 DOCUMENTATION/
│   ├── EXECUTION_PLAN_v3.0.docx → Current execution plan
│   ├── Phase 1-3/              → Phase-specific documentation
│   └── System Architecture/    → Field mapping, technical reference
├── .github/workflows/          → GitHub Actions (daily pipeline)
├── AI_Sales_OS_MindMap.html    → Interactive project mind map
└── 🗂️ ARCHIVED/               → Superseded files and old phases
```

## GitHub Actions

Daily pipeline runs at **7:00 AM KSA** (04:00 UTC):
1. `daily_sync.py --mode incremental` → Sync new/updated records
2. `lead_score.py` → Recalculate scores

Manual trigger available with mode selection from GitHub UI.

**Required Secrets:** `APOLLO_API_KEY`, `NOTION_API_KEY`, `NOTION_DATABASE_ID_CONTACTS`, `NOTION_DATABASE_ID_COMPANIES`

## Current Status

See `EXECUTION_PLAN_v3.0.docx` for full details or open `AI_Sales_OS_MindMap.html` for interactive overview.

**Version:** 3.0 | **Date:** 27 March 2026 | **Contacts:** 44,875 | **Companies:** 15,407
