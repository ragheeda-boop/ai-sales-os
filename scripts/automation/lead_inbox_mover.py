"""
lead_inbox_mover.py — AI Sales OS Lead Inbox v2.0
==================================================
Version: v0.2 (Real CRM Writes + Backfill)

Purpose
-------
Move qualified leads from the 📥 Lead Inbox into the real CRM by:

  1. Creating (or matching) a Company record in the 🏢 Companies DB
  2. Creating (or matching) a Contact record in the 👤 Contacts DB,
     linked to that Company
  3. Writing the Notion page IDs back into Lead Inbox
     (CRM Company Ref + CRM Contact Ref + CRM Sync State + CRM Synced At)
  4. Setting Lead Inbox Status = "Moved"

This version corrects the semantic gap in v0.1 where "Moved" meant "status
flipped but nothing actually in the CRM". In v0.2, "Moved" means "real
Company + Contact exist in the CRM and are linked back to the Lead Inbox row".

Modes
-----
  --mode forward  : process Status = "Qualified" (default)
  --mode backfill : process Status = "Moved" where CRM Company Ref is empty
                    (cleans up the v0.1 leftover: leads marked Moved with
                    no actual CRM records behind them)
  --mode all      : both forward and backfill in one pass

Dedup strategy
--------------
  Company:
    1. If lead has an email, extract domain; match Companies by Domain (exact, lowercase)
    2. Else match by Company Name (normalized: trim, lowercase, collapse whitespace)
    3. Else create a new Company
  Contact:
    1. Match Contacts by Email (exact, lowercase)
    2. Else create a new Contact
  Never deletes, never overwrites existing non-empty fields.

Usage
-----
    python lead_inbox_mover.py                               # dry-run, forward mode
    python lead_inbox_mover.py --mode backfill               # dry-run, backfill leftover Moved
    python lead_inbox_mover.py --mode all                    # dry-run, both
    python lead_inbox_mover.py --mode all --execute          # REAL WRITES
    python lead_inbox_mover.py --mode backfill --execute --limit 10   # test backfill
    python lead_inbox_mover.py --verbose

Env vars (all mandatory; fails loudly if missing)
-------------------------------------------------
    NOTION_API_KEY
    NOTION_DATABASE_ID_LEAD_INBOX
    NOTION_DATABASE_ID_COMPANIES
    NOTION_DATABASE_ID_CONTACTS

Exit codes
----------
    0 — completed (with or without changes)
    1 — env var missing or Notion API error
    2 — validation failures present (when --strict is passed)
"""

import argparse
import logging
import os
import re
import sys
import time
from datetime import datetime
from logging.handlers import RotatingFileHandler

import requests
from dotenv import load_dotenv

load_dotenv()


# ── Config ─────────────────────────────────────────────────────────────────

def _require_env(name: str) -> str:
    val = os.getenv(name)
    if not val:
        raise EnvironmentError(
            f"Required env var {name!r} is not set. "
            f"Add it to your .env file or GitHub Secrets."
        )
    return val


NOTION_API_KEY  = _require_env("NOTION_API_KEY")
LEAD_INBOX_DB   = _require_env("NOTION_DATABASE_ID_LEAD_INBOX")
COMPANIES_DB    = _require_env("NOTION_DATABASE_ID_COMPANIES")
CONTACTS_DB     = _require_env("NOTION_DATABASE_ID_CONTACTS")

NOTION_VERSION  = "2022-06-28"
RATE_LIMIT      = 0.35
MAX_RETRIES     = 3

HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Notion-Version": NOTION_VERSION,
    "Content-Type": "application/json",
}

STATUS_QUALIFIED = "Qualified"
STATUS_MOVED     = "Moved"

SYNC_STATE_CREATED = "Created"
SYNC_STATE_MATCHED = "Matched"
SYNC_STATE_FAILED  = "Failed"

