#!/usr/bin/env python3
"""
AI Sales OS — Documentation Sync Checker
doc_sync_checker.py

Validates that key documentation facts match the actual codebase state.
Run this after any development session to catch documentation drift before it compounds.

Checks:
  - Script count in CLAUDE.md vs actual scripts in CODE folder
  - Pipeline step count in docs vs actual steps in daily_sync.yml
  - .env.example DB IDs vs documented requirements
  - Phase status in CLAUDE.md vs actual files present

Usage:
    python doc_sync_checker.py              # run all checks, print report
    python doc_sync_checker.py --strict     # exit 1 if any drift found
    python doc_sync_checker.py --fix-hints  # show exact fix commands
"""

import os
import re
import sys
import glob
import argparse
from pathlib import Path

# ─── Paths ────────────────────────────────────────────────────────────────────

SCRIPT_DIR = Path(__file__).resolve().parent       # absolute path always
PROJECT_ROOT = SCRIPT_DIR.parent.parent            # Phase 3 - Sync → 💻 CODE → AI Sales OS

CLAUDE_MD = PROJECT_ROOT / "CLAUDE.md"
SYSTEM_OVERVIEW = PROJECT_ROOT / "🚀 START HERE" / "SYSTEM_OVERVIEW.md"
QUICK_START = PROJECT_ROOT / "🚀 START HERE" / "QUICK_START.md"
WORKFLOW_FILE = PROJECT_ROOT / ".github" / "workflows" / "daily_sync.yml"
ENV_EXAMPLE = SCRIPT_DIR / ".env.example"
CODE_DIR = SCRIPT_DIR

# ─── Check functions ──────────────────────────────────────────────────────────

def check_script_count():
    """Count actual .py scripts (excluding venv) vs documented count."""
    issues = []

    # Count actual production scripts (exclude .venv, exclude superseded)
    actual_scripts = [
        f for f in CODE_DIR.glob("*.py")
        if not str(f).endswith(("sync_companies.py", "sync_contacts.py",
                                "apollo_sync_scheduler.py", "initial_load_from_csv.py"))
    ]
    actual_count = len(actual_scripts)

    # Read documented count from CLAUDE.md
    claude_text = CLAUDE_MD.read_text(encoding="utf-8") if CLAUDE_MD.exists() else ""
    system_text = SYSTEM_OVERVIEW.read_text(encoding="utf-8") if SYSTEM_OVERVIEW.exists() else ""

    for text, filename in [(claude_text, "CLAUDE.md"), (system_text, "SYSTEM_OVERVIEW.md")]:
        # Match both "Python Scripts (18 scripts)" and "Python Scripts (18)"
        matches = re.findall(r"Python Scripts \((\d+)(?:\s+scripts)?\)", text)
        for match in matches:
            doc_count = int(match)
            if doc_count != actual_count:
                issues.append({
                    "file": filename,
                    "check": "Script Count",
                    "found": f"Python Scripts ({doc_count})",
                    "expected": f"Python Scripts ({actual_count})",
                    "severity": "HIGH"
                })

    return actual_count, actual_scripts, issues


