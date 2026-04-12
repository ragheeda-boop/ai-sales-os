#!/usr/bin/env python3
"""
Full Reset Notion — AI Sales OS
================================

Production-grade bulk archival of operational Notion databases, preparing a
clean slate for a fresh Apollo → Notion rebuild.

Mechanism
---------
Uses Notion API `PATCH /v1/pages/{id}` with `{"archived": true}` (moves page
to Trash). This is the cleanest reset path:
  - Removes records from all views and relations instantly
  - Restorable from Notion Trash for 30 days
  - No schema changes, no dependency on custom "Stage = Archived" logic
  - Works uniformly across Tasks, Meetings, Opportunities, Contacts, Companies

This is NOT the same as setting `Stage = "Archived"` (which is a soft
governance flag). For a full reset we want the records *gone* from the live
workspace — that's what Notion archival does.

Execution Order (prevents dangling relations / concurrent-script races)
-----------------------------------------------------------------------
    1. Tasks            — leaf records, safe to kill first
    2. Opportunities    — referenced by Tasks/Meetings
    3. Meetings         — referenced by Opportunities
    4. Contacts         — referenced by Tasks/Meetings/Opps
    5. Companies        — root, everyone points to it — last

Safety
------
Destructive. Requires THREE explicit flags to run:
    --execute --confirm-reset --i-understand-this-archives-everything

Without all three, runs in dry-run mode regardless of other args.

Usage
-----
    # 1) Always start with a dry-run audit
    python scripts/governance/full_reset_notion.py --dry-run

    # 2) Dry-run a specific DB only
    python scripts/governance/full_reset_notion.py --dry-run --only tasks

    # 3) Execute (core: tasks + contacts + companies)
    python scripts/governance/full_reset_notion.py \
        --execute --confirm-reset --i-understand-this-archives-everything

    # 4) Execute including Meetings + Opportunities
    python scripts/governance/full_reset_notion.py \
        --include-meetings --include-opportunities \
        --execute --confirm-reset --i-understand-this-archives-everything

    # 5) Limit for a test run
    python scripts/governance/full_reset_notion.py \
        --only tasks --limit 10 \
        --execute --confirm-reset --i-understand-this-archives-everything

Env Vars (all mandatory — no hardcoded fallbacks)
-------------------------------------------------
    NOTION_API_KEY
    NOTION_DATABASE_ID_CONTACTS
    NOTION_DATABASE_ID_COMPANIES
    NOTION_DATABASE_ID_TASKS
    NOTION_DATABASE_ID_MEETINGS         (only if --include-meetings)
    NOTION_DATABASE_ID_OPPORTUNITIES    (only if --include-opportunities)
"""
from __future__ import annotations

import os
import sys
import json
import time
import logging
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

# ─── Path bootstrap so `core.*` imports resolve ─────────────────────────────
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_SCRIPTS_DIR = os.path.dirname(_THIS_DIR)
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from dotenv import load_dotenv
load_dotenv()

from core.notion_helpers import (  # noqa: E402
    notion_request,
    rate_limiter,
    NOTION_BASE_URL,
)