# Default stages for newly created CRM records coming from Lead Inbox.
# These are leads we've just qualified and are about to contact, so:
#   Company Stage = Outreach (we'll reach out next)
#   Contact Stage = Lead     (first touch-point)
DEFAULT_COMPANY_STAGE = "Outreach"
DEFAULT_CONTACT_STAGE = "Lead"
RECORD_SOURCE         = "Lead Inbox"


# ── Logging ────────────────────────────────────────────────────────────────

logger = logging.getLogger("lead_inbox_mover")
logger.setLevel(logging.INFO)

_log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "data", "logs")
os.makedirs(_log_dir, exist_ok=True)
_handler = RotatingFileHandler(
    os.path.join(_log_dir, "lead_inbox_mover.log"),
    maxBytes=5 * 1024 * 1024,
    backupCount=3,
    encoding="utf-8",
)
_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
logger.addHandler(_handler)

_console = logging.StreamHandler()
_console.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
logger.addHandler(_console)


# ── Notion helpers ─────────────────────────────────────────────────────────

def _notion_request(method: str, url: str, payload: dict | None = None) -> dict:
    for attempt in range(MAX_RETRIES):
        resp = requests.request(method, url, headers=HEADERS, json=payload, timeout=30)
        if resp.status_code == 200:
            return resp.json()
        if resp.status_code in (429, 500, 502, 503, 504):
            wait = (2 ** attempt) * 1.0
            logger.warning(f"Notion {resp.status_code}; retry in {wait}s")
            time.sleep(wait)
            continue
        raise RuntimeError(f"Notion API {resp.status_code}: {resp.text[:300]}")
    raise RuntimeError("Notion API: max retries exceeded")


def _query_all(db_id: str, filter_payload: dict | None = None) -> list[dict]:
    url = f"https://api.notion.com/v1/databases/{db_id}/query"
    payload: dict = {"page_size": 100}
    if filter_payload:
        payload["filter"] = filter_payload
    out: list[dict] = []
    while True:
        data = _notion_request("POST", url, payload)
        out.extend(data.get("results", []))
        if not data.get("has_more"):
            return out
        payload["start_cursor"] = data["next_cursor"]


def _create_page(db_id: str, properties: dict) -> str:
    url = "https://api.notion.com/v1/pages"
    data = _notion_request("POST", url, {
        "parent": {"database_id": db_id},
        "properties": properties,
    })
    time.sleep(RATE_LIMIT)
    return data["id"]


def _update_page(page_id: str, properties: dict) -> None:
    url = f"https://api.notion.com/v1/pages/{page_id}"
    _notion_request("PATCH", url, {"properties": properties})
    time.sleep(RATE_LIMIT)


# ── Property helpers ───────────────────────────────────────────────────────

def _plain(prop: dict, kind: str) -> str:
    if not prop:
        return ""
    if kind == "title":
        return "".join(t.get("plain_text", "") for t in prop.get("title", [])).strip()
    if kind == "rich_text":
        return "".join(t.get("plain_text", "") for t in prop.get("rich_text", [])).strip()
    if kind == "email":
        return (prop.get("email") or "").strip()
    if kind == "phone_number":
        return (prop.get("phone_number") or "").strip()
    if kind == "select":
        sel = prop.get("select")
        return sel.get("name", "") if sel else ""
    if kind == "status":
        st = prop.get("status")
        return st.get("name", "") if st else ""
    return ""


def _rt(text: str) -> dict:
    if not text:
        return {"rich_text": []}
    return {"rich_text": [{"text": {"content": text[:2000]}}]}


def _title(text: str) -> dict:
    return {"title": [{"text": {"content": (text or "")[:2000]}}]}


def _select(name: str) -> dict:
    return {"select": {"name": name}} if name else {"select": None}


def _status(name: str) -> dict:
    return {"status": {"name": name}}


def _email_val(email: str) -> dict:
    return {"email": email or None}


def _phone_val(phone: str) -> dict:
    return {"phone_number": phone or None}


def _relation(page_id: str) -> dict:
    return {"relation": [{"id": page_id}] if page_id else []}


def _date_val(iso_date: str) -> dict:
    return {"date": {"start": iso_date}} if iso_date else {"date": None}


