#!/usr/bin/env python3
"""
followup_rules_engine.py
=========================
Phase 5: Rules engine — evaluate engagement signals and advance Follow-up Stage

STATE MACHINE:
  Not Started
    → [email_sent=True]          → Email Sent — Waiting
  Email Sent — Waiting
    → [opened=True, no reply]    → Opened — No Reply
    → [replied=True]             → Replied — Qualifying
    → [stale > 14d]              → Stale — Re-engage
  Opened — No Reply
    → [replied=True]             → Replied — Qualifying
    → [3+ days no reply]         → email_sent=True  (trigger follow-up task)
    → [stale > 14d]              → Stale — Re-engage
  Replied — Qualifying
    → [meeting_booked=True]      → Meeting Scheduled
    → [stale > 14d]              → Stale — Re-engage
  Meeting Scheduled
    → [meeting_done=True]        → Meeting Done — Follow-up
  Meeting Done — Follow-up
    → (manual advance)
  Stale — Re-engage
    → [email_sent again]         → Email Sent — Waiting
    → [manual_note="disqualified"] → Disqualified
  Disqualified
    → (terminal)

RULES ALSO COMPUTE:
  - Priority: High (replied/meeting), Medium (opened), Low (sent), None (not started)
  - Next Action: based on current stage + last activity
  - Next Action Due Date: based on stage SLA
  - Stale Flag: checkbox
  - Days Since Contact: number

Run:
    python followup_rules_engine.py
    python followup_rules_engine.py --dry-run
    python followup_rules_engine.py --limit 100
    python followup_rules_engine.py --reset-stale    # recalculate stale flags only
"""

import os, sys, time, json, argparse, logging
from pathlib import Path
from datetime import datetime, date, timezone, timedelta
from collections import defaultdict

import requests
from dotenv import load_dotenv

from constants_eng import (
    NOTION_DB_ID,
    F_NAME, F_EMAIL, F_MOBILE,
    F_EMAIL_SENT, F_EMAIL_OPENED, F_EMAIL_REPLIED, F_EMAIL_BOUNCED,
    F_LAST_SENT_AT, F_LAST_OPENED_AT, F_LAST_REPLIED_AT,
    F_LAST_ACT_DATE, F_LAST_ACT_TYPE, F_ACT_COUNT,
    F_POS_SIGNAL, F_MTG_BOOKED, F_MTG_DONE,
    F_STATUS, F_FOLLOWUP_STAGE, F_PRIORITY,
    F_STALE_FLAG, F_DAYS_SINCE, F_NEXT_ACTION, F_NEXT_DUE,
    F_MANUAL_NOTE, F_MISS_EMAIL, F_READY,
    STALE_DAYS, OPENED_FOLLOWUP_DAYS,
)

# ───────────────────────────────────────────────
# Logging
# ───────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("followup_rules_engine.log", encoding="utf-8"),
    ],
)
log = logging.getLogger(__name__)

# ───────────────────────────────────────────────
# Load env
# ───────────────────────────────────────────────

load_dotenv(Path(__file__).parent / ".env")
NOTION_TOKEN = os.getenv("NOTION_API_KEY") or os.getenv("NOTION_TOKEN")
if not NOTION_TOKEN:
    sys.exit("❌  NOTION_API_KEY not set in .env")

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json",
}

# ───────────────────────────────────────────────
# Stage definitions
# ───────────────────────────────────────────────

STAGE_NOT_STARTED       = "Not Started"
STAGE_SENT              = "Email Sent — Waiting"
STAGE_OPENED            = "Opened — No Reply"
STAGE_REPLIED           = "Replied — Qualifying"
STAGE_MTG_SCHEDULED     = "Meeting Scheduled"
STAGE_MTG_DONE          = "Meeting Done — Follow-up"
STAGE_STALE             = "Stale — Re-engage"
STAGE_DISQUALIFIED      = "Disqualified"

# Stages that are "terminal" — don't advance automatically
TERMINAL_STAGES = {STAGE_DISQUALIFIED, STAGE_MTG_DONE}