# ─── Logging ────────────────────────────────────────────────────────────────
LOG_PATH = os.path.join(_THIS_DIR, "full_reset_notion.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_PATH, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("full_reset_notion")


# ─── DB Registry ────────────────────────────────────────────────────────────
# Execution order is the order of this list. DO NOT reorder without thinking
# about relation direction (leaves first, roots last).
DB_REGISTRY_ORDER = [
    "tasks",
    "opportunities",
    "meetings",
    "contacts",
    "companies",
]

DB_ENV_MAP = {
    "tasks":         "NOTION_DATABASE_ID_TASKS",
    "opportunities": "NOTION_DATABASE_ID_OPPORTUNITIES",
    "meetings":      "NOTION_DATABASE_ID_MEETINGS",
    "contacts":      "NOTION_DATABASE_ID_CONTACTS",
    "companies":     "NOTION_DATABASE_ID_COMPANIES",
}

# DBs that require an explicit opt-in flag to be touched
OPTIONAL_DBS = {"meetings", "opportunities"}


# ─── Fetch (paginated) ──────────────────────────────────────────────────────
def fetch_all_page_ids(db_id: str, db_label: str, limit: Optional[int] = None) -> List[str]:
    """
    Paginated scan of every live (non-archived) page in a database.
    Returns a list of page IDs only (we don't need properties for archival).
    """
    page_ids: List[str] = []
    has_more = True
    start_cursor: Optional[str] = None
    pages_scanned = 0

    logger.info(f"[{db_label}] Fetching all live page IDs ...")

    while has_more:
        body: Dict = {"page_size": 100}
        if start_cursor:
            body["start_cursor"] = start_cursor

        resp = notion_request(
            "POST",
            f"{NOTION_BASE_URL}/databases/{db_id}/query",
            json=body,
        )
        data = resp.json()
        results = data.get("results", [])
        for p in results:
            # Notion returns archived pages only if filtered; the default
            # query excludes archived. Belt-and-suspenders:
            if p.get("archived"):
                continue
            page_ids.append(p["id"])
            if limit and len(page_ids) >= limit:
                logger.info(f"[{db_label}] --limit {limit} reached, stopping fetch.")
                return page_ids

        pages_scanned += len(results)
        has_more = data.get("has_more", False)
        start_cursor = data.get("next_cursor")

        if pages_scanned % 500 == 0 and pages_scanned:
            logger.info(f"[{db_label}] scanned {pages_scanned} pages so far ...")

    logger.info(f"[{db_label}] Fetch complete — {len(page_ids)} live records.")
    return page_ids


# ─── Archive one page (PATCH archived:true) ────────────────────────────────
def archive_page(page_id: str) -> Tuple[bool, Optional[str]]:
    """
    Archive a single Notion page. Returns (ok, error_message_or_none).
    notion_helpers.notion_request already handles 429, 5xx, timeouts, backoff.
    """
    try:
        notion_request(
            "PATCH",
            f"{NOTION_BASE_URL}/pages/{page_id}",
            json={"archived": True},
        )
        return True, None
    except Exception as e:  # noqa: BLE001
        return False, f"{type(e).__name__}: {e}"


# ─── Process one DB ─────────────────────────────────────────────────────────
def process_database(
    db_label: str,
    db_id: str,
    dry_run: bool,
    limit: Optional[int],
    workers: int,
) -> Dict:
    """
    Audit + (optionally) archive every live page in one database.
    Returns a stats dict.
    """
    t0 = time.time()
    stats = {
        "db": db_label,
        "total_live": 0,
        "archived": 0,
        "failed": 0,
        "skipped_dry_run": 0,
        "errors_sample": [],
        "elapsed_sec": 0.0,
    }

    page_ids = fetch_all_page_ids(db_id, db_label, limit=limit)
    stats["total_live"] = len(page_ids)

    if not page_ids:
        logger.info(f"[{db_label}] Nothing to do — database is already empty.")
        stats["elapsed_sec"] = round(time.time() - t0, 2)
        return stats

    if dry_run:
        logger.info(
            f"[{db_label}] DRY-RUN — would archive {len(page_ids)} pages. "
            f"No changes made."
        )
        stats["skipped_dry_run"] = len(page_ids)
        stats["elapsed_sec"] = round(time.time() - t0, 2)
        return stats

    # Execute — parallel archive with bounded workers
    logger.info(
        f"[{db_label}] EXECUTING archival of {len(page_ids)} pages "
        f"with {workers} workers ..."
    )

    completed = 0
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futures = {ex.submit(archive_page, pid): pid for pid in page_ids}
        for fut in as_completed(futures):
            pid = futures[fut]
            ok, err = fut.result()
            if ok:
                stats["archived"] += 1
            else:
                stats["failed"] += 1
                if len(stats["errors_sample"]) < 10:
                    stats["errors_sample"].append({"page_id": pid, "error": err})
            completed += 1
            if completed % 250 == 0:
                logger.info(
                    f"[{db_label}] progress: {completed}/{len(page_ids)} "
                    f"(archived={stats['archived']}, failed={stats['failed']})"
                )

    stats["elapsed_sec"] = round(time.time() - t0, 2)
    logger.info(
        f"[{db_label}] DONE — archived={stats['archived']}, "
        f"failed={stats['failed']}, elapsed={stats['elapsed_sec']}s"
    )
    return stats


# ─── Plan builder ───────────────────────────────────────────────────────────
def build_plan(args) -> List[Tuple[str, str]]:
    """
    Decide which DBs to process in which order, based on args.
    Returns ordered list of (label, db_id).
    """
    plan: List[Tuple[str, str]] = []

    if args.only:
        labels = [args.only]
    else:
        labels = list(DB_REGISTRY_ORDER)
        if not args.include_meetings:
            labels = [x for x in labels if x != "meetings"]
        if not args.include_opportunities:
            labels = [x for x in labels if x != "opportunities"]

    for label in labels:
        env_var = DB_ENV_MAP[label]
        db_id = os.getenv(env_var)
        if not db_id:
            if args.only == label:
                raise EnvironmentError(
                    f"Missing env var {env_var} required for --only {label}"
                )
            logger.warning(f"[{label}] SKIP — {env_var} not set in env.")
            continue
        plan.append((label, db_id))

    return plan


# ─── CLI ────────────────────────────────────────────────────────────────────
def parse_args():
    p = argparse.ArgumentParser(
        description="Full reset of AI Sales OS operational Notion databases.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    mode = p.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", default=True,
                      help="Audit only — no writes (default).")
    mode.add_argument("--execute", action="store_true",
                      help="Actually archive. REQUIRES --confirm-reset "
                           "AND --i-understand-this-archives-everything.")

    p.add_argument("--confirm-reset", action="store_true",
                   help="Safety flag #1 — required with --execute.")
    p.add_argument("--i-understand-this-archives-everything",
                   dest="i_understand",
                   action="store_true",
                   help="Safety flag #2 — required with --execute.")

    p.add_argument("--include-meetings", action="store_true",
                   help="Include Meetings DB in the reset.")
    p.add_argument("--include-opportunities", action="store_true",
                   help="Include Opportunities DB in the reset.")

    p.add_argument("--only", choices=DB_REGISTRY_ORDER,
                   help="Process exactly ONE database (overrides include-* flags).")

    p.add_argument("--limit", type=int, default=None,
                   help="Cap per-DB record count (useful for test runs).")

    p.add_argument("--workers", type=int, default=4,
                   help="Parallel archive workers per DB (default 4). "
                        "Keep ≤5 to respect Notion ~3 req/s rate limit.")

    return p.parse_args()


def main():
    args = parse_args()

    # Resolve final mode
    really_execute = (
        args.execute
        and args.confirm_reset
        and args.i_understand
    )

    if args.execute and not really_execute:
        logger.error(
            "--execute requires BOTH --confirm-reset AND "
            "--i-understand-this-archives-everything. Aborting."
        )
        sys.exit(2)

    mode_label = "EXECUTE (DESTRUCTIVE)" if really_execute else "DRY-RUN"
    logger.info("=" * 72)
    logger.info(f"Full Reset Notion — mode: {mode_label}")
    logger.info(f"Started at: {datetime.now(timezone.utc).isoformat()}")
    logger.info("=" * 72)

    # Env sanity
    if not os.getenv("NOTION_API_KEY"):
        logger.error("NOTION_API_KEY is not set. Aborting.")
        sys.exit(2)

    # Plan
    try:
        plan = build_plan(args)
    except EnvironmentError as e:
        logger.error(str(e))
        sys.exit(2)

    if not plan:
        logger.error("No databases in plan. Nothing to do.")
        sys.exit(1)

    logger.info("Planned execution order:")
    for i, (label, db_id) in enumerate(plan, 1):
        logger.info(f"  {i}. {label:<14} ({db_id})")

    if really_execute:
        logger.warning("")
        logger.warning("⚠️  DESTRUCTIVE MODE — pages will be sent to Notion Trash.")
        logger.warning("    Trash retains deleted pages for 30 days — restorable.")
        logger.warning("    Starting in 5 seconds ... (Ctrl-C to abort)")
        logger.warning("")
        try:
            time.sleep(5)
        except KeyboardInterrupt:
            logger.error("Aborted by user during countdown.")
            sys.exit(130)

    # Run
    all_stats = []
    for label, db_id in plan:
        stats = process_database(
            db_label=label,
            db_id=db_id,
            dry_run=(not really_execute),
            limit=args.limit,
            workers=args.workers,
        )
        all_stats.append(stats)

    # ─── Final summary ──
    logger.info("")
    logger.info("=" * 72)
    logger.info("FINAL SUMMARY")
    logger.info("=" * 72)
    total_live = total_arch = total_fail = total_dry = 0
    for s in all_stats:
        total_live += s["total_live"]
        total_arch += s["archived"]
        total_fail += s["failed"]
        total_dry  += s["skipped_dry_run"]
        logger.info(
            f"  {s['db']:<14} live={s['total_live']:<6} "
            f"archived={s['archived']:<6} failed={s['failed']:<4} "
            f"dry_run={s['skipped_dry_run']:<6} "
            f"elapsed={s['elapsed_sec']}s"
        )
    logger.info("-" * 72)
    logger.info(
        f"  {'TOTAL':<14} live={total_live:<6} "
        f"archived={total_arch:<6} failed={total_fail:<4} "
        f"dry_run={total_dry:<6}"
    )
    logger.info("=" * 72)

    # Persist stats JSON
    stats_file = os.path.join(_THIS_DIR, "last_full_reset_stats.json")
    with open(stats_file, "w", encoding="utf-8") as f:
        json.dump(
            {
                "mode": mode_label,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "databases": all_stats,
                "totals": {
                    "live": total_live,
                    "archived": total_arch,
                    "failed": total_fail,
                    "dry_run": total_dry,
                },
            },
            f,
            indent=2,
        )
    logger.info(f"Stats written to {stats_file}")

    if total_fail > 0:
        logger.warning(f"Completed with {total_fail} failures — review log.")
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
