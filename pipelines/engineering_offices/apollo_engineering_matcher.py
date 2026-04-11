#!/usr/bin/env python3
"""
apollo_engineering_matcher.py
==============================
Phase 3: Match engineering offices against Apollo accounts & contacts

For each company in the Notion DB:
  1. Try to find an Apollo Account by domain / phone / name
  2. Try to find an Apollo Contact by email / mobile
  3. Write back: Apollo Matched, Match Confidence, Apollo Account ID, Apollo Contact ID
  4. If matched contact is NOT in the "مكاتب هندسية خار apollo" list — add them

Run:
    python apollo_engineering_matcher.py
    python apollo_engineering_matcher.py --dry-run
    python apollo_engineering_matcher.py --limit 50
    python apollo_engineering_matcher.py --unmatched-only
"""

import os, sys, time, json, argparse, logging, re
from pathlib import Path
from datetime import datetime

import requests
from dotenv import load_dotenv

from constants_eng import (
    NOTION_DB_ID, APOLLO_LIST_NAME,
    F_NAME, F_CR, F_EMAIL, F_MOBILE, F_WA, F_CITY, F_REGION,
    F_APOLLO_MATCHED, F_MATCH_CONF, F_APOLLO_ACC_ID, F_APOLLO_CON_ID,
    F_IN_LIST,
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
        logging.FileHandler("apollo_engineering_matcher.log", encoding="utf-8"),
    ],
)
log = logging.getLogger(__name__)

# ───────────────────────────────────────────────
# Load credentials
# ───────────────────────────────────────────────

load_dotenv(Path(__file__).parent / ".env")
NOTION_TOKEN = os.getenv("NOTION_API_KEY") or os.getenv("NOTION_TOKEN")
APOLLO_KEY   = os.getenv("APOLLO_API_KEY")

if not NOTION_TOKEN:
    sys.exit("❌  NOTION_API_KEY not set in .env")
if not APOLLO_KEY:
    sys.exit("❌  APOLLO_API_KEY not set in .env")

NOTION_HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json",
}
APOLLO_BASE = "https://api.apollo.io/v1"

# ───────────────────────────────────────────────
# HTTP helpers
# ───────────────────────────────────────────────

def _notion_req(method: str, url: str, **kwargs) -> dict:
    for attempt in range(6):
        resp = requests.request(method, url, headers=NOTION_HEADERS, **kwargs)
        if resp.status_code == 429:
            time.sleep(2 ** attempt); continue
        if resp.status_code >= 500:
            time.sleep(2 ** attempt); continue
        resp.raise_for_status()
        return resp.json()
    raise RuntimeError(f"Notion request failed: {url}")


def _apollo_req(method: str, path: str, **kwargs) -> dict:
    url = f"{APOLLO_BASE}{path}"
    params = kwargs.pop("params", {})
    params["api_key"] = APOLLO_KEY
    for attempt in range(5):
        resp = requests.request(method, url, params=params, **kwargs)
        if resp.status_code == 429:
            time.sleep(3 ** attempt); continue
        if resp.status_code >= 500:
            time.sleep(2 ** attempt); continue
        if resp.status_code == 404:
            return {}
        resp.raise_for_status()
        return resp.json()
    return {}


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
# Extract helpers
# ───────────────────────────────────────────────

def _get_text(props: dict, field: str) -> str:
    blocks = props.get(field, {}).get("rich_text", [])
    return blocks[0]["plain_text"].strip() if blocks else ""

def _get_title(props: dict, field: str) -> str:
    blocks = props.get(field, {}).get("title", [])
    return blocks[0]["plain_text"].strip() if blocks else ""

def _get_email(props: dict, field: str) -> str:
    return (props.get(field, {}).get("email") or "").strip()

def _get_phone(props: dict, field: str) -> str:
    return (props.get(field, {}).get("phone_number") or "").strip()

def _get_checkbox(props: dict, field: str) -> bool:
    return bool(props.get(field, {}).get("checkbox", False))

def _get_select(props: dict, field: str) -> str:
    sel = props.get(field, {}).get("select")
    return sel["name"] if sel else ""


def extract_email_domain(email: str) -> str:
    """Extract domain from email for Apollo account search."""
    m = re.search(r"@([\w\.\-]+)", email)
    return m.group(1) if m else ""


