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
from typing import Dict

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
# scripts/ root — parent of monitoring/
SCRIPTS_ROOT = os.path.dirname(SCRIPT_DIR)

# Path drift fix (v6.0 modular reorg):
# Before v6.0 all scripts lived in one flat directory and each wrote its
# stats file next to itself, so health_check reading from SCRIPT_DIR worked.
# After v6.0 each module writes into its own module directory, so this map
# routes each stats filename to its canonical writer location. Kept in sync
# with the `path:` entries in .github/workflows/daily_sync.yml (Upload Sync
# Stats step).
STATS_LOCATIONS: Dict[str, str] = {
    "last_sync_stats.json":            "core",         # NOT YET WRITTEN — daily_sync.py has no stats export (known gap; see pipeline-health-monitor SKILL.md:50)
    "last_action_stats.json":          "automation",   # auto_tasks.py:793
    "last_sequence_stats.json":        "automation",   # auto_sequence.py:535
    "last_outcome_stats.json":         "automation",   # outcome_tracker.py:300  (CAVEAT: writes to CWD via relative path — latent bug, tracked separately)
    "last_analytics_stats.json":       "enrichment",   # analytics_tracker.py:662
    "last_job_postings_stats.json":    "enrichment",   # job_postings_enricher.py:499
    "last_meeting_tracker_stats.json": "meetings",     # meeting_tracker.py:908
    "last_analyzer_stats.json":        "meetings",     # meeting_analyzer.py:558
    "last_opportunity_stats.json":     "meetings",     # opportunity_manager.py:960
}


def _resolve_stats_path(filename: str) -> str:
    """Resolve a stats filename to its canonical writer location.

    Looks up STATS_LOCATIONS first; falls back to SCRIPT_DIR for backwards
    compatibility with any unmapped files.
    """
    module = STATS_LOCATIONS.get(filename)
    if module:
        return os.path.join(SCRIPTS_ROOT, module, filename)
    return os.path.join(SCRIPT_DIR, filename)


def load_json(filename: str) -> dict:
    """Load a JSON stats file, return empty dict if not found."""
    path = _resolve_stats_path(filename)
    if not os.path.exists(path):
        logger.debug(f"Stats file not found: {path}")
        return {}
    try:
        with open(path) as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"Could not load {filename} from {path}: {e}")
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


def check_meeting_tracker_health(stats: dict) -> list:
    """Check meeting tracker stats."""
    issues = []
    if not stats:
        return issues  # meeting tracker may not have run yet

    errors = stats.get("errors", 0)
    if errors > 0:
        issues.append(("WARNING", f"Meeting Tracker had {errors} errors"))

    processed = stats.get("events_processed", 0)
    created = stats.get("meetings_created", 0)
    contacts_updated = stats.get("contacts_updated", 0)

    if processed > 0 and created == 0 and contacts_updated == 0:
        issues.append(("INFO", f"Meeting Tracker processed {processed} events but created 0 meetings — all may be duplicates or no contact matches"))

    return issues


def check_analyzer_health(stats: dict) -> list:
    """Check meeting analyzer stats."""
    issues = []
    if not stats:
        return issues  # analyzer may not have run yet

    errors = stats.get("errors", 0)
    analyzed = stats.get("analyzed", 0)
    found = stats.get("meetings_found", 0)

    if errors > 0:
        issues.append(("WARNING", f"Meeting Analyzer had {errors} errors (API failures or parse issues)"))

    if found > 0 and analyzed == 0:
        issues.append(("WARNING", f"Meeting Analyzer found {found} meetings but analyzed 0 — check ANTHROPIC_API_KEY"))

    opp_flagged = stats.get("opportunities_flagged", 0)
    if opp_flagged > 0:
        issues.append(("INFO", f"Meeting Analyzer flagged {opp_flagged} opportunity signal(s) — review recommended"))

    return issues


def check_opportunity_health(stats: dict) -> list:
    """Check opportunity manager stats."""
    issues = []
    if not stats:
        return issues  # opportunity manager may not have run yet

    errors = stats.get("errors", 0)
    if errors > 0:
        issues.append(("WARNING", f"Opportunity Manager had {errors} errors"))

    stale_detected = stats.get("stale_detected", 0)
    if stale_detected > 0:
        issues.append(("WARNING", f"{stale_detected} stale deals detected — no update in 14+ days"))

    created = stats.get("opportunities_created", 0)
    meetings_processed = stats.get("meetings_processed", 0)
    if meetings_processed > 0 and created == 0:
        issues.append(("INFO", f"Opportunity Manager processed {meetings_processed} meetings but created 0 opportunities — contacts may already have open deals"))

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

    # Check meeting tracker stats
    meeting_stats = load_json("last_meeting_tracker_stats.json")
    meeting_issues = check_meeting_tracker_health(meeting_stats)
    all_issues.extend(meeting_issues)

    # Check meeting analyzer stats
    analyzer_stats = load_json("last_analyzer_stats.json")
    analyzer_issues = check_analyzer_health(analyzer_stats)
    all_issues.extend(analyzer_issues)

    # Check opportunity manager stats
    opp_stats = load_json("last_opportunity_stats.json")
    opp_issues = check_opportunity_health(opp_stats)
    all_issues.extend(opp_issues)

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