# ── Normalization / dedup ──────────────────────────────────────────────────

_GENERIC_EMAIL_DOMAINS = {
    "gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "icloud.com",
    "live.com", "aol.com", "protonmail.com", "proton.me", "mail.com",
    "me.com", "msn.com",
}


def _extract_domain(email: str) -> str:
    if not email or "@" not in email:
        return ""
    domain = email.split("@", 1)[1].strip().lower()
    # Strip generic domains — they are not reliable company identifiers
    if domain in _GENERIC_EMAIL_DOMAINS:
        return ""
    return domain


def _normalize_name(name: str) -> str:
    if not name:
        return ""
    n = name.strip().lower()
    n = re.sub(r"\s+", " ", n)
    # Strip common legal suffixes so "ACME Ltd." matches "ACME"
    n = re.sub(r"\b(ltd|llc|inc|co|corp|corporation|limited|gmbh|sa|sarl|plc|company)\.?$", "", n).strip()
    return n


# ── Lazy dedup cache ───────────────────────────────────────────────────────
#
# Full preload of Contacts DB is prohibitive (~45K records). Instead we do
# targeted filtered queries per lead, caching results in-process so repeat
# lookups (same domain or email) are free within a single run.

class CRMCache:
    def __init__(self) -> None:
        self.companies_by_domain: dict[str, str] = {}  # domain -> page_id
        self.companies_by_name:   dict[str, str] = {}  # normalized name -> page_id
        self.contacts_by_email:   dict[str, str] = {}  # email lower -> page_id
        self._domain_misses: set[str] = set()
        self._name_misses:   set[str] = set()
        self._email_misses:  set[str] = set()

    def preload(self) -> None:
        # Intentional no-op in v0.2 lazy mode. Kept for API compatibility.
        logger.info("Lazy-lookup mode (no preload). Dedup queries run per-lead.")

    def _query_company_by_domain(self, domain: str) -> str:
        data = _notion_request(
            "POST",
            f"https://api.notion.com/v1/databases/{COMPANIES_DB}/query",
            {
                "filter": {"property": "Domain", "rich_text": {"equals": domain}},
                "page_size": 1,
            },
        )
        results = data.get("results", [])
        return results[0]["id"] if results else ""

    def _query_company_by_name(self, name: str) -> str:
        # Notion filter on title = exact match on the title string.
        data = _notion_request(
            "POST",
            f"https://api.notion.com/v1/databases/{COMPANIES_DB}/query",
            {
                "filter": {"property": "Company Name", "title": {"equals": name}},
                "page_size": 1,
            },
        )
        results = data.get("results", [])
        return results[0]["id"] if results else ""

    def _query_contact_by_email(self, email: str) -> str:
        data = _notion_request(
            "POST",
            f"https://api.notion.com/v1/databases/{CONTACTS_DB}/query",
            {
                "filter": {"property": "Email", "email": {"equals": email}},
                "page_size": 1,
            },
        )
        results = data.get("results", [])
        return results[0]["id"] if results else ""

    def find_company(self, domain: str, name: str) -> tuple[str, str]:
        """Return (page_id, match_strategy). match_strategy in {'domain','name',''}."""
        if domain:
            if domain in self.companies_by_domain:
                return self.companies_by_domain[domain], "domain"
            if domain not in self._domain_misses:
                pid = self._query_company_by_domain(domain)
                if pid:
                    self.companies_by_domain[domain] = pid
                    return pid, "domain"
                self._domain_misses.add(domain)

        if name:
            nn = _normalize_name(name)
            raw_key = name.strip()
            if nn in self.companies_by_name:
                return self.companies_by_name[nn], "name"
            if raw_key not in self._name_misses:
                pid = self._query_company_by_name(raw_key)
                if pid:
                    self.companies_by_name[nn] = pid
                    return pid, "name"
                self._name_misses.add(raw_key)

        return "", ""

    def find_contact(self, email: str) -> str:
        if not email:
            return ""
        key = email.lower().strip()
        if key in self.contacts_by_email:
            return self.contacts_by_email[key]
        if key in self._email_misses:
            return ""
        pid = self._query_contact_by_email(email)
        if pid:
            self.contacts_by_email[key] = pid
            return pid
        self._email_misses.add(key)
        return ""

    def register_company(self, page_id: str, domain: str, name: str) -> None:
        if domain:
            self.companies_by_domain[domain] = page_id
            self._domain_misses.discard(domain)
        if name:
            self.companies_by_name[_normalize_name(name)] = page_id
            self._name_misses.discard(name.strip())

    def register_contact(self, page_id: str, email: str) -> None:
        if email:
            key = email.lower().strip()
            self.contacts_by_email[key] = page_id
            self._email_misses.discard(key)