# ───────────────────────────────────────────────
# Apollo search functions
# ───────────────────────────────────────────────

def apollo_search_contact_by_email(email: str) -> dict | None:
    """Search Apollo contacts by email address."""
    if not email:
        return None
    data = _apollo_req("GET", "/contacts/search", params={"q_keywords": email, "page": 1, "per_page": 1})
    contacts = data.get("contacts", [])
    if contacts:
        return contacts[0]
    # Try people match (more accurate)
    data = _apollo_req("POST", "/people/match", json={"email": email, "reveal_personal_emails": False})
    person = data.get("person")
    return person


def apollo_search_contact_by_phone(phone: str) -> dict | None:
    """Search Apollo contacts by phone number."""
    if not phone:
        return None
    # Clean to digits only for comparison
    digits = re.sub(r"\D", "", phone)
    data = _apollo_req("GET", "/contacts/search", params={
        "q_keywords": phone,
        "page": 1,
        "per_page": 5,
    })
    for c in data.get("contacts", []):
        c_phone = re.sub(r"\D", "", c.get("phone_numbers", [{}])[0].get("sanitized_number", "") if c.get("phone_numbers") else "")
        if c_phone and c_phone.endswith(digits[-9:]):
            return c
    return None


def apollo_search_account_by_domain(domain: str) -> dict | None:
    """Search Apollo accounts by domain."""
    if not domain or domain in ("gmail.com", "yahoo.com", "hotmail.com", "outlook.com"):
        return None
    data = _apollo_req("GET", "/accounts/search", params={
        "q_organization_domains": domain,
        "page": 1,
        "per_page": 1,
    })
    accounts = data.get("accounts", [])
    return accounts[0] if accounts else None


def apollo_search_account_by_name(name: str, city: str = "") -> dict | None:
    """Search Apollo accounts by company name."""
    if not name:
        return None
    query = name
    if city:
        query = f"{name} {city}"
    data = _apollo_req("GET", "/accounts/search", params={
        "q_keywords": query,
        "page": 1,
        "per_page": 3,
    })
    accounts = data.get("accounts", [])
    if accounts:
        return accounts[0]
    return None


def apollo_get_list_id(list_name: str) -> str | None:
    """Find Apollo list ID by name."""
    data = _apollo_req("GET", "/email_accounts", params={"per_page": 1})  # just to test auth
    # Fetch label lists
    data = _apollo_req("GET", "/labels", params={"per_page": 100})
    for label in data.get("labels", []):
        if label.get("name") == list_name:
            return label.get("id")
    return None


def apollo_add_to_list(contact_id: str, list_id: str) -> bool:
    """Add a contact to an Apollo label/list."""
    if not contact_id or not list_id:
        return False
    data = _apollo_req("POST", f"/contacts/{contact_id}/update", json={
        "label_ids": [list_id],
    })
    return bool(data)


# ───────────────────────────────────────────────
# Match & confidence scoring
# ───────────────────────────────────────────────

def compute_match_confidence(rec: dict, contact: dict | None, account: dict | None) -> str:
    """Score match confidence: High / Medium / Low."""
    score = 0
    if contact:
        score += 50   # contact found
        if contact.get("email") and rec.get("email") and \
           contact["email"].lower() == rec["email"].lower():
            score += 30  # email exact match
    if account:
        score += 20
    if score >= 80:
        return "High"
    if score >= 50:
        return "Medium"
    return "Low"


# ───────────────────────────────────────────────
# Notion property builders (minimal)
# ───────────────────────────────────────────────

def _text(val: str) -> dict:
    return {"rich_text": [{"text": {"content": val[:2000] if val else ""}}]}

def _checkbox(val: bool) -> dict:
    return {"checkbox": bool(val)}

def _select(val: str) -> dict:
    if not val:
        return {"select": None}
    return {"select": {"name": val}}


