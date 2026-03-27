---
name: pipeline-health-monitor
description: "Monitor daily pipeline health, detect failures, and alert on anomalies in AI Sales OS. Use this skill when the user asks about pipeline status, health checks, 'did the sync run today?', 'is everything working?', error investigation, log analysis, failure detection, or wants a daily operations report. Also trigger when checking if GitHub Actions ran successfully or when reviewing last_sync_stats.json / last_action_stats.json."
---

# Pipeline Health Monitor — AI Sales OS

You monitor the operational health of the entire AI Sales OS pipeline. The system runs daily without human intervention — your job is to catch when things go wrong before anyone notices.

## Pipeline Flow (Daily at 7 AM KSA)

```
Step 1: daily_sync.py --mode incremental --hours 26
Step 2: lead_score.py
Step 3: action_ready_updater.py
Step 4: auto_tasks.py (continue-on-error)
Step 5: health_check.py
Step 6: Upload logs (30-day retention)
Step 7: Notify on failure
```

Managed by `.github/workflows/daily_sync.yml`.

## Health Check Script (`health_check.py`)

Reads stats files and checks for anomalies:

### Checks Performed

| Check | Level | Condition |
|-------|-------|-----------|
| Zero records processed | CRITICAL | created + updated = 0 |
| High duplicate rate | WARNING | duplicates/fetched > 5% |
| Failed records | WARNING | failed_contacts + failed_companies > 0 |
| Action Engine errors | WARNING | errors > 0 in action stats |
| Zero tasks created | INFO | created = 0 (may be normal) |

### Thresholds (from code)

```python
THRESHOLDS = {
    "min_records_processed": 1,
    "max_duplicate_rate": 0.05,
    "max_runtime_minutes": 60,
}
```

## Stats Files

**`last_sync_stats.json`** — Written by sync (if implemented):
```json
{
    "apollo_fetched_contacts": 150,
    "apollo_fetched_accounts": 30,
    "notion_created_contacts": 12,
    "notion_updated_contacts": 138,
    "notion_created_companies": 2,
    "notion_updated_companies": 28,
    "duplicates_prevented": 5,
    "failed_contacts": 0,
    "failed_companies": 0
}
```

**`last_action_stats.json`** — Written by auto_tasks.py:
```json
{
    "created": 42,
    "skipped_open_task": 15,
    "skipped_blocked": 3,
    "skipped_no_rule": 0,
    "errors": 0
}
```

## Log Files

All in `💻 CODE/Phase 3 - Sync/`:
- `daily_sync.log` — Sync execution details
- `lead_score.log` — Scoring results and distribution
- `action_ready.log` — Action Ready updates
- `auto_tasks.log` — Task creation details
- `health_check.log` — Health check results

## Baseline Metrics (March 2026)

- Total contacts: 44,875
- Total companies: 15,407
- HOT leads: 100+ (exact count unknown, has_more=True)
- Average HOT score: 93.5
- Tasks created: depends on first full run
- Daily sync volume: depends on Apollo activity

## When Investigating Issues

1. **Sync failed:** Check `daily_sync.log` for API errors, rate limits, or connection issues. Verify `APOLLO_API_KEY` is valid.
2. **Zero records:** Could be normal if no Apollo records were updated in the last 26 hours. Check if it's a weekend or holiday.
3. **High duplicates:** Check if time-window splitting triggered, or if there's a pagination issue.
4. **Task errors:** Check `auto_tasks.log` for Notion API errors. Common cause: Tasks DB Status field type mismatch.
5. **Scoring anomalies:** Check if company employee data changed, or if engagement data was overwritten.

## Commands

```bash
python health_check.py          # run all checks
python health_check.py --strict # exit 1 on any warning (not just critical)
```

Always follow the shared rules in `shared-sales-os-rules`.
