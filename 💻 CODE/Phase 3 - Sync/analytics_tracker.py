#!/usr/bin/env python3
"""
AI Sales OS — Analytics Tracker

Pulls Apollo Analytics data and syncs engagement signals back to Notion.
Provides real performance data to close the feedback loop.

Features:
  - Fetch email performance by seniority, company size, time
  - Sync sequence engagement data back to contact records
  - Generate weekly analytics summaries
  - Feed data to score_calibrator.py

Usage:
    python analytics_tracker.py                    # full sync + report
    python analytics_tracker.py --dry-run          # preview without writing
    python analytics_tracker.py --days 7           # last N days
    python analytics_tracker.py --export           # save report to file
    python analytics_tracker.py --skip-sync        # report only, no Notion writes
"""
import os
import sys
import json
import logging
import time
import argparse
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.dirname(__file__))
from notion_helpers import (
    NOTION_DATABASE_ID_CONTACTS,
    update_page,
    rate_limiter,
    notion_request,
    NOTION_BASE_URL,
)
from constants import (
    FIELD_EMAIL_SENT, FIELD_EMAIL_OPENED, FIELD_REPLIED,
    FIELD_MEETING_BOOKED, FIELD_OUTREACH_STATUS,
    FIELD_LAST_CONTACTED, FIELD_CONTACT_RESPONDED,
    FIELD_APOLLO_CONTACT_ID,
)

# ─── Config ──────────────────────────────────────────────────────────────────

APOLLO_API_KEY = os.getenv("APOLLO_API_KEY")
APOLLO_BASE_URL = "https://api.apollo.io/api/v1"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# ─── Logging ─────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("analytics_tracker.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


# ─── Apollo Analytics API ────────────────────────────────────────────────────

def apollo_request(method: str, url: str, max_retries: int = 5, **kwargs):
    """Apollo API request with retry logic."""
    import requests
    kwargs.setdefault("timeout", 60)

    for attempt in range(max_retries):
        try:
            resp = requests.request(method, url, **kwargs)
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            if attempt < max_retries - 1:
                wait = min(2 ** attempt, 30)
                logger.warning(f"Connection error (attempt {attempt + 1}): {e}")
                time.sleep(wait)
                continue
            raise

        if resp.status_code == 429:
            wait = float(resp.headers.get("Retry-After", min(2 ** attempt, 30)))
            time.sleep(wait)
            continue

        if resp.status_code >= 500:
            time.sleep(min(2 ** attempt, 30))
            continue

        resp.raise_for_status()
        return resp

    raise Exception(f"Failed after {max_retries} retries")


def fetch_analytics_report(
    metrics: List[str],
    group_by: Optional[List[str]] = None,
    date_range: Optional[Dict] = None,
) -> Dict:
    """Fetch analytics from Apollo."""
    payload = {
        "api_key": APOLLO_API_KEY,
        "metrics": metrics,
    }
    if group_by:
        payload["group_by"] = group_by
    if date_range:
        payload["date_range"] = date_range
    else:
        payload["date_range"] = {"modality": "last_30_days"}

    try:
        resp = apollo_request(
            "POST",
            f"{APOLLO_BASE_URL}/analytics/sync_report",
            json=payload,
        )
        return resp.json()
    except Exception as e:
        logger.error(f"Analytics API error: {e}")
        return {}


def fetch_seniority_performance(days: int = 30) -> Dict:
    """Get email performance broken down by seniority."""
    if days <= 30:
        date_range = {"modality": "last_30_days"}
    elif days <= 90:
        date_range = {"modality": "last_3_months"}
    else:
        date_range = {"modality": "last_6_months"}

    return fetch_analytics_report(
        metrics=[
            "num_emails_sent", "num_emails_opened", "num_emails_replied",
            "percent_emails_replied", "num_contacts_replied",
        ],
        group_by=["person_seniority"],
        date_range=date_range,
    )