# ───────────────────────────────────────────────
# Main
# ───────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--unmatched-only", action="store_true", help="Only process unmatched records")
    args = parser.parse_args()

    log.info("📂  Loading Notion records...")
    filter_payload = None
    if args.unmatched_only:
        filter_payload = {
            "property": F_APOLLO_MATCHED,
            "checkbox": {"equals": False}
        }
    pages = notion_query_all(NOTION_DB_ID, filter_payload)
    log.info(f"   → {len(pages)} pages loaded")

    if args.limit:
        pages = pages[:args.limit]
        log.info(f"   → Limited to {args.limit}")

    # Pre-fetch Apollo list ID
    apollo_list_id = None
    try:
        apollo_list_id = apollo_get_list_id(APOLLO_LIST_NAME)
        if apollo_list_id:
            log.info(f"✅  Apollo list '{APOLLO_LIST_NAME}' → ID: {apollo_list_id}")
        else:
            log.warning(f"⚠️  Apollo list '{APOLLO_LIST_NAME}' not found — will skip list enrollment")
    except Exception as e:
        log.warning(f"⚠️  Could not fetch Apollo list: {e}")

    stats = {"matched": 0, "no_match": 0, "added_to_list": 0, "errors": 0}

    for i, page in enumerate(pages, 1):
        pid = page["id"]
        props = page.get("properties", {})

        name   = _get_title(props, F_NAME)
        email  = _get_email(props, F_EMAIL)
        mobile = _get_phone(props, F_MOBILE)
        city   = _get_text(props, F_CITY)

        log.info(f"[{i}/{len(pages)}] {name}")

        try:
            contact = None
            account = None

            # Strategy 1: Search by email (highest confidence)
            if email:
                contact = apollo_search_contact_by_email(email)
                if contact:
                    log.info(f"   → Matched by email: {contact.get('id', '')[:8]}…")

            # Strategy 2: Search by phone
            if not contact and mobile:
                contact = apollo_search_contact_by_phone(mobile)
                if contact:
                    log.info(f"   → Matched by phone: {contact.get('id', '')[:8]}…")

            # Strategy 3: Search account by domain (from email)
            if not account and email:
                domain = extract_email_domain(email)
                account = apollo_search_account_by_domain(domain)
                if account:
                    log.info(f"   → Account matched by domain: {account.get('id', '')[:8]}…")

            # Strategy 4: Account by name
            if not account and name:
                account = apollo_search_account_by_name(name, city)
                if account:
                    log.info(f"   → Account matched by name: {account.get('id', '')[:8]}…")

            # Compute match confidence
            matched = bool(contact or account)
            confidence = compute_match_confidence(
                {"email": email},
                contact,
                account,
            ) if matched else ""

            # Build update
            update_props = {
                F_APOLLO_MATCHED:  _checkbox(matched),
                F_MATCH_CONF:      _select(confidence),
                F_APOLLO_ACC_ID:   _text(account.get("id", "") if account else ""),
                F_APOLLO_CON_ID:   _text(contact.get("id", "") if contact else ""),
            }

            # Add to Apollo list if matched and not already there
            in_list = _get_checkbox(props, F_IN_LIST)
            if contact and apollo_list_id and not in_list:
                if not args.dry_run:
                    added = apollo_add_to_list(contact["id"], apollo_list_id)
                    if added:
                        update_props[F_IN_LIST] = _checkbox(True)
                        stats["added_to_list"] += 1
                        log.info(f"   → Added to Apollo list ✓")
                else:
                    stats["added_to_list"] += 1

            if not args.dry_run:
                update_page(pid, update_props)

            if matched:
                stats["matched"] += 1
                log.info(f"   → Matched (confidence: {confidence})")
            else:
                stats["no_match"] += 1
                log.info(f"   → No match found")

            # Small delay to avoid Apollo rate limits
            time.sleep(0.3)

        except Exception as e:
            log.error(f"   → ERROR: {e}")
            stats["errors"] += 1

    # ── Summary ──────────────────────────────────
    print("\n" + "═"*55)
    print("   APOLLO MATCH COMPLETE")
    print("═"*55)
    print(f"  Total processed:  {len(pages)}")
    print(f"  Matched:          {stats['matched']}")
    print(f"  No match:         {stats['no_match']}")
    print(f"  Added to list:    {stats['added_to_list']}")
    print(f"  Errors:           {stats['errors']}")
    match_rate = stats['matched'] / len(pages) * 100 if pages else 0
    print(f"  Match rate:       {match_rate:.1f}%")
    if args.dry_run:
        print("\n  ⚠️  DRY RUN — no changes written")
    print("═"*55 + "\n")


if __name__ == "__main__":
    main()