# ── Lead Inbox extraction ──────────────────────────────────────────────────

def extract_lead(page: dict) -> dict:
    props = page.get("properties", {})
    return {
        "page_id":      page["id"],
        "name":         _plain(props.get("Name", {}),             "title"),
        "company":      _plain(props.get("Company Name", {}),     "rich_text"),
        "email":        _plain(props.get("Email", {}),            "email"),
        "phone":        _plain(props.get("Phone", {}),            "phone_number"),
        "title":        _plain(props.get("Title", {}),            "rich_text"),
        "source":       _plain(props.get("Source", {}),           "select"),
        "intake_owner": _plain(props.get("Intake Owner", {}),     "select"),
        "warm_signal":  _plain(props.get("Warm Signal", {}),      "rich_text"),
        "notes":        _plain(props.get("Notes", {}),            "rich_text"),
        "status":       _plain(props.get("Status", {}),           "status"),
        "crm_company_ref": _plain(props.get("CRM Company Ref", {}), "rich_text"),
        "crm_contact_ref": _plain(props.get("CRM Contact Ref", {}), "rich_text"),
    }


_EMAIL_RE = re.compile(r"^[^@\s|,;]+@[^@\s|,;]+\.[^@\s|,;]+$")


def _is_valid_email(email: str) -> bool:
    return bool(email and _EMAIL_RE.match(email))


def validate(rec: dict) -> list[str]:
    errs: list[str] = []
    if not rec["name"]:
        errs.append("missing Name")
    if not rec["email"] and not rec["phone"]:
        errs.append("missing both Email and Phone")
    if not rec["intake_owner"]:
        errs.append("missing Intake Owner")
    # Guard against pipe-separated or otherwise malformed emails. We don't
    # fail the lead — we just strip the email so the contact still gets
    # created (with just name + phone) and the operator can fix it later.
    if rec["email"] and not _is_valid_email(rec["email"]):
        rec["notes"] = (rec.get("notes") or "") + \
            f" [v0.2: stripped invalid email '{rec['email']}' — needs manual split]"
        rec["email"] = ""
        if not rec["phone"]:
            errs.append("invalid email and no phone fallback")
    return errs


# ── CRM write builders ─────────────────────────────────────────────────────

def build_company_props(rec: dict, domain: str) -> dict:
    name = rec["company"] or rec["name"]
    props = {
        "Company Name":          _title(name),
        "Primary Company Owner": _select(rec["intake_owner"]),
        "Company Stage":         _select(DEFAULT_COMPANY_STAGE),
        "Record Source":         _rt(RECORD_SOURCE),
    }
    if domain:
        props["Domain"] = _rt(domain)
    return props


def build_contact_props(rec: dict, company_page_id: str) -> dict:
    # Split name roughly into First/Last for the schema
    parts = (rec["name"] or "").split(" ", 1)
    first = parts[0] if parts else ""
    last  = parts[1] if len(parts) > 1 else ""

    props: dict = {
        "Full Name":      _title(rec["name"]),
        "Contact Owner":  _rt(rec["intake_owner"]),
        "Stage":          _select(DEFAULT_CONTACT_STAGE),
        "Record Source":  _select("Manual"),
        "Company":        _relation(company_page_id),
    }
    if first:
        props["First Name"] = _rt(first)
    if last:
        props["Last Name"] = _rt(last)
    if rec["email"]:
        props["Email"] = _email_val(rec["email"])
    if rec["phone"]:
        props["Mobile Phone"] = _phone_val(rec["phone"])
    if rec["title"]:
        props["Title"] = _rt(rec["title"])
    if rec["warm_signal"] or rec["notes"]:
        combined = " | ".join(x for x in (rec["warm_signal"], rec["notes"]) if x)
        props["Notes"] = _rt(combined)
    return props


