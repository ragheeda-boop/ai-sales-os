---
name: apollo-sync-operator
description: "Operate, troubleshoot, and improve the Apollo-to-Notion sync pipeline. Use this skill whenever the user mentions syncing, Apollo data, daily_sync.py, incremental/backfill/full mode, sync errors, duplicate records, Apollo API issues, pagination problems, or anything about getting data from Apollo into Notion. Also trigger when the user asks about sync stats, last run results, or wants to run/schedule a sync."
---

# Apollo Sync Operator — AI Sales OS

You operate the Apollo → Notion synchronization engine. This is the data foundation that everything else depends on — scoring, tasks, and pipeline health all flow from sync quality.

## How the Sync Works

The engine is `daily_sync.py` (v2.3) in `💻 CODE/Phase 3 - Sync/`. It pulls data from Apollo's API and writes to Notion via `notion_helpers.py`.

### Three Modes

| Mode | When to Use | Command |
|------|-------------|---------|
| **incremental** | Daily use, GitHub Actions | `python daily_sync.py --mode incremental --hours 26` |
| **backfill** | Recover gaps, catch up after downtime | `python daily_sync.py --mode backfill --days 7` |
| **full** | First-time build or complete rebuild | `python daily_sync.py --mode full` |

Incremental uses a 26-hour window (not 24) to ensure 2 hours of overlap. The triple dedup (Apollo ID → Email → in-memory seen_ids) handles any duplicates from the overlap.

**Local Timestamp Filter (v2.3):** After fetching from Apollo, a client-side filter drops any record whose `updated_at` is before the requested `since` datetime. This is critical — Apollo's `contact_updated_at_range` filter uses day-granularity only and was previously returning all 44,877 contacts on every incremental run (causing 4-5h runtimes). With this fix, incremental runs complete in minutes.

Full mode uses alphabetical partitioning (A-Z + numbers) to work around Apollo's 50,000 result cap per search. Each letter gets its own query, keeping each partition well under the limit for ~45k contacts.

### Key Technical Details

- **Pre-loading:** Before any writes, loads ALL existing Notion records into memory (`preload_companies()`, `preload_contacts()`) to minimize API calls and enable update-vs-create decisions.
- **Rate limiting:** Built into `notion_helpers.py`. Apollo requests use `apollo_request()` with 5x exponential backoff on 429/500 errors.
- **Parallel workers:** `MAX_WORKERS = 3` for Notion writes via ThreadPoolExecutor.
- **Checkpoint resume:** Backfill mode saves `backfill_checkpoint.json` so interrupted runs can resume. Cleared on successful completion.
- **Safe boolean writing:** Lines 574-585 of `daily_sync.py` — only writes engagement checkboxes if Apollo explicitly returns the field. Prevents overwriting manual True with False.
- **Seniority normalization:** `_normalize_seniority()` at line 496 uses `SENIORITY_NORMALIZE` from constants.py to unify "C-Suite"/"C suite" variants.

### Data Flow

```
Apollo contacts/search API → format_contact_from_api() → Notion properties dict → create_page() or update_page()
Apollo accounts/search API → format_company_from_api() → Notion properties dict → create_page() or update_page()
```

Companies ALWAYS sync before contacts (contacts need company page IDs for relations).

### What Gets Written

**Companies:** Company Name, Domain, Website, Industry, Employees, Employee Size, Annual Revenue, Revenue Range, Total Funding, Latest Funding Amount, Last Raised At, City/State/Country/Address, Phone, LinkedIn/Facebook/Twitter, Keywords, Technologies, Short Description, Account Stage, Apollo Account Id, Record Source, Data Status.

**Contacts:** Full Name, First/Last Name, Email, Title, Seniority (normalized), City/State/Country, LinkedIn, Phone numbers (mapped by type), Apollo Contact/Account ID, Departments, Email Status, Stage, Outreach Status, engagement booleans (safe write), Last Contacted, Do Not Call, Record Source, Data Status, Company relation.

### Known Issues

1. **Stage is largely empty** — Apollo returns stage inconsistently. The code writes it (line 560) but ~85% of contacts have no value.
2. **Intent Scores are empty** — Primary/Secondary Intent Score fields exist but Apollo doesn't return data for them. Likely a plan limitation.
3. **No stats file output** — `daily_sync.py` logs a summary but doesn't write `last_sync_stats.json`. Health check looks for this file. Consider adding stats export.

## When Troubleshooting

If sync reports 0 records: check `APOLLO_API_KEY` validity, check Apollo rate limits, verify the date range isn't empty.

If high duplicate rate (>5%): check if time-window splitting is working correctly, verify dedup logic in `sync_contacts()`.

If company names look wrong: verify `format_company_from_api()` uses `"Company Name"` as the title field (this was a previous bug that has been fixed).

If booleans are being overwritten: verify the safe boolean pattern at lines 574-585 checks `if apollo_key in contact and contact[apollo_key] is not None`.

## GitHub Actions

The pipeline runs daily at 7 AM KSA (04:00 UTC) via `.github/workflows/daily_sync.yml` — **2 independent jobs** (each with its own 6h clock, 9h total capacity):

**Job 1 — sync-and-score (5h 50min timeout):**
1. Sync (`daily_sync.py --hours 26` — local timestamp filter makes this minutes not hours)
2. Enrich (`job_postings_enricher.py --limit 50`)
3. Lead Score (`lead_score.py`)
4. Action Ready (`action_ready_updater.py`)

**Job 2 — action-and-track (3h timeout, runs after Job 1):**
5. Auto Tasks, Sequences, Meeting Tracker/Analyzer, Opportunities, Analytics, Health Check, Morning Brief, Dashboard

Required secrets: `APOLLO_API_KEY`, `NOTION_API_KEY`, `NOTION_DATABASE_ID_CONTACTS`, `NOTION_DATABASE_ID_COMPANIES`, `NOTION_DATABASE_ID_TASKS`.

Always follow the shared rules in `shared-sales-os-rules`.
