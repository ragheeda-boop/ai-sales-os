"""
run_muqawil_pipeline.py — Master orchestrator for Muqawil contractor pipeline
Runs all pipeline steps in order with logging and error handling.

Steps:
  Step 1: 01_clean_deduplicate.py   — Clean + deduplicate scraped data
  Step 2: 05_rules_engine.py        — Apply priority/stage/status rules
  Step 3: 03_apollo_matcher.py      — Match against Apollo CRM
  Step 4: 04_gmail_outreach_check.py — Check Gmail for previous outreach
  Step 5: 05_rules_engine.py        — Re-apply rules after Apollo/Gmail signals
  Step 6: 02_notion_sync.py         — Push new records to Notion (incremental)

Usage:
  python run_muqawil_pipeline.py              # full pipeline (all steps)
  python run_muqawil_pipeline.py --step 2     # run only step 2
  python run_muqawil_pipeline.py --from-step 3 # start from step 3
  python run_muqawil_pipeline.py --dry-run    # dry-run all steps
  python run_muqawil_pipeline.py --notion-only # only push to Notion (step 6)

Schedule: Run daily via Windows Task Scheduler or manually after scraper finishes.
"""

import sys, os, subprocess, time, argparse, logging
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).parent
PYTHON   = str(Path(sys.executable))
LOG_FILE = BASE_DIR / "pipeline_run.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger(__name__)

STEPS = [
    (1, "01_clean_deduplicate.py",    []),
    (2, "05_rules_engine.py",         []),
    (3, "03_apollo_matcher.py",       ["--limit", "500"]),   # limit per run (Apollo quota)
    (4, "04_gmail_outreach_check.py", []),
    (5, "05_rules_engine.py",         []),                   # re-run after signals
    (6, "02_notion_sync.py",          []),                   # incremental push
]

def run_step(script: str, extra_args: list, dry_run: bool) -> bool:
    script_path = BASE_DIR / script
    cmd = [PYTHON, str(script_path)] + extra_args
    if dry_run:
        cmd.append("--dry-run")

    log.info("── Running: %s %s", script, " ".join(extra_args))
    t0 = time.time()
    try:
        result = subprocess.run(cmd, capture_output=False, timeout=7200)
        elapsed = time.time() - t0
        if result.returncode == 0:
            log.info("── OK: %s (%.0fs)", script, elapsed)
            return True
        else:
            log.error("── FAILED: %s (exit %d, %.0fs)", script, result.returncode, elapsed)
            return False
    except subprocess.TimeoutExpired:
        log.error("── TIMEOUT: %s after 2 hours", script)
        return False
    except Exception as e:
        log.error("── ERROR running %s: %s", script, e)
        return False

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run",    action="store_true")
    parser.add_argument("--step",       type=int, help="Run only this step number")
    parser.add_argument("--from-step",  type=int, default=1, help="Start from this step")
    parser.add_argument("--notion-only",action="store_true", help="Only run step 6 (Notion sync)")
    parser.add_argument("--skip-apollo",action="store_true", help="Skip Apollo matcher (step 3)")
    parser.add_argument("--skip-gmail", action="store_true", help="Skip Gmail check (step 4)")
    args = parser.parse_args()

    log.info("=" * 60)
    log.info("Muqawil Pipeline — %s", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"))
    log.info("Mode: %s", "DRY-RUN" if args.dry_run else "LIVE")
    log.info("=" * 60)

    if args.notion_only:
        steps = [(6, "02_notion_sync.py", [])]
    elif args.step:
        steps = [s for s in STEPS if s[0] == args.step]
    else:
        steps = [s for s in STEPS if s[0] >= args.from_step]

    if args.skip_apollo:
        steps = [s for s in steps if s[0] != 3]
    if args.skip_gmail:
        steps = [s for s in steps if s[0] != 4]

    results = {}
    for step_num, script, extra_args in steps:
        log.info("")
        log.info("STEP %d: %s", step_num, script)
        ok = run_step(script, extra_args, args.dry_run)
        results[step_num] = ok
        if not ok:
            log.error("Pipeline stopped at step %d. Fix and rerun with --from-step %d", step_num, step_num)
            break
        time.sleep(1)

    log.info("")
    log.info("=" * 60)
    log.info("PIPELINE SUMMARY:")
    for step_num, ok in results.items():
        script = next(s[1] for s in STEPS if s[0] == step_num)
        status = "✓ OK" if ok else "✗ FAILED"
        log.info("  Step %d: %-35s %s", step_num, script, status)
    all_ok = all(results.values())
    log.info("Result: %s", "ALL OK" if all_ok else "FAILED")
    log.info("=" * 60)
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