def check_pipeline_steps():
    """Count actual steps in daily_sync.yml vs documented step count."""
    issues = []

    if not WORKFLOW_FILE.exists():
        return 0, []

    workflow_text = WORKFLOW_FILE.read_text(encoding="utf-8")

    # Count named steps in the MAIN daily sync job only.
    # Strategy: find the first job block and count its '- name:' entries,
    # stopping before the next top-level job definition.
    # We look for step names that belong to the primary pipeline job (not weekly).
    # The weekly job is identified by its schedule trigger — steps after its
    # '- name: "⬇️ Checkout"' (no emoji) are part of the weekly job.
    # Simpler: count all '- name:' entries in the main job section
    # (lines 1 through the weekly job boundary).
    lines = workflow_text.splitlines()
    in_weekly_job = False
    main_step_count = 0
    for line in lines:
        # Detect weekly calibration job boundary (second top-level job key)
        stripped = line.strip()
        if re.match(r'^weekly-calibration:', stripped) or re.match(r'^calibration:', stripped):
            in_weekly_job = True
        if not in_weekly_job and re.match(r'- name:', stripped):
            # Exclude the failure notification step (it's conditional, not a pipeline step)
            main_step_count += 1
    # Subtract 1 for the "Notify on Failure" conditional step (always at end of main job)
    actual_steps = max(0, main_step_count - 1)

    # Check docs
    for doc_file in [CLAUDE_MD, SYSTEM_OVERVIEW, QUICK_START]:
        if not doc_file.exists():
            continue
        text = doc_file.read_text(encoding="utf-8")
        matches = re.findall(r"(\d+)-step pipeline", text)
        for match in matches:
            doc_steps = int(match)
            if doc_steps != actual_steps:
                issues.append({
                    "file": doc_file.name,
                    "check": "Pipeline Step Count",
                    "found": f"{doc_steps}-step pipeline",
                    "expected": f"{actual_steps}-step pipeline",
                    "severity": "MEDIUM"
                })

    return actual_steps, issues


def check_env_variables():
    """Check that .env.example has all documented required variables."""
    issues = []

    if not ENV_EXAMPLE.exists():
        issues.append({
            "file": ".env.example",
            "check": "File exists",
            "found": "MISSING",
            "expected": ".env.example file",
            "severity": "HIGH"
        })
        return issues

    env_text = ENV_EXAMPLE.read_text(encoding="utf-8")

    required_vars = [
        "APOLLO_API_KEY",
        "NOTION_API_KEY",
        "NOTION_DATABASE_ID_CONTACTS",
        "NOTION_DATABASE_ID_COMPANIES",
        "NOTION_DATABASE_ID_TASKS",
        "NOTION_DATABASE_ID_MEETINGS",
        "NOTION_DATABASE_ID_OPPORTUNITIES",
    ]

    for var in required_vars:
        if var not in env_text:
            issues.append({
                "file": ".env.example",
                "check": "Required ENV var",
                "found": f"{var} MISSING",
                "expected": f"{var} present",
                "severity": "HIGH"
            })

    return issues


def check_new_scripts_documented():
    """Check that all production scripts in the CODE dir are mentioned in CLAUDE.md."""
    issues = []

    if not CLAUDE_MD.exists():
        return issues

    claude_text = CLAUDE_MD.read_text(encoding="utf-8")

    skip = {"__init__", "test_", "setup", "conftest"}
    scripts = [
        f.stem for f in CODE_DIR.glob("*.py")
        if not any(s in f.stem for s in skip)
        and ".venv" not in str(f)
    ]

    for script in scripts:
        if script not in claude_text:
            issues.append({
                "file": "CLAUDE.md",
                "check": "Script documented",
                "found": f"`{script}.py` NOT in CLAUDE.md",
                "expected": f"`{script}.py` mentioned in CLAUDE.md",
                "severity": "MEDIUM"
            })

    return issues


def check_phase_status():
    """Check that Phase statuses in CLAUDE.md match what's actually built."""
    issues = []

    if not CLAUDE_MD.exists():
        return issues

    claude_text = CLAUDE_MD.read_text(encoding="utf-8")

    # Phase 3.5 scripts — if they exist, Phase 3.5 should be marked complete
    phase_35_scripts = ["meeting_tracker.py", "meeting_analyzer.py", "opportunity_manager.py"]
    phase_35_built = all((CODE_DIR / s).exists() for s in phase_35_scripts)

    if phase_35_built and "Phase 3.5" not in claude_text:
        issues.append({
            "file": "CLAUDE.md",
            "check": "Phase 3.5 documented",
            "found": "Phase 3.5 scripts exist but not in CLAUDE.md",
            "expected": "Phase 3.5 section in CLAUDE.md",
            "severity": "HIGH"
        })

    return issues


