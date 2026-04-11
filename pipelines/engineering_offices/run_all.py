#!/usr/bin/env python3
"""
run_all.py
==========
Master orchestrator for the Engineering Offices Follow-up System
مكاتب هندسية - وزارة الاسكان

Runs the full pipeline in order:
  Phase 1: Clean & deduplicate raw CSV data
  Phase 2: Sync cleaned companies to Notion DB
  Phase 3: Match companies to Apollo accounts/contacts
  Phase 4: Sync Apollo sequence activity to Notion
  Phase 5: Apply follow-up rules engine (compute stages, priorities, actions)

Each phase is skippable. The pipeline is idempotent — safe to re-run.

Run:
    python run_all.py                       # full pipeline
    python run_all.py --dry-run             # preview only, no writes
    python run_all.py --skip-clean          # skip Phase 1 (use existing cleaned_offices.json)
    python run_all.py --skip-sync           # skip Phase 2
    python run_all.py --skip-match          # skip Phase 3
    python run_all.py --skip-activity       # skip Phase 4
    python run_all.py --skip-rules          # skip Phase 5
    python run_all.py --phases 1,2          # run only phases 1 and 2
    python run_all.py --phases 4,5          # daily update — activity + rules only
"""

import subprocess, sys, time, json, argparse, logging
from pathlib import Path
from datetime import datetime

# ───────────────────────────────────────────────
# Logging
# ───────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("run_all.log", encoding="utf-8"),
    ],
)
log = logging.getLogger(__name__)

# ───────────────────────────────────────────────
# Phase definitions
# ───────────────────────────────────────────────

PHASES = [
    {
        "id": 1,
        "name": "Clean & Deduplicate",
        "script": "clean_engineering_offices.py",
        "args": [],
        "description": "Read CSVs, clean Arabic text, normalize phones/emails, deduplicate",
    },
    {
        "id": 2,
        "name": "Sync to Notion",
        "script": "notion_engineering_sync.py",
        "args": [],
        "description": "Push cleaned companies to Notion DB (create/update)",
    },
    {
        "id": 3,
        "name": "Apollo Match",
        "script": "apollo_engineering_matcher.py",
        "args": ["--unmatched-only"],
        "description": "Match companies to Apollo accounts and contacts",
    },
    {
        "id": 4,
        "name": "Activity Sync",
        "script": "apollo_activity_sync.py",
        "args": ["--days", "90"],
        "description": "Pull Apollo sequence activity (sent, opened, replied)",
    },
    {
        "id": 5,
        "name": "Rules Engine",
        "script": "followup_rules_engine.py",
        "args": [],
        "description": "Evaluate follow-up stages, priorities, and next actions",
    },
]


# ───────────────────────────────────────────────
# Runner
# ───────────────────────────────────────────────

def run_phase(phase: dict, dry_run: bool = False, extra_args: list = None) -> bool:
    """
    Run a single phase. Returns True on success, False on failure.
    """
    script = Path(__file__).parent / phase["script"]
    cmd = [sys.executable, str(script)]

    if dry_run:
        cmd.append("--dry-run")

    if extra_args:
        cmd.extend(extra_args)
    elif phase.get("args"):
        cmd.extend(phase["args"])

    log.info(f"▶  Running: {' '.join(str(c) for c in cmd)}")
    start = time.time()

    try:
        result = subprocess.run(cmd, cwd=str(script.parent), capture_output=False, text=True)
        elapsed = time.time() - start
        if result.returncode == 0:
            log.info(f"✅  Phase {phase['id']} completed in {elapsed:.1f}s")
            return True
        else:
            log.error(f"❌  Phase {phase['id']} failed (exit {result.returncode}) after {elapsed:.1f}s")
            return False
    except Exception as e:
        log.error(f"❌  Phase {phase['id']} crashed: {e}")
        return False