def fetch_company_size_performance(days: int = 30) -> Dict:
    """Get email performance broken down by company size."""
    if days <= 30:
        date_range = {"modality": "last_30_days"}
    elif days <= 90:
        date_range = {"modality": "last_3_months"}
    else:
        date_range = {"modality": "last_6_months"}

    return fetch_analytics_report(
        metrics=[
            "num_emails_sent", "num_emails_opened", "num_emails_replied",
            "percent_emails_replied",
        ],
        group_by=["organization_num_current_employees"],
        date_range=date_range,
    )


def fetch_weekly_trends() -> Dict:
    """Get weekly email performance trends."""
    return fetch_analytics_report(
        metrics=[
            "num_emails_sent", "num_emails_replied", "percent_emails_replied",
            "num_contacts_replied",
        ],
        group_by=["smart_datetime_week"],
        date_range={"modality": "last_3_months"},
    )


def fetch_sequence_performance() -> Dict:
    """Get performance by sequence."""
    return fetch_analytics_report(
        metrics=[
            "num_emails_sent", "num_emails_opened", "num_emails_replied",
            "percent_emails_replied",
        ],
        group_by=["emailer_campaign_id"],
        date_range={"modality": "last_30_days"},
    )


def fetch_overall_stats(days: int = 30) -> Dict:
    """Get overall team email stats."""
    if days <= 30:
        date_range = {"modality": "last_30_days"}
    else:
        date_range = {"modality": "last_3_months"}

    return fetch_analytics_report(
        metrics=[
            "num_emails_sent", "num_emails_delivered", "num_emails_opened",
            "num_emails_replied", "num_emails_bounced",
            "percent_emails_replied",
            "num_contacts_emailed", "num_contacts_replied",
        ],
        date_range=date_range,
    )


# ─── Sync Engagement to Notion ──────────────────────────────────────────────

