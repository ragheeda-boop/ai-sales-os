# v7.0 Archived Scripts — 2026-04-14

These scripts were archived as part of the v7.0 Blueprint execution.
They are preserved here for reference but are no longer part of the active system.

| Script | Original Location | Reason |
|--------|-------------------|--------|
| ai_decision_engine.py | scripts/scoring/ | Superseded by company_priority_scorer.py (Decision Layer v7.0) |
| ai_action_executor.py | scripts/automation/ | Incomplete, conflicts with auto_tasks.py v2.0 |
| ai_sequence_generator.py | scripts/automation/ | Never used in production, dead code |
| call_script_builder.py | scripts/automation/ | Never used in production, dead code — replaced by AI Call Hook field |
| cleanup_overdue_tasks.py | scripts/automation/ | One-time migration tool, already executed post-v5.0 |
| archive_unqualified.py | scripts/governance/ | Superseded by data_governor.py v6.1 |
| fix_seniority.py | scripts/governance/ | One-time migration (C suite → C-Suite), already executed |
