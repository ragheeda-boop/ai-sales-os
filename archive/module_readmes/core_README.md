# core/ — Engine Layer

Fundamental scripts that power the entire system. Every other module depends on these.

## Scripts (currently in Phase 3 - Sync/)

| Script | Role |
|--------|------|
| `daily_sync.py` (v4.0) | Apollo → Notion sync engine. 3 modes: incremental/backfill/full |
| `constants.py` | Single source of truth: all field names, thresholds, SLA hours |
| `notion_helpers.py` | Shared Notion API utilities: create, update, preload, rate limiter |
| `doc_sync_checker.py` | Documentation drift validator — run after every dev session |

## Key Facts
- constants.py must be loaded before ANY other script
- notion_helpers.py is imported by 15+ scripts — changes here affect everything
- daily_sync.py v4.0 (CLAUDE.md previously said v3.0 — now corrected)
