#!/usr/bin/env python3
"""
ai_sales_actions_enricher.py — Apply Apollo "AI Sales Actions" to Notion.

Reads Companies whose rich_text field `AI Sales Actions` is populated,
parses the structured block via `core.ai_sales_actions_parser`, and writes:

  Company DB (primary target):
    - AI Priority            (select)    P1/P2/P3
    - AI Fit                 (select)    High/Medium/Low
    - AI Urgency             (select)    High/Medium/Low
    - AI Segment             (rich_text)
    - AI Signal              (rich_text)
    - AI Pain Summary        (rich_text)
    - AI Target Role         (rich_text)
    - AI Action Type         (select)    Call/Email/Sequence/None
    - AI Tone                (rich_text)
    - AI Sales Actions Parsed At (date)

  Contacts DB (propagated to each linked contact at the company):
    - AI Call Hook           (rich_text, bullets joined)
    - AI Email Subject       (rich_text)
    - AI Email Opening       (rich_text)
    - AI Email Pain          (rich_text)
    - AI Email Value         (rich_text)
    - AI Email CTA           (rich_text)

Design rules
────────────
• Idempotent — skips companies whose `AI Sales Actions Parsed At` is newer
  than the source's `last_edited_time` (unless --force).
• Additive — only writes parsed sub-fields; never touches Name, Industry,
  Stage, or any owner/manual field.
• Safe — select fields are only written with canonical values; unknown
  values fall back to rich_text-only (the select field is left untouched).
• Dry-run by default — use --execute to apply writes.

CLI
───
    python enrichment/ai_sales_actions_enricher.py                 # dry-run
    python enrichment/ai_sales_actions_enricher.py --execute
    python enrichment/ai_sales_actions_enricher.py --execute --limit 20
    python enrichment/ai_sales_actions_enricher.py --execute --force
    python enrichment/ai_sales_actions_enricher.py --company-id <page_id>
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ── repo-local imports ───────────────────────────────────────────────────────
SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from core import constants as C  # noqa: E402
from core.notion_helpers import notion_request  # noqa: E402
from core.ai_sales_actions_parser import (  # noqa: E402
    parse_ai_sales_actions_typed,
    ParsedAISalesActions,
)

# ── logging ──────────────────────────────────────────────────────────────────
LOG_DIR = Path(__file__).resolve().parents[2] / "data" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger("ai_sales_actions_enricher")
logger.setLevel(logging.INFO)
if not logger.handlers:
    _fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    _sh = logging.StreamHandler()
    _sh.setFormatter(_fmt)
    logger.addHandler(_sh)
    _fh = logging.FileHandler(LOG_DIR / "ai_sales_actions_enricher.log")
    _fh.setFormatter(_fmt)
    logger.addHandler(_fh)

# ── env ──────────────────────────────────────────────────────────────────────
NOTION_BASE = "https://api.notion.com/v1"


def _require_env(key: str) -> str:
    v = os.getenv(key)
    if not v:
        raise EnvironmentError(
            f"Missing required env var {key}. "
            "Set NOTION_API_KEY, NOTION_DATABASE_ID_COMPANIES, NOTION_DATABASE_ID_CONTACTS."
        )
    return v


# ── Notion property builders (typed) ─────────────────────────────────────────

def _rt(text: str) -> Dict:
    text = (text or "").strip()
    if not text:
        return {"rich_text": []}
    # Notion rich_text segment cap = 2000 chars
    return {"rich_text": [{"type": "text", "text": {"content": text[:1990]}}]}


def _select(value: str) -> Dict:
    v = (value or "").strip()
    if not v:
        return {"select": None}
    return {"select": {"name": v}}


def _date_now() -> Dict:
    return {"date": {"start": datetime.now(timezone.utc).isoformat()}}


# ── select value guards ──────────────────────────────────────────────────────

VALID_PRIORITY = {C.AI_PRIORITY_P1, C.AI_PRIORITY_P2, C.AI_PRIORITY_P3}
VALID_FIT = {"High", "Medium", "Low"}
VALID_URGENCY = {"High", "Medium", "Low"}
VALID_ACTION = {C.AI_ACTION_CALL, C.AI_ACTION_EMAIL, C.AI_ACTION_SEQUENCE, C.AI_ACTION_NONE}


def _canonical_action(raw: str) -> str:
    v = (raw or "").strip().lower()
    if "call" in v or "phone" in v:
        return C.AI_ACTION_CALL
    if "sequence" in v or "cadence" in v or "nurture" in v:
        return C.AI_ACTION_SEQUENCE
    if "email" in v or "message" in v:
        return C.AI_ACTION_EMAIL
    if "none" in v or "skip" in v:
        return C.AI_ACTION_NONE
    return ""


def _canonical_urgency(raw: str) -> str:
    v = (raw or "").strip().lower()
    if v in {"high", "urgent", "critical"}:
        return "High"
    if v in {"medium", "med", "moderate"}:
        return "Medium"
    if v in {"low"}:
        return "Low"
    return ""


# ── Company query / write ────────────────────────────────────────────────────

def query_companies_with_ai_actions(
    companies_db_id: str,
    limit: Optional[int] = None,
    single_company_id: Optional[str] = None,
) -> List[Dict]:
    """Return raw Notion page objects for companies where AI Sales Actions is non-empty."""
    if single_company_id:
        r = notion_request("GET", f"{NOTION_BASE}/pages/{single_company_id}")
        r.raise_for_status()
        return [r.json()]

    pages: List[Dict] = []
    next_cursor: Optional[str] = None
    page_size = 100

    filter_payload = {
        "property": C.FIELD_AI_SALES_ACTIONS_RAW,
        "rich_text": {"is_not_empty": True},
    }

    while True:
        body = {"filter": filter_payload, "page_size": page_size}
        if next_cursor:
            body["start_cursor"] = next_cursor

        r = notion_request(
            "POST",
            f"{NOTION_BASE}/databases/{companies_db_id}/query",
            json=body,
        )
        if r.status_code != 200:
            logger.error("Companies query failed: %s %s", r.status_code, r.text[:500])
            break
        data = r.json()
        pages.extend(data.get("results", []))
        if limit and len(pages) >= limit:
            pages = pages[:limit]
            break
        if not data.get("has_more"):
            break
        next_cursor = data.get("next_cursor")

    return pages


def _read_rich_text(prop: Dict) -> str:
    if not prop or prop.get("type") != "rich_text":
        return ""
    return "".join(seg.get("plain_text", "") for seg in prop.get("rich_text") or [])


def _read_date(prop: Dict) -> Optional[str]:
    if not prop or prop.get("type") != "date":
        return None
    d = prop.get("date") or {}
    return d.get("start")


def _read_relation_ids(prop: Dict) -> List[str]:
    if not prop or prop.get("type") != "relation":
        return []
    return [r.get("id") for r in prop.get("relation") or [] if r.get("id")]


def _needs_reparse(page: Dict, force: bool) -> bool:
    if force:
        return True
    props = page.get("properties", {})
    parsed_at = _read_date(props.get(C.FIELD_AI_SALES_ACTIONS_PARSED_AT, {}))
    if not parsed_at:
        return True
    # re-parse if source last_edited_time is newer than parsed_at
    last_edit = page.get("last_edited_time")
    if not last_edit:
        return True
    try:
        return datetime.fromisoformat(last_edit.replace("Z", "+00:00")) > datetime.fromisoformat(parsed_at.replace("Z", "+00:00"))
    except Exception:
        return True


def build_company_props(parsed: ParsedAISalesActions) -> Dict:
    """Return a Notion properties dict of only the parsed AI fields we write."""
    props: Dict = {}

    # rich_text fields (always safe)
    props[C.FIELD_AI_SEGMENT] = _rt(parsed.segment)
    props[C.FIELD_AI_SIGNAL] = _rt(parsed.signal)
    props[C.FIELD_AI_PAIN_SUMMARY] = _rt(parsed.pain)
    props[C.FIELD_AI_TARGET_ROLE] = _rt(parsed.target_role)
    props[C.FIELD_AI_TONE] = _rt(parsed.tone)

    # select fields — guarded
    if parsed.priority in VALID_PRIORITY:
        props[C.FIELD_AI_PRIORITY] = _select(parsed.priority)
    if parsed.fit in VALID_FIT:
        props[C.FIELD_AI_FIT] = _select(parsed.fit)

    urgency = _canonical_urgency(parsed.urgency)
    if urgency in VALID_URGENCY:
        props[C.FIELD_AI_URGENCY] = _select(urgency)

    action = _canonical_action(parsed.action)
    if action in VALID_ACTION:
        props[C.FIELD_AI_ACTION_TYPE] = _select(action)

    props[C.FIELD_AI_SALES_ACTIONS_PARSED_AT] = _date_now()
    return props


def build_contact_props(parsed: ParsedAISalesActions) -> Dict:
    """Per-contact propagation props — only populated fields are written."""
    props: Dict = {}
    if parsed.call_hook:
        props[C.FIELD_AI_CALL_HOOK] = _rt(parsed.call_hook_joined)
    if parsed.email_subject:
        props[C.FIELD_AI_EMAIL_SUBJECT] = _rt(parsed.email_subject)
    if parsed.email_opening:
        props[C.FIELD_AI_EMAIL_OPENING] = _rt(parsed.email_opening)
    if parsed.email_pain:
        props[C.FIELD_AI_EMAIL_PAIN] = _rt(parsed.email_pain)
    if parsed.email_value:
        props[C.FIELD_AI_EMAIL_VALUE] = _rt(parsed.email_value)
    if parsed.email_cta:
        props[C.FIELD_AI_EMAIL_CTA] = _rt(parsed.email_cta)
    return props


def update_page(page_id: str, properties: Dict) -> bool:
    r = notion_request(
        "PATCH",
        f"{NOTION_BASE}/pages/{page_id}",
        json={"properties": properties},
    )
    if r.status_code != 200:
        logger.error("Update %s failed: %s %s", page_id, r.status_code, r.text[:400])
        return False
    return True


def find_linked_contacts(contacts_db_id: str, company_page_id: str) -> List[str]:
    """Query Contacts DB for contacts whose Company relation includes this company."""
    body = {
        "filter": {
            "property": "Company",  # contacts → company relation
            "relation": {"contains": company_page_id},
        },
        "page_size": 100,
    }
    ids: List[str] = []
    cursor = None
    while True:
        if cursor:
            body["start_cursor"] = cursor
        r = notion_request(
            "POST",
            f"{NOTION_BASE}/databases/{contacts_db_id}/query",
            json=body,
        )
        if r.status_code != 200:
            logger.warning(
                "Contacts lookup for %s failed: %s", company_page_id, r.status_code
            )
            break
        data = r.json()
        for pg in data.get("results", []):
            ids.append(pg["id"])
        if not data.get("has_more"):
            break
        cursor = data.get("next_cursor")
    return ids


# ── main loop ────────────────────────────────────────────────────────────────

def run(
    execute: bool = False,
    limit: Optional[int] = None,
    force: bool = False,
    single_company_id: Optional[str] = None,
    skip_contacts: bool = False,
) -> Dict[str, int]:
    companies_db = _require_env("NOTION_DATABASE_ID_COMPANIES")
    contacts_db = _require_env("NOTION_DATABASE_ID_CONTACTS")
    _require_env("NOTION_API_KEY")

    stats = {
        "companies_scanned": 0,
        "companies_parsed": 0,
        "companies_updated": 0,
        "companies_skipped_fresh": 0,
        "companies_skipped_invalid": 0,
        "contacts_updated": 0,
        "errors": 0,
    }

    logger.info(
        "Enricher start — mode=%s limit=%s force=%s",
        "EXECUTE" if execute else "DRY-RUN",
        limit,
        force,
    )

    pages = query_companies_with_ai_actions(
        companies_db_id=companies_db,
        limit=limit,
        single_company_id=single_company_id,
    )
    logger.info("Found %d companies with AI Sales Actions populated", len(pages))

    for page in pages:
        stats["companies_scanned"] += 1
        page_id = page["id"]
        props = page.get("properties", {})

        raw = _read_rich_text(props.get(C.FIELD_AI_SALES_ACTIONS_RAW, {}))
        if not raw.strip():
            stats["companies_skipped_invalid"] += 1
            continue

        if not _needs_reparse(page, force):
            stats["companies_skipped_fresh"] += 1
            continue

        parsed = parse_ai_sales_actions_typed(raw)
        if not parsed.is_valid:
            stats["companies_skipped_invalid"] += 1
            logger.info("Company %s: unparseable/too-sparse — skipped", page_id)
            continue
        stats["companies_parsed"] += 1

        company_props = build_company_props(parsed)
        contact_props = build_contact_props(parsed)

        logger.info(
            "Company %s → priority=%s fit=%s action=%s hooks=%d email=%s",
            page_id,
            parsed.priority or "-",
            parsed.fit or "-",
            _canonical_action(parsed.action) or "-",
            len(parsed.call_hook),
            "Y" if parsed.email_subject else "N",
        )

        if not execute:
            # dry-run: still look up contacts to report count
            if contact_props and not skip_contacts:
                ids = find_linked_contacts(contacts_db, page_id)
                logger.info("  would update %d contacts", len(ids))
            continue

        # ── WRITE COMPANY ──
        try:
            ok = update_page(page_id, company_props)
            if ok:
                stats["companies_updated"] += 1
            else:
                stats["errors"] += 1
                continue
        except Exception as e:
            stats["errors"] += 1
            logger.error("Company %s write error: %s", page_id, e)
            continue

        # ── WRITE CONTACTS ──
        if contact_props and not skip_contacts:
            try:
                contact_ids = find_linked_contacts(contacts_db, page_id)
                for cid in contact_ids:
                    if update_page(cid, contact_props):
                        stats["contacts_updated"] += 1
                    else:
                        stats["errors"] += 1
            except Exception as e:
                stats["errors"] += 1
                logger.error("Contact propagation for %s error: %s", page_id, e)

    # write stats file
    stats_file = LOG_DIR / "ai_sales_actions_enricher_stats.json"
    try:
        stats_file.write_text(json.dumps(stats, indent=2))
    except Exception:
        pass

    logger.info("Done — %s", json.dumps(stats))
    return stats


# ── CLI ──────────────────────────────────────────────────────────────────────

def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Apply Apollo AI Sales Actions to Notion.")
    p.add_argument("--execute", action="store_true", help="Apply writes (default: dry-run)")
    p.add_argument("--limit", type=int, default=None, help="Limit number of companies processed")
    p.add_argument("--force", action="store_true", help="Reparse even if Parsed At is fresh")
    p.add_argument("--company-id", default=None, help="Process a single company page ID")
    p.add_argument("--skip-contacts", action="store_true", help="Do not propagate to contacts")
    return p.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    try:
        run(
            execute=args.execute,
            limit=args.limit,
            force=args.force,
            single_company_id=args.company_id,
            skip_contacts=args.skip_contacts,
        )
    except EnvironmentError as e:
        logger.error(str(e))
        sys.exit(2)
    except KeyboardInterrupt:
        logger.warning("Interrupted by user")
        sys.exit(130)