# Map stage to priority
STAGE_PRIORITY = {
    STAGE_MTG_SCHEDULED:  "High",
    STAGE_MTG_DONE:       "High",
    STAGE_REPLIED:        "High",
    STAGE_OPENED:         "Medium",
    STAGE_SENT:           "Low",
    STAGE_STALE:          "Low",
    STAGE_NOT_STARTED:    "Low",
    STAGE_DISQUALIFIED:   "Low",
}

# Map stage to next action text
STAGE_NEXT_ACTION = {
    STAGE_NOT_STARTED:    "Send initial outreach email",
    STAGE_SENT:           "Wait for response — check again in 3 days",
    STAGE_OPENED:         "Send follow-up email — opened but no reply",
    STAGE_REPLIED:        "Qualify and schedule meeting",
    STAGE_MTG_SCHEDULED:  "Confirm meeting and prepare agenda",
    STAGE_MTG_DONE:       "Send follow-up summary and next steps",
    STAGE_STALE:          "Re-engage with new angle or offer",
    STAGE_DISQUALIFIED:   "No action — disqualified",
}

# SLA: days until next action is due
STAGE_SLA_DAYS = {
    STAGE_NOT_STARTED:  7,
    STAGE_SENT:         3,
    STAGE_OPENED:       1,
    STAGE_REPLIED:      2,
    STAGE_MTG_SCHEDULED: 1,
    STAGE_MTG_DONE:     3,
    STAGE_STALE:        14,
    STAGE_DISQUALIFIED: 0,
}

# Disqualifying manual note keywords
DISQUALIFY_KEYWORDS = {"عبيط", "disqualified", "not interested", "غير مهتم", "لا يرد", "محظور"}

# ───────────────────────────────────────────────
# HTTP helpers
# ───────────────────────────────────────────────

def _notion_req(method: str, url: str, **kwargs) -> dict:
    for attempt in range(6):
        resp = requests.request(method, url, headers=HEADERS, **kwargs)
        if resp.status_code == 429:
            time.sleep(2 ** attempt); continue
        if resp.status_code >= 500:
            time.sleep(2 ** attempt); continue
        resp.raise_for_status()
        return resp.json()
    raise RuntimeError(f"Notion request failed: {url}")


def notion_query_all(db_id: str, filter_payload: dict = None) -> list[dict]:
    pages, cursor = [], None
    while True:
        body = {"page_size": 100}
        if cursor:
            body["start_cursor"] = cursor
        if filter_payload:
            body["filter"] = filter_payload
        data = _notion_req("POST", f"https://api.notion.com/v1/databases/{db_id}/query", json=body)
        pages.extend(data.get("results", []))
        if not data.get("has_more"):
            break
        cursor = data["next_cursor"]
    return pages


def update_page(page_id: str, props: dict) -> dict:
    return _notion_req("PATCH", f"https://api.notion.com/v1/pages/{page_id}", json={"properties": props})


# ───────────────────────────────────────────────
# Property extractors
# ───────────────────────────────────────────────

def _get_title(props, field):
    b = props.get(field, {}).get("title", [])
    return b[0]["plain_text"].strip() if b else ""

def _get_text(props, field):
    b = props.get(field, {}).get("rich_text", [])
    return b[0]["plain_text"].strip() if b else ""

def _get_select(props, field):
    s = props.get(field, {}).get("select")
    return s["name"] if s else ""

def _get_checkbox(props, field):
    return bool(props.get(field, {}).get("checkbox", False))

def _get_date(props, field):
    d = props.get(field, {}).get("date")
    return d["start"] if d else ""

def _get_number(props, field):
    return props.get(field, {}).get("number") or 0


# ───────────────────────────────────────────────
# Property builders
# ───────────────────────────────────────────────

def _text(val):
    return {"rich_text": [{"text": {"content": str(val)[:2000] if val else ""}}]}

def _select(val):
    return {"select": {"name": val}} if val else {"select": None}

def _checkbox(val):
    return {"checkbox": bool(val)}

def _number(val):
    return {"number": int(val) if val is not None else None}

def _date(val):
    if not val:
        return {"date": None}
    return {"date": {"start": val if isinstance(val, str) else val.isoformat()}}


# ───────────────────────────────────────────────
# Rules engine
# ───────────────────────────────────────────────