def sync_engagement_to_notion(dry_run: bool = False) -> Dict:
    """
    Sync engagement data from Apollo contacts search back to Notion.
    Looks for contacts with recent engagement that Notion doesn't know about.
    """
    stats = {"checked": 0, "updated": 0, "errors": 0}

    # Fetch contacts from Notion that are "In Sequence" or "Sent"
    cursor = None
    contacts_to_check = []

    while True:
        body = {
            "page_size": 100,
            "filter": {
                "or": [
                    {"property": FIELD_OUTREACH_STATUS, "select": {"equals": "In Sequence"}},
                    {"property": FIELD_OUTREACH_STATUS, "select": {"equals": "Sent"}},
                    {"property": FIELD_OUTREACH_STATUS, "select": {"equals": "Opened"}},
                ]
            },
        }
        if cursor:
            body["start_cursor"] = cursor

        rate_limiter.wait()
        try:
            resp = notion_request("POST", f"{NOTION_BASE_URL}/databases/{NOTION_DATABASE_ID_CONTACTS}/query", json=body)
            data = resp.json()
        except Exception as e:
            logger.error(f"Error fetching contacts: {e}")
            break

        for page in data.get("results", []):
            props = page.get("properties", {})
            apollo_id_rt = props.get(FIELD_APOLLO_CONTACT_ID, {}).get("rich_text", [])
            apollo_id = apollo_id_rt[0]["plain_text"].strip() if apollo_id_rt else ""

            if not apollo_id:
                continue

            current_replied = props.get(FIELD_REPLIED, {}).get("checkbox", False)
            current_opened = props.get(FIELD_EMAIL_OPENED, {}).get("checkbox", False)
            current_sent = props.get(FIELD_EMAIL_SENT, {}).get("checkbox", False)
            outreach = props.get(FIELD_OUTREACH_STATUS, {}).get("select", {})
            outreach_name = outreach.get("name", "") if outreach else ""

            contacts_to_check.append({
                "page_id": page["id"],
                "apollo_id": apollo_id,
                "current_replied": current_replied,
                "current_opened": current_opened,
                "current_sent": current_sent,
                "outreach_status": outreach_name,
            })

        if not data.get("has_more"):
            break
        cursor = data.get("next_cursor")

    logger.info(f"Found {len(contacts_to_check)} contacts with outreach activity to check")
    stats["checked"] = len(contacts_to_check)

    # For each contact, check if engagement has changed
    # We use Apollo contact search to batch-check engagement
    # Process in batches of 25
    for i in range(0, len(contacts_to_check), 25):
        batch = contacts_to_check[i:i + 25]

        for contact in batch:
            try:
                # Query Apollo for this contact's engagement
                resp = apollo_request(
                    "POST",
                    f"{APOLLO_BASE_URL}/contacts/search",
                    json={
                        "api_key": APOLLO_API_KEY,
                        "id": [contact["apollo_id"]],
                        "per_page": 1,
                    },
                )
                data = resp.json()
                apollo_contacts = data.get("contacts", [])

                if not apollo_contacts:
                    continue

                ac = apollo_contacts[0]

                # Check for engagement updates
                updates = {}
                new_outreach = contact["outreach_status"]

                # Check replied
                if ac.get("contact_replied") and not contact["current_replied"]:
                    updates[FIELD_REPLIED] = {"checkbox": True}
                    updates[FIELD_CONTACT_RESPONDED] = {"checkbox": True}
                    new_outreach = "Replied"

                # Check opened
                if ac.get("contact_email_opened") and not contact["current_opened"]:
                    updates[FIELD_EMAIL_OPENED] = {"checkbox": True}
                    if new_outreach not in ("Replied", "Meeting Booked"):
                        new_outreach = "Opened"

                # Check sent
                if ac.get("contact_email_sent") and not contact["current_sent"]:
                    updates[FIELD_EMAIL_SENT] = {"checkbox": True}

                # Update outreach status if changed
                if new_outreach != contact["outreach_status"]:
                    updates[FIELD_OUTREACH_STATUS] = {"select": {"name": new_outreach}}

                if updates:
                    if dry_run:
                        logger.info(f"  [DRY RUN] Would update {contact['apollo_id']}: {list(updates.keys())}")
                    else:
                        update_page(contact["page_id"], updates)
                    stats["updated"] += 1

            except Exception as e:
                logger.warning(f"Error checking {contact['apollo_id']}: {e}")
                stats["errors"] += 1

            time.sleep(0.3)  # Rate limit

    return stats


# ─── Report Generation ──────────────────────────────────────────────────────

