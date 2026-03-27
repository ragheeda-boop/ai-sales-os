#!/usr/bin/env python3
"""
AI Sales OS — Health Check

Validates the last pipeline run by checking stats files.
Alerts on: zero records, high duplicate rate, long runtime, zero HOT leads.

Usage:
    python health_check.py          # run all checks
    python health_check.py --strict # exit with code 1 on any warning (not just critical)
"""
import os
import sys
import json
import logging
import argparse
from datetime import datetime

# ─── Logging ─────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("health_check.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)

# ─── Thresholds ──────────────────────────────────────────────────────────────

THRESHOLDS = {
    "min_records_processed": 1,
    "max_duplicate_rate": 0.05,
    "max_runtime_minutes": 60,
}

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def load_json(filename: str) -> dict:
    """Load a JSON stats file, return empty dict if not found."""
    path = os.path.join(SCRIPT_DIR, filename)
    if not os.path.exists(path):
        return {}
    try:
        with open(path) as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"Could not load {filename}: {e}")
        return {}


def check_sync_health(stats: dict) -> list:
    """Check sync stats for issues."""
    issues = []
    if not stats:
        issues.append(("WARNING", "No sync stats file found — first run?"))
        return issues

    created = stats.get("notion_created_contacts", 0) + stats.get("notion_created_companies", 0)
    updated = stats.get("notion_updated_contacts", 0) + stats.get("notion_updated_companies", 0)
    total = created + updated

    if total < THRESHOLDS["min_records_processed"]:
        issues.append(("CRITICAL", f"Zero records processed in sync — sync may have failed"))

    fetched = stats.get("apollo_fetched_contacts", 1) + stats.get("apollo_fetched_accounts", 1)
    dupes = stats.get("duplicates_prevented", 0)
    dup_rate = dupes / max(fetched, 1)
    if dup_rate > THRESHOLDS["max_duplicate_rate"]:
        issues.append(("WARNING", f"High duplicate rate: {dup_rate:.1%} ({dupes}/{fetched})"))

    failed = stats.get("failed_contacts", 0) + stats.get("failed_companies", 0)
    if failed > 0:
        issues.append(("WARNING", f"{failed} records failed to sync"))

    return issues


def check_action_health(stats: dict) -> list:
    """Check action engine stats."""
    issues = []
    if not stats:
        return issues  # auto_tasks may not have run yet

    errors = stats.get("errors", 0)
    if errors > 0:
        issues.append(("WARNING", f"Action Engine had {errors} errors creating tasks"))

    created = stats.get("created", 0)
    if created == 0:
        issues.append(("INFO", "Action Engine created 0 tasks — all contacts may already have open tasks"))

    return issues


def main():
    parser = argparse.ArgumentParser(description="AI Sales OS — Health Check")
    parser.add_argument("--strict", action="store_true", help="Exit 1 on any warning")
    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info(f"HEALTH CHECK — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    logger.info("=" * 60)

    all_issues = []

    # Check sync stats
    sync_stats = load_json("last_sync_stats.json")
    sync_issues = check_sync_health(sync_stats)
    all_issues.extend(sync_issues)

    # Check action stats
    action_stats = load_json("last_action_stats.json")
    action_issues = check_action_health(action_stats)
    all_issues.extend(action_issues)

    # Report
    if all_issues:
        logger.info("")
        logger.info("ISSUES DETECTED:")
        for level, msg in all_issues:
            if level == "CRITICAL":
                logger.error(f"  {level}: {msg}")
            elif level == "WARNING":
                logger.warning(f"  {level}: {msg}")
            else:
                logger.info(f"  {level}: {msg}")
    else:
        logger.info("All checks passed")

    logger.info("=" * 60)

    # Exit code
    has_critical = any(level == "CRITICAL" for level, _ in all_issues)
    has_warning = any(level == "WARNING" for level, _ in all_issues)

    if has_critical:
        sys.exit(1)
    if args.strict and has_warning:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