def days_since(date_str: str) -> int:
    """Return number of days since a date string (YYYY-MM-DD or ISO)."""
    if not date_str:
        return 9999
    try:
        d = date.fromisoformat(date_str[:10])
        return (date.today() - d).days
    except ValueError:
        return 9999


def evaluate_stage(page: dict) -> dict:
    """
    Apply state machine rules to a Notion page.
    Returns a dict of Notion property updates (only changed fields).
    """
    props = page.get("properties", {})

    # Read current state
    name          = _get_title(props, F_NAME)
    current_stage = _get_select(props, F_FOLLOWUP_STAGE)
    current_prio  = _get_select(props, F_PRIORITY)

    email_sent    = _get_checkbox(props, F_EMAIL_SENT)
    email_opened  = _get_checkbox(props, F_EMAIL_OPENED)
    email_replied = _get_checkbox(props, F_EMAIL_REPLIED)
    email_bounced = _get_checkbox(props, F_EMAIL_BOUNCED)
    mtg_booked    = _get_checkbox(props, F_MTG_BOOKED)
    mtg_done      = _get_checkbox(props, F_MTG_DONE)
    pos_signal    = _get_checkbox(props, F_POS_SIGNAL)
    miss_email    = _get_checkbox(props, F_MISS_EMAIL)

    last_act_date   = _get_date(props, F_LAST_ACT_DATE)
    last_sent_at    = _get_date(props, F_LAST_SENT_AT)
    last_opened_at  = _get_date(props, F_LAST_OPENED_AT)
    last_replied_at = _get_date(props, F_LAST_REPLIED_AT)

    manual_note   = _get_text(props, F_MANUAL_NOTE).lower()
    company_status = _get_select(props, F_STATUS)

    # Compute days since last contact
    last_contact = last_replied_at or last_opened_at or last_sent_at or last_act_date
    days_since_contact = days_since(last_contact)

    # Check for disqualifying note
    is_disqualified = any(kw in manual_note for kw in DISQUALIFY_KEYWORDS)

    # Don't touch terminal stages unless disqualified
    if current_stage in TERMINAL_STAGES and not is_disqualified:
        return {}

    # Don't touch records with no email (can't advance via email)
    if miss_email and not email_sent:
        return {}

    # ── Apply state machine ──────────────────────

    new_stage = current_stage or STAGE_NOT_STARTED

    # Disqualification overrides everything
    if is_disqualified:
        new_stage = STAGE_DISQUALIFIED

    # Terminal: meeting done
    elif mtg_done:
        new_stage = STAGE_MTG_DONE

    # Meeting scheduled
    elif mtg_booked:
        new_stage = STAGE_MTG_SCHEDULED

    # Has reply → Qualifying
    elif email_replied:
        new_stage = STAGE_REPLIED

    # Opened but no reply
    elif email_opened and not email_replied:
        new_stage = STAGE_OPENED

    # Email sent, no open yet
    elif email_sent and not email_opened:
        # Check for stale
        if last_sent_at and days_since(last_sent_at) > STALE_DAYS:
            new_stage = STAGE_STALE
        else:
            new_stage = STAGE_SENT

    # Nothing sent
    else:
        new_stage = STAGE_NOT_STARTED

    # Stale detection: override mid-funnel stages
    if new_stage in (STAGE_SENT, STAGE_OPENED, STAGE_REPLIED):
        if days_since_contact > STALE_DAYS and days_since_contact < 9999:
            new_stage = STAGE_STALE

    # Compute stale flag
    is_stale = new_stage == STAGE_STALE

    # Compute priority
    new_priority = STAGE_PRIORITY.get(new_stage, "Low")
    # Override: if manually noted as "مهتم" / "interested" → bump to High
    if any(kw in manual_note for kw in ("مهتم", "interested", "يريد")):
        new_priority = "High"

    # Compute next action
    next_action = STAGE_NEXT_ACTION.get(new_stage, "")

    # Compute next action due date
    sla_days = STAGE_SLA_DAYS.get(new_stage, 3)
    if sla_days > 0:
        next_due = (date.today() + timedelta(days=sla_days)).isoformat()
    else:
        next_due = ""

    # Sync Company Status with Follow-up Stage
    # (only advance forward — never overwrite Meeting/Customer)
    PROTECTED_STATUSES = {"Meeting Scheduled", "Meeting Done", "Customer", "Disqualified"}
    new_status = company_status
    STATUS_FROM_STAGE = {
        STAGE_NOT_STARTED:   "Prospect",
        STAGE_SENT:          "Outreach Sent",
        STAGE_OPENED:        "Opened",
        STAGE_REPLIED:       "Replied",
        STAGE_MTG_SCHEDULED: "Meeting Scheduled",
        STAGE_MTG_DONE:      "Meeting Done",
        STAGE_STALE:         "Stale",
        STAGE_DISQUALIFIED:  "Disqualified",
    }
    if company_status not in PROTECTED_STATUSES:
        new_status = STATUS_FROM_STAGE.get(new_stage, company_status)

    # ── Build update dict ──────────────────────
    updates = {}

    if new_stage != current_stage:
        updates[F_FOLLOWUP_STAGE] = _select(new_stage)
        log.info(f"   → Stage: {current_stage or '(empty)'} → {new_stage}")

    if new_priority != current_prio:
        updates[F_PRIORITY] = _select(new_priority)

    updates[F_STALE_FLAG] = _checkbox(is_stale)
    updates[F_DAYS_SINCE] = _number(days_since_contact if days_since_contact < 9999 else None)
    updates[F_NEXT_ACTION] = _text(next_action)

    if next_due:
        updates[F_NEXT_DUE] = _date(next_due)

    if new_status and new_status != company_status:
        updates[F_STATUS] = _select(new_status)

    return updates


