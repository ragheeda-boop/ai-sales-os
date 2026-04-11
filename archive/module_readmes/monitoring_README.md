# monitoring/ — Observability Layer

Scripts that report on system health and generate intelligence outputs.

## Scripts (currently in Phase 3 - Sync/)

| Script | Role |
|--------|------|
| `health_check.py` | Post-pipeline validator: checks 5 stats JSON files for anomalies |
| `dashboard_generator.py` (v4.2) | Live Notion data → Sales_Dashboard_Accounts.html |
| `morning_brief.py` (v4.0) | Daily: urgent calls, tasks, replies, pipeline summary |
| `score_calibrator.py` | Weekly review-only: recommends scoring weight adjustments |

## Health Check Stats Files Monitored
last_sync_stats.json | last_action_stats.json | last_meeting_tracker_stats.json
last_analyzer_stats.json | last_opportunity_stats.json