def build_full_analytics_report(days: int = 30) -> str:
    """Build a comprehensive analytics report."""
    report = []
    report.append(f"# AI Sales OS — Analytics Report")
    report.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    report.append(f"**Period:** Last {days} days")
    report.append("")

    # Overall stats
    logger.info("Fetching overall stats...")
    overall = fetch_overall_stats(days)
    if overall:
        report.append("## Overall Performance")
        rows = overall.get("rows", [])
        if rows:
            for row in rows:
                for key, val in row.items():
                    if key.startswith("num_") or key.startswith("percent_"):
                        label = key.replace("num_", "").replace("percent_", "% ").replace("_", " ").title()
                        report.append(f"- **{label}:** {val}")
        report.append("")

    # Seniority breakdown
    logger.info("Fetching seniority performance...")
    seniority = fetch_seniority_performance(days)
    if seniority:
        report.append("## Performance by Seniority")
        rows = seniority.get("rows", [])
        if rows:
            report.append("| Seniority | Sent | Opened | Replied | Reply % |")
            report.append("|-----------|------|--------|---------|---------|")
            for row in sorted(rows, key=lambda r: r.get("num_emails_replied", 0), reverse=True):
                name = row.get("person_seniority", "Unknown")
                sent = row.get("num_emails_sent", 0)
                opened = row.get("num_emails_opened", 0)
                replied = row.get("num_emails_replied", 0)
                pct = row.get("percent_emails_replied", 0)
                report.append(f"| {name} | {sent} | {opened} | {replied} | {pct:.1f}% |")
        report.append("")

    # Company size breakdown
    logger.info("Fetching company size performance...")
    size = fetch_company_size_performance(days)
    if size:
        report.append("## Performance by Company Size")
        rows = size.get("rows", [])
        if rows:
            report.append("| Company Size | Sent | Replied | Reply % |")
            report.append("|-------------|------|---------|---------|")
            for row in sorted(rows, key=lambda r: r.get("num_emails_replied", 0), reverse=True):
                name = row.get("organization_num_current_employees", "Unknown")
                sent = row.get("num_emails_sent", 0)
                replied = row.get("num_emails_replied", 0)
                pct = row.get("percent_emails_replied", 0)
                report.append(f"| {name} | {sent} | {replied} | {pct:.1f}% |")
        report.append("")

    # Weekly trends
    logger.info("Fetching weekly trends...")
    trends = fetch_weekly_trends()
    if trends:
        report.append("## Weekly Trends")
        rows = trends.get("rows", [])
        if rows:
            report.append("| Week | Sent | Replied | Reply % |")
            report.append("|------|------|---------|---------|")
            for row in sorted(rows, key=lambda r: r.get("smart_datetime_week", ""))[-8:]:
                week = row.get("smart_datetime_week", "?")
                sent = row.get("num_emails_sent", 0)
                replied = row.get("num_emails_replied", 0)
                pct = row.get("percent_emails_replied", 0)
                report.append(f"| {week} | {sent} | {replied} | {pct:.1f}% |")
        report.append("")

    return "\n".join(report)


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="AI Sales OS — Analytics Tracker")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing")
    parser.add_argument("--days", type=int, default=30, help="Analysis period in days")
    parser.add_argument("--export", action="store_true", help="Save report to file")
    parser.add_argument("--skip-sync", action="store_true", help="Report only, no Notion sync")
    args = parser.parse_args()

    logger.info("=" * 70)
    logger.info(f"ANALYTICS TRACKER | Days: {args.days} | Dry Run: {args.dry_run} | Skip Sync: {args.skip_sync}")
    logger.info("=" * 70)

    start_time = time.time()

    # Step 1: Sync engagement data to Notion
    if not args.skip_sync:
        logger.info("Step 1: Syncing engagement data to Notion...")
        sync_stats = sync_engagement_to_notion(dry_run=args.dry_run)
        logger.info(f"  Checked: {sync_stats['checked']} | Updated: {sync_stats['updated']} | Errors: {sync_stats['errors']}")
    else:
        logger.info("Step 1: Skipping Notion sync (--skip-sync)")

    # Step 2: Build analytics report
    logger.info("Step 2: Building analytics report...")
    report = build_full_analytics_report(days=args.days)

    if args.export:
        report_file = os.path.join(SCRIPT_DIR, f"analytics_report_{datetime.now().strftime('%Y%m%d')}.md")
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(report)
        logger.info(f"Report saved to {report_file}")

    # Always print report summary
    for line in report.split("\n"):
        if line.startswith("#") or line.startswith("|") or line.startswith("-"):
            logger.info(f"  {line}")

    elapsed = time.time() - start_time

    logger.info("=" * 70)
    logger.info(f"ANALYTICS TRACKER COMPLETE | Time: {elapsed:.1f}s")
    logger.info("=" * 70)

    # Save stats
    stats_file = os.path.join(SCRIPT_DIR, "last_analytics_stats.json")
    try:
        with open(stats_file, "w") as f:
            json.dump({
                "sync_checked": sync_stats["checked"] if not args.skip_sync else 0,
                "sync_updated": sync_stats["updated"] if not args.skip_sync else 0,
                "report_generated": True,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }, f, indent=2)
    except Exception:
        pass


if __name__ == "__main__":
    main()