# ───────────────────────────────────────────────
# Main
# ───────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--reset-stale", action="store_true", help="Recalculate stale flags only")
    args = parser.parse_args()

    log.info("📂  Loading all Notion records...")
    pages = notion_query_all(NOTION_DB_ID)
    log.info(f"   → {len(pages)} pages")

    if args.limit:
        pages = pages[:args.limit]

    stats = defaultdict(int)
    stage_changes = defaultdict(int)

    for i, page in enumerate(pages, 1):
        pid = page["id"]
        props = page.get("properties", {})
        name = props.get(F_NAME, {}).get("title", [{}])[0].get("plain_text", f"[Row {i}]")

        log.info(f"[{i}/{len(pages)}] {name}")

        try:
            if args.reset_stale:
                # Only compute stale flag + days since
                last_act = _get_date(props, F_LAST_ACT_DATE)
                last_sent = _get_date(props, F_LAST_SENT_AT)
                last_contact = last_act or last_sent
                d = days_since(last_contact)
                is_stale = d > STALE_DAYS and d < 9999
                updates = {
                    F_STALE_FLAG: _checkbox(is_stale),
                    F_DAYS_SINCE: _number(d if d < 9999 else None),
                }
                if not args.dry_run:
                    update_page(pid, updates)
                stats["updated"] += 1
                continue

            updates = evaluate_stage(page)

            if updates:
                if not args.dry_run:
                    update_page(pid, updates)
                stats["updated"] += 1

                if F_FOLLOWUP_STAGE in updates:
                    new_stage = updates[F_FOLLOWUP_STAGE]["select"]["name"] if updates[F_FOLLOWUP_STAGE]["select"] else "None"
                    stage_changes[new_stage] += 1
            else:
                stats["unchanged"] += 1
                log.info(f"   → No change")

        except Exception as e:
            log.error(f"   → ERROR: {e}")
            stats["errors"] += 1

    # ── Summary ──────────────────────────────────
    print("\n" + "═"*60)
    print("   FOLLOW-UP RULES ENGINE — COMPLETE")
    print("═"*60)
    print(f"  Total:       {len(pages)}")
    print(f"  Updated:     {stats['updated']}")
    print(f"  Unchanged:   {stats['unchanged']}")
    print(f"  Errors:      {stats['errors']}")
    if stage_changes:
        print()
        print("  Stage assignments:")
        for stage, cnt in sorted(stage_changes.items(), key=lambda x: -x[1]):
            print(f"    {stage:<35} {cnt}")
    if args.dry_run:
        print("\n  ⚠️  DRY RUN — no changes written")
    print("═"*60 + "\n")


if __name__ == "__main__":
    main()
