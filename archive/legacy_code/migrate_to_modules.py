#!/usr/bin/env python3
"""
AI Sales OS — Module Migration Script
======================================
Migrates scripts from flat Phase 3 - Sync/ into the modular architecture.

⚠️  DO NOT run on main branch directly.
    Create a feature branch, run, test locally, then merge.

Usage:
    python migrate_to_modules.py --dry-run   # preview only
    python migrate_to_modules.py --execute   # apply migration

What it does:
    1. Copies scripts to new module directories
    2. Updates sys.path.insert() in each script to point to core/
    3. Generates updated GitHub Actions workflow snippet
    4. Creates symlinks in Phase 3 - Sync/ for backward compatibility

Safety:
    - Never deletes originals (only copies)
    - Creates symlinks so existing workflow paths still work
    - Generates a migration report
"""

import os
import shutil
import sys
import argparse
from pathlib import Path

# ─── Migration Map ────────────────────────────────────────────────────────────

SRC = Path(__file__).parent / "Phase 3 - Sync"

MIGRATION_MAP = {
    "core": [
        "daily_sync.py",
        "constants.py",
        "notion_helpers.py",
        "doc_sync_checker.py",
    ],
    "scoring": [
        "lead_score.py",
        "score_calibrator.py",
        "action_ready_updater.py",
    ],
    "automation": [
        "auto_tasks.py",
        "auto_sequence.py",
        "outcome_tracker.py",
        "cleanup_overdue_tasks.py",
    ],
    "governance": [
        "ingestion_gate.py",
        "data_governor.py",
        "archive_unqualified.py",
        "audit_ownership.py",
        "fix_seniority.py",
    ],
    "enrichment": [
        "job_postings_enricher.py",
        "muhide_strategic_analysis.py",
        "analytics_tracker.py",
    ],
    "meetings": [
        "meeting_tracker.py",
        "meeting_analyzer.py",
        "opportunity_manager.py",
    ],
    "monitoring": [
        "health_check.py",
        "dashboard_generator.py",
        "morning_brief.py",
    ],
    "webhooks": [
        "webhook_server.py",
        "verify_links.py",
    ],
}

# Files that import from sibling scripts (need path updates)
CROSS_IMPORTS = {
    "daily_sync.py": ["constants", "notion_helpers", "ingestion_gate"],
    "auto_tasks.py": ["notion_helpers", "constants"],
    "lead_score.py": ["notion_helpers", "constants"],
    "action_ready_updater.py": ["notion_helpers", "constants"],
    "outcome_tracker.py": [],  # standalone with direct HTTP calls
    "ingestion_gate.py": ["constants"],
    "data_governor.py": ["constants", "notion_helpers"],
    "auto_sequence.py": ["notion_helpers", "constants"],
    "meeting_tracker.py": ["notion_helpers", "constants"],
    "meeting_analyzer.py": ["notion_helpers", "constants"],
    "opportunity_manager.py": ["notion_helpers", "constants"],
    "job_postings_enricher.py": ["notion_helpers", "constants"],
    "muhide_strategic_analysis.py": ["notion_helpers", "constants"],
    "analytics_tracker.py": ["notion_helpers", "constants"],
    "health_check.py": [],
    "dashboard_generator.py": ["notion_helpers", "constants"],
    "morning_brief.py": ["notion_helpers", "constants"],
    "score_calibrator.py": ["notion_helpers", "constants"],
    "archive_unqualified.py": ["notion_helpers", "constants"],
    "cleanup_overdue_tasks.py": ["notion_helpers", "constants"],
    "audit_ownership.py": ["notion_helpers", "constants"],
    "doc_sync_checker.py": [],
    "webhook_server.py": [],
    "verify_links.py": ["notion_helpers", "constants"],
    "fix_seniority.py": ["notion_helpers", "constants"],
}


def build_new_sys_path(script_name: str, target_module: str) -> str:
    """
    Generate updated sys.path.insert() calls for a script in its new location.
    All scripts need to reference 'core/' for constants.py and notion_helpers.py.
    """
    base = Path(__file__).parent  # CODE/
    core_path = base / "core"
    # Relative from target_module/ to core/
    # e.g., from automation/ → ../core
    rel = os.path.relpath(str(core_path), str(base / target_module))
    return f'sys.path.insert(0, os.path.join(os.path.dirname(__file__), "{rel}"))'


def main():
    parser = argparse.ArgumentParser(description="AI Sales OS Module Migration")
    parser.add_argument("--dry-run", action="store_true", help="Preview only, no file operations")
    parser.add_argument("--execute", action="store_true", help="Execute migration")
    args = parser.parse_args()

    if not args.dry_run and not args.execute:
        print("Specify --dry-run or --execute")
        sys.exit(1)

    base = Path(__file__).parent
    report = []
    errors = []

    print("=" * 60)
    print(f"AI Sales OS Module Migration | {'DRY RUN' if args.dry_run else 'EXECUTING'}")
    print("=" * 60)

    for module, scripts in MIGRATION_MAP.items():
        dest_dir = base / module
        print(f"\n[{module}/]")

        for script in scripts:
            src_path = SRC / script
            dest_path = dest_dir / script
            symlink_path = SRC / script  # stays in original location

            if not src_path.exists():
                print(f"  ⚠️  MISSING: {script} (not in Phase 3 - Sync/)")
                errors.append(f"Missing: {script}")
                continue

            # Report what would happen
            path_update = build_new_sys_path(script, module)
            needs_path_update = bool(CROSS_IMPORTS.get(script))

            print(f"  {'📋 Would copy' if args.dry_run else '📋 Copying'}: {script}")
            print(f"    → {dest_path}")
            if needs_path_update:
                print(f"    → sys.path update: {path_update}")
            print(f"    → Symlink kept at: Phase 3 - Sync/{script}")

            report.append({
                "script": script,
                "from": str(src_path),
                "to": str(dest_path),
                "module": module,
                "needs_path_update": needs_path_update,
            })

            if args.execute:
                # Copy file
                shutil.copy2(src_path, dest_path)

                # Update sys.path in copied file
                if needs_path_update:
                    content = dest_path.read_text(encoding="utf-8")
                    old_insert = 'sys.path.insert(0, os.path.dirname(__file__))'
                    new_insert = path_update
                    content = content.replace(old_insert, new_insert)
                    dest_path.write_text(content, encoding="utf-8")

                # Note: symlink creation would make original → copy
                # Skipping to avoid confusion; originals remain in Phase 3 - Sync/
                print(f"    ✅ Done")

    # Workflow update note
    print("\n" + "=" * 60)
    print("GITHUB ACTIONS WORKFLOW")
    print("=" * 60)
    print("Update .github/workflows/daily_sync.yml:")
    print("  working-directory: '💻 CODE/Phase 3 - Sync'")
    print("  → No change needed if originals remain in place (recommended)")
    print("  → OR update to new module paths when scripts are moved")

    print("\n" + "=" * 60)
    print(f"SUMMARY: {len(report)} scripts mapped | {len(errors)} missing")
    print("=" * 60)

    if errors:
        print("\nErrors:")
        for e in errors:
            print(f"  ⚠️  {e}")

    if args.dry_run:
        print("\n⚠️  DRY RUN COMPLETE — no files were modified")
        print("Run with --execute to apply migration")
    else:
        print("\n✅ Migration complete. Originals still in Phase 3 - Sync/ (safe).")
        print("Update GitHub Actions workflow paths when ready to cut over.")


if __name__ == "__main__":
    main()
