# AI Sales OS — Module Architecture Plan

## Current State
All 26 active scripts live flat in `Phase 3 - Sync/`. This works but causes:
- Unclear ownership of each script's domain
- Import complexity as scripts cross-reference each other
- Hard to navigate at a glance

## Target Architecture (implemented here as directories)

```
CODE/
├── Phase 3 - Sync/        ← CURRENT: All scripts live here (PRODUCTION - do not break)
│
├── core/                  ← Engine: sync, constants, Notion helpers
├── scoring/               ← Lead Score, Sort Score, Calibrator
├── automation/            ← Action Engine, Sequences, Outcome Tracker
├── governance/            ← Ingestion Gate, Data Governor, Archival
├── enrichment/            ← Job Postings, MUHIDE Analysis, Analytics
├── meetings/              ← Meeting Tracker, Analyzer, Opportunity Manager
├── monitoring/            ← Health Check, Dashboard, Morning Brief
├── webhooks/              ← Webhook Server, Verify Links
│
├── muqawil_pipeline/      ← Contractors pipeline (existing, undocumented until now)
└── engineering-offices/   ← Ministry offices pipeline (existing, currently inactive)
```

## Module Mapping

| Module | Scripts |
|--------|---------|
| `core/` | daily_sync.py, constants.py, notion_helpers.py, doc_sync_checker.py |
| `scoring/` | lead_score.py, score_calibrator.py, action_ready_updater.py |
| `automation/` | auto_tasks.py, auto_sequence.py, outcome_tracker.py, cleanup_overdue_tasks.py |
| `governance/` | ingestion_gate.py, data_governor.py, archive_unqualified.py, audit_ownership.py, fix_seniority.py |
| `enrichment/` | job_postings_enricher.py, muhide_strategic_analysis.py, analytics_tracker.py |
| `meetings/` | meeting_tracker.py, meeting_analyzer.py, opportunity_manager.py |
| `monitoring/` | health_check.py, dashboard_generator.py, morning_brief.py |
| `webhooks/` | webhook_server.py, verify_links.py |

## Migration Status: PLANNED (NOT YET EXECUTED)

⚠️ Files have NOT been moved. Moving Python scripts requires:
1. Updating all `sys.path.insert()` calls in each script
2. Updating GitHub Actions workflow (`.github/workflows/daily_sync.yml`) paths
3. Updating cross-script imports (`from ingestion_gate import ...`, etc.)
4. Testing in a branch before merging to main

### Migration Steps (when ready)

```bash
# 1. Create a migration branch
git checkout -b refactor/modular-structure

# 2. Run the migration script (creates symlinks for backward compatibility)
python migrate_to_modules.py

# 3. Test locally
python core/daily_sync.py --mode incremental --dry-run
python scoring/lead_score.py --dry-run

# 4. Update GitHub Actions workflow paths
# 5. Push and test in CI before merging
```

## Why NOT to move files immediately

The current `Phase 3 - Sync/` directory is referenced by:
- `.github/workflows/daily_sync.yml` (all script paths hardcoded)
- Cross-imports: `daily_sync.py` imports `ingestion_gate`, `constants`, `notion_helpers`
- `sys.path.insert(0, os.path.dirname(__file__))` assumes sibling file access

Moving files without updating all three will break the 7:00 AM KSA daily production run.

## Interim Recommendation

Until migration is executed:
- All production scripts remain in `Phase 3 - Sync/`
- Use the directory names above as LOGICAL groupings in your mind / documentation
- New scripts should be created with the module structure in mind