# ───────────────────────────────────────────────
# Main
# ───────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Engineering Offices Follow-up System — Master Orchestrator"
    )
    parser.add_argument("--dry-run", action="store_true", help="No writes in any phase")
    parser.add_argument("--skip-clean",    action="store_true", help="Skip Phase 1")
    parser.add_argument("--skip-sync",     action="store_true", help="Skip Phase 2")
    parser.add_argument("--skip-match",    action="store_true", help="Skip Phase 3")
    parser.add_argument("--skip-activity", action="store_true", help="Skip Phase 4")
    parser.add_argument("--skip-rules",    action="store_true", help="Skip Phase 5")
    parser.add_argument("--phases", type=str, default="", help="Comma-separated phase IDs to run (e.g. '1,2')")
    parser.add_argument("--continue-on-error", action="store_true", help="Continue pipeline even if a phase fails")
    args = parser.parse_args()

    # Determine which phases to run
    skip_map = {
        1: args.skip_clean,
        2: args.skip_sync,
        3: args.skip_match,
        4: args.skip_activity,
        5: args.skip_rules,
    }

    if args.phases:
        requested = set(int(p.strip()) for p in args.phases.split(","))
        phases_to_run = [p for p in PHASES if p["id"] in requested]
    else:
        phases_to_run = [p for p in PHASES if not skip_map.get(p["id"], False)]

    # Print pipeline header
    print("\n" + "═"*65)
    print("   مكاتب هندسية - وزارة الاسكان  |  Follow-up System Pipeline")
    print("═"*65)
    print(f"  Run time:  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Dry run:   {args.dry_run}")
    print(f"  Phases:    {', '.join(str(p['id']) for p in phases_to_run)}")
    print("═"*65)
    for p in phases_to_run:
        print(f"  Phase {p['id']}: {p['name']}")
        print(f"          {p['description']}")
    print("═"*65 + "\n")

    if not phases_to_run:
        log.warning("No phases selected to run.")
        return

    pipeline_start = time.time()
    results = {}

    for phase in phases_to_run:
        print(f"\n{'─'*65}")
        print(f"  Phase {phase['id']}: {phase['name'].upper()}")
        print(f"{'─'*65}")
        log.info(f"⚙️  Starting Phase {phase['id']}: {phase['name']}")

        success = run_phase(phase, dry_run=args.dry_run)
        results[phase["id"]] = success

        if not success and not args.continue_on_error:
            log.error(f"💥  Pipeline aborted at Phase {phase['id']}.")
            log.error("    Use --continue-on-error to keep going despite failures.")
            break

        time.sleep(1)  # Small pause between phases

    # ── Final summary ─────────────────────────────
    elapsed = time.time() - pipeline_start
    print("\n" + "═"*65)
    print("   PIPELINE COMPLETE")
    print("═"*65)
    for pid, success in results.items():
        phase = next(p for p in PHASES if p["id"] == pid)
        status = "✅ OK" if success else "❌ FAILED"
        print(f"  Phase {pid}: {phase['name']:<25} {status}")
    print()
    print(f"  Total time: {elapsed:.1f}s ({elapsed/60:.1f} min)")
    if args.dry_run:
        print("\n  ⚠️  DRY RUN — no changes were written")
    print("═"*65 + "\n")

    # Save pipeline run record
    run_record = {
        "run_at": datetime.utcnow().isoformat(),
        "dry_run": args.dry_run,
        "phases_run": list(results.keys()),
        "results": {str(k): v for k, v in results.items()},
        "elapsed_seconds": elapsed,
    }
    record_path = Path(__file__).parent / "last_pipeline_run.json"
    with open(record_path, "w", encoding="utf-8") as f:
        json.dump(run_record, f, ensure_ascii=False, indent=2)
    log.info(f"📊  Pipeline record saved → {record_path}")

    # Exit with error if any phase failed
    if not all(results.values()):
        sys.exit(1)


if __name__ == "__main__":
    main()