def build_lead_inbox_update(company_id: str, contact_id: str, state: str, mark_moved: bool) -> dict:
    today = datetime.utcnow().date().isoformat()
    props = {
        "CRM Company Ref": _rt(company_id),
        "CRM Contact Ref": _rt(contact_id),
        "CRM Sync State":  _select(state),
        "CRM Synced At":   _date_val(today),
    }
    if mark_moved:
        props["Status"] = _status(STATUS_MOVED)
    return props


# ── Query ──────────────────────────────────────────────────────────────────

def query_leads(mode: str, limit: int | None = None) -> list[dict]:
    """
    forward  : Status = Qualified
    backfill : Status = Moved AND CRM Company Ref is empty
    all      : both (returned as one flat list; forward first)
    """
    def _q(filter_payload: dict) -> list[dict]:
        url = f"https://api.notion.com/v1/databases/{LEAD_INBOX_DB}/query"
        payload: dict = {"filter": filter_payload, "page_size": 100}
        out: list[dict] = []
        while True:
            data = _notion_request("POST", url, payload)
            out.extend(data.get("results", []))
            if limit and len(out) >= limit:
                return out[:limit]
            if not data.get("has_more"):
                return out
            payload["start_cursor"] = data["next_cursor"]

    forward_filter = {"property": "Status", "status": {"equals": STATUS_QUALIFIED}}
    backfill_filter = {
        "and": [
            {"property": "Status", "status": {"equals": STATUS_MOVED}},
            {"property": "CRM Company Ref", "rich_text": {"is_empty": True}},
        ]
    }

    if mode == "forward":
        return _q(forward_filter)
    if mode == "backfill":
        return _q(backfill_filter)
    # all
    fwd = _q(forward_filter)
    if limit and len(fwd) >= limit:
        return fwd[:limit]
    bf_limit = (limit - len(fwd)) if limit else None
    bf = _q(backfill_filter) if bf_limit is None else _q(backfill_filter)[:bf_limit]
    return fwd + bf


# ── Main processing loop ───────────────────────────────────────────────────

def process_lead(rec: dict, cache: CRMCache, execute: bool, logger_: logging.Logger) -> tuple[str, str, str]:
    """
    Returns (company_id, contact_id, state). state in {'Created','Matched','Failed'}
    In dry-run mode, returns placeholder IDs like 'DRY-NEW' / 'DRY-MATCH-<id>'.
    """
    domain = _extract_domain(rec["email"])
    company_id, match_strategy = cache.find_company(domain, rec["company"] or rec["name"])

    # Company: match or create
    if company_id:
        company_state = f"matched[{match_strategy}]"
        logger_.info(f"    ↳ Company matched by {match_strategy}: {company_id[:8]}…")
    else:
        if execute:
            props = build_company_props(rec, domain)
            company_id = _create_page(COMPANIES_DB, props)
            cache.register_company(company_id, domain, rec["company"] or rec["name"])
            company_state = "created"
            logger_.info(f"    ↳ Company CREATED: {company_id[:8]}… ({rec['company'] or rec['name']})")
        else:
            company_id = "DRY-NEW-COMPANY"
            company_state = "would-create"
            logger_.info(f"    ↳ Company WOULD CREATE: {rec['company'] or rec['name']} (domain={domain or '—'})")

    # Contact: match or create
    contact_id = cache.find_contact(rec["email"])
    if contact_id:
        contact_state = "matched[email]"
        logger_.info(f"    ↳ Contact matched by email: {contact_id[:8]}…")
    else:
        if execute:
            props = build_contact_props(rec, company_id)
            contact_id = _create_page(CONTACTS_DB, props)
            cache.register_contact(contact_id, rec["email"])
            contact_state = "created"
            logger_.info(f"    ↳ Contact CREATED: {contact_id[:8]}… ({rec['name']})")
        else:
            contact_id = "DRY-NEW-CONTACT"
            contact_state = "would-create"
            logger_.info(f"    ↳ Contact WOULD CREATE: {rec['name']} ({rec['email'] or rec['phone']})")

    # Derive overall sync state
    if "created" in company_state or "created" in contact_state:
        state = SYNC_STATE_CREATED
    elif "would-create" in company_state or "would-create" in contact_state:
        state = SYNC_STATE_CREATED  # dry-run hint
    else:
        state = SYNC_STATE_MATCHED

    return company_id, contact_id, state