def check_notion_page_alignment():
    """Remind about Notion pages that likely need updating when code changes."""
    reminders = []

    # Check if there's a recent git commit that changed scripts but docs look old
    notion_pages = [
        "🔁 Autonomous Loop Dashboard — update step count if pipeline changed",
        "🚀 Command Center — update Daily Pipeline section if scripts added/removed",
        "📚 SOPs & Workflow Reference — update if Action Ready conditions or SLA changed",
        "🧠 Claude Skills — update skill SKILL.md files if new scripts added",
    ]

    reminders.extend(notion_pages)
    return reminders


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="AI Sales OS — Documentation Sync Checker")
    parser.add_argument("--strict", action="store_true", help="Exit 1 if any drift found")
    parser.add_argument("--fix-hints", action="store_true", help="Show fix commands")
    args = parser.parse_args()

    print("=" * 70)
    print("AI SALES OS — DOCUMENTATION SYNC CHECKER")
    print("=" * 70)
    print()

    all_issues = []

    # ── Check 1: Script count
    print("🔍 Checking script count...")
    actual_count, scripts, issues = check_script_count()
    print(f"   Actual production scripts: {actual_count}")
    for s in sorted(scripts):
        print(f"   • {s.name}")
    all_issues.extend(issues)

    # ── Check 2: Pipeline steps
    print()
    print("🔍 Checking pipeline step count...")
    actual_steps, issues = check_pipeline_steps()
    print(f"   Actual pipeline script calls: {actual_steps}")
    all_issues.extend(issues)

    # ── Check 3: ENV variables
    print()
    print("🔍 Checking .env.example variables...")
    issues = check_env_variables()
    if not issues:
        print("   ✅ All required variables present")
    all_issues.extend(issues)

    # ── Check 4: Scripts documented in CLAUDE.md
    print()
    print("🔍 Checking all scripts documented in CLAUDE.md...")
    issues = check_new_scripts_documented()
    if not issues:
        print("   ✅ All scripts mentioned in CLAUDE.md")
    all_issues.extend(issues)

    # ── Check 5: Phase status
    print()
    print("🔍 Checking phase status alignment...")
    issues = check_phase_status()
    if not issues:
        print("   ✅ Phase statuses aligned")
    all_issues.extend(issues)

    # ── Notion reminders
    print()
    print("📋 Notion pages to manually verify after code changes:")
    for reminder in check_notion_page_alignment():
        print(f"   • {reminder}")

    # ── Summary
    print()
    print("=" * 70)
    if all_issues:
        print(f"⚠️  DRIFT DETECTED — {len(all_issues)} issue(s) found:\n")
        high = [i for i in all_issues if i["severity"] == "HIGH"]
        medium = [i for i in all_issues if i["severity"] == "MEDIUM"]

        for i in high + medium:
            sev_icon = "🔴" if i["severity"] == "HIGH" else "🟡"
            print(f"  {sev_icon} [{i['severity']}] {i['file']} — {i['check']}")
            print(f"     Found:    {i['found']}")
            print(f"     Expected: {i['expected']}")
            print()

        if args.fix_hints:
            print("\n💡 Fix Hints:")
            print("  • Script count: Update 'Python Scripts (N)' in CLAUDE.md + SYSTEM_OVERVIEW.md")
            print("  • Pipeline steps: Update 'N-step pipeline' in all docs")
            print("  • ENV vars: Add missing vars to .env.example")
            print("  • New scripts: Add script section to CLAUDE.md Active Scripts table")
            print("  • Phase 3.5: Add Phase 3.5 row to CLAUDE.md Execution Plan")

        if args.strict:
            print("\n❌ Strict mode: exiting with code 1")
            sys.exit(1)
    else:
        print("✅ All documentation checks passed — no drift detected.")

    print("=" * 70)


if __name__ == "__main__":
    main()