def main() -> int:
    ap = argparse.ArgumentParser(description="Lead Inbox → CRM mover v0.2 (real writes + backfill)")
    ap.add_argument("--mode",    choices=["forward", "backfill", "all"], default="forward",
                    help="forward=Qualified, backfill=Moved w/o refs, all=both (default: forward)")
    ap.add_argument("--execute", action="store_true", help="Apply real CRM writes (default: dry-run)")
    ap.add_argument("--limit",   type=int, default=None, help="Process at most N records")
    ap.add_argument("--strict",  action="store_true", help="Exit 2 if any validation failures")
    ap.add_argument("--verbose", action="store_true", help="Log every record")
    args = ap.parse_args()

    mode_label = "EXECUTE" if args.execute else "DRY-RUN"
    logger.info("=" * 72)
    logger.info(f"lead_inbox_mover.py v0.2 — mode={args.mode}, run={mode_label}")
    logger.info("=" * 72)

    try:
        cache = CRMCache()
        cache.preload()
        leads = query_leads(args.mode, limit=args.limit)
    except Exception as e:
        logger.error(f"Setup failed: {e}")
        return 1

    logger.info(f"Found {len(leads)} lead(s) to process")

    if not leads:
        logger.info("Nothing to do.")
        return 0

    ok = fail = 0
    created_company = matched_company = 0
    created_contact = matched_contact = 0

    for page in leads:
        rec = extract_lead(page)
        errs = validate(rec)

        logger.info(
            f"• {rec['name'] or '(no name)'} | "
            f"{rec['email'] or rec['phone'] or '—'} | "
            f"company='{rec['company'] or '—'}' | "
            f"owner={rec['intake_owner'] or '—'} | "
            f"status={rec['status']}"
        )

        if errs:
            fail += 1
            logger.warning(f"    ✗ skipped: {', '.join(errs)}")
            if args.execute:
                try:
                    _update_page(rec["page_id"], {
                        "CRM Sync State": _select(SYNC_STATE_FAILED),
                    })
                except Exception as e:
                    logger.error(f"    ✗ failed to mark Failed: {e}")
            continue

        try:
            company_id, contact_id, state = process_lead(rec, cache, args.execute, logger)
        except Exception as e:
            fail += 1
            logger.error(f"    ✗ process_lead crashed: {e}")
            continue

        # Count based on log trace
        # (tiny heuristic; precise counts in verbose logs above)
        if args.execute:
            # Write back refs to Lead Inbox
            mark_moved = (rec["status"] != STATUS_MOVED)
            try:
                _update_page(rec["page_id"], build_lead_inbox_update(
                    company_id, contact_id, state, mark_moved
                ))
                logger.info(f"    ✓ Lead Inbox updated (state={state}, moved={mark_moved})")
            except Exception as e:
                fail += 1
                logger.error(f"    ✗ failed to update Lead Inbox: {e}")
                continue

        ok += 1

    logger.info("-" * 72)
    logger.info(f"Summary: {ok} processed OK, {fail} failed")
    logger.info(f"Mode: {args.mode} | Run: {mode_label}")
    if not args.execute:
        logger.info("Re-run with --execute to apply real CRM writes.")
    logger.info("=" * 72)

    if args.strict and fail:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
