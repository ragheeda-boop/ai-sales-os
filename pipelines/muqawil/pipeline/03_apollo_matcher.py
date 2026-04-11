"""
03_apollo_matcher.py — Match muqawil contractors against Apollo CRM
Checks if each contractor's domain or email already exists in Apollo.
Updates cleaned_contractors.json with apollo_matched / apollo_account_id / apollo_contact_id.
Also updates Notion if records are already synced.

Usage:
  python 03_apollo_matcher.py              # match all unmatched
  python 03_apollo_matcher.py --dry-run    # show matches without writing
  python 03_apollo_matcher.py --limit 50   # limit to first N records
  python 03_apollo_matcher.py --force      # re-check already-matched records too
"""

import json, os, sys, time, argparse, logging, re
from datetime import datetime, timezone
from pathlib import Path

try:
    import requests
except ImportError:
    print("ERROR: requests not installed. Run: pip install requests")
    sys.exit(1)

# ── Config ────────────────────────────────────────────────────────────────────
BASE_DIR    = Path(__file__).parent
ROOT_DIR    = BASE_DIR.parent
ENV_PATH    = ROOT_DIR / "💻 CODE" / "Phase 3 - Sync" / ".env"
INPUT_FILE  = BASE_DIR / "cleaned_contractors.json"
OUTPUT_FILE = BASE_DIR / "cleaned_contractors.json"          # update in-place
BACKUP_FILE = BASE_DIR / "cleaned_contractors_pre_apollo.json"
LOG_FILE    = BASE_DIR / "03_apollo_matcher.log"
CHECKPOINT  = BASE_DIR / "03_apollo_checkpoint.json"
NOTION_DB   = "25384c7f9128462b8737773004e7d1bd"
RATE_LIMIT  = 0.5    # seconds between Apollo requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger(__name__)


# ── Load .env ─────────────────────────────────────────────────────────────────
def load_env(path: Path) -> dict:
    env = {}
    if not path.exists():
        return env
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            env[k.strip()] = v.strip().strip('"').strip("'")
    return env

env = load_env(ENV_PATH)
APOLLO_API_KEY = env.get("APOLLO_API_KEY") or os.environ.get("APOLLO_API_KEY", "")
NOTION_API_KEY = env.get("NOTION_API_KEY") or os.environ.get("NOTION_API_KEY", "")

if not APOLLO_API_KEY:
    log.error("APOLLO_API_KEY not found in .env at: %s", ENV_PATH)
    sys.exit(1)

APOLLO_HEADERS = {"Content-Type": "application/json", "Cache-Control": "no-cache"}
NOTION_HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28",
}

# ── Apollo search helpers ──────────────────────────────────────────────────────
def apollo_search_company(domain: str) -> dict | None:
    """Search Apollo accounts by domain. Returns first match or None."""
    if not domain:
        return None
    # strip http/https/www
    domain = re.sub(r"^https?://(www\.)?", "", domain).rstrip("/").lower()
    url = "https://api.apollo.io/api/v1/accounts/search"
    payload = {
        "api_key": APOLLO_API_KEY,
        "q_organization_domains": [domain],
        "page": 1,
        "per_page": 1,
    }
    try:
        resp = requests.post(url, json=payload, timeout=20)
        if resp.status_code == 200:
            data = resp.json()
            accounts = data.get("accounts", [])
            if accounts:
                return accounts[0]
        elif resp.status_code == 429:
            log.warning("Apollo rate limit — sleeping 5s")
            time.sleep(5)
    except Exception as e:
        log.warning("Apollo account search error: %s", e)
    return None

def apollo_search_person(email: str) -> dict | None:
    """Search Apollo contacts by email. Returns first match or None."""
    if not email or "@" not in email:
        return None
    url = "https://api.apollo.io/api/v1/contacts/search"
    payload = {
        "api_key": APOLLO_API_KEY,
        "q_email": email,
        "page": 1,
        "per_page": 1,
    }
    try:
        resp = requests.post(url, json=payload, timeout=20)
        if resp.status_code == 200:
            data = resp.json()
            contacts = data.get("contacts", [])
            if contacts:
                return contacts[0]
        elif resp.status_code == 429:
            log.warning("Apollo rate limit — sleeping 5s")
            time.sleep(5)
    except Exception as e:
        log.warning("Apollo contact search error: %s", e)
    return None


# ── Notion update helper ───────────────────────────────────────────────────────
def notion_find_page(membership_number: str) -> str | None:
    """Find Notion page by Membership Number. Returns page_id or None."""
    if not NOTION_API_KEY:
        return None
    url = f"https://api.notion.com/v1/databases/{NOTION_DB}/query"
    body = {
        "filter": {
            "property": "Membership Number",
            "rich_text": {"equals": membership_number}
        },
        "page_size": 1,
    }
    try:
        resp = requests.post(url, headers=NOTION_HEADERS, json=body, timeout=15)
        if resp.status_code == 200:
            results = resp.json().get("results", [])
            if results:
                return results[0]["id"]
    except Exception as e:
        log.warning("Notion query error: %s", e)
    return None

def notion_update_match(page_id: str, apollo_account_id: str, apollo_contact_id: str):
    """Write Apollo match data back to Notion page."""
    if not NOTION_API_KEY or not page_id:
        return
    url = f"https://api.notion.com/v1/pages/{page_id}"
    props = {
        "Apollo Matched": {"checkbox": True},
        "Apollo Account ID": {"rich_text": [{"text": {"content": apollo_account_id or ""}}]},
    }
    if apollo_contact_id:
        props["Apollo Contact ID"] = {"rich_text": [{"text": {"content": apollo_contact_id}}]}
    try:
        requests.patch(url, headers=NOTION_HEADERS, json={"properties": props}, timeout=15)
    except Exception as e:
        log.warning("Notion update error for %s: %s", page_id, e)


# ── Checkpoint ────────────────────────────────────────────────────────────────
def load_checkpoint() -> set:
    if CHECKPOINT.exists():
        return set(json.loads(CHECKPOINT.read_text(encoding="utf-8")).get("checked", []))
    return set()

def save_checkpoint(checked: set):
    CHECKPOINT.write_text(
        json.dumps({"checked": list(checked), "count": len(checked),
                    "saved_at": datetime.now(timezone.utc).isoformat()}, ensure_ascii=False),
        encoding="utf-8"
    )

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit",   type=int, default=0)
    parser.add_argument("--force",   action="store_true", help="Re-check already-matched records")
    args = parser.parse_args()

    log.info("=" * 60)
    log.info("03_apollo_matcher.py — Apollo Matching")
    log.info("Mode: %s", "DRY-RUN" if args.dry_run else "LIVE")

    records = json.loads(INPUT_FILE.read_text(encoding="utf-8"))
    log.info("Records loaded: %d", len(records))

    checked = set() if args.force else load_checkpoint()
    log.info("Already checked: %d", len(checked))

    # Backup before modifying
    if not args.dry_run and not BACKUP_FILE.exists():
        BACKUP_FILE.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
        log.info("Backup saved: %s", BACKUP_FILE.name)

    to_check = [r for r in records if r.get("membership_number") not in checked]
    if args.limit:
        to_check = to_check[:args.limit]
    log.info("Records to check: %d", len(to_check))

    matched, not_matched = 0, 0
    record_index = {r["membership_number"]: r for r in records if r.get("membership_number")}

    for i, rec in enumerate(to_check, 1):
        mem_num  = rec.get("membership_number", "")
        domain   = rec.get("domain", "")
        email    = rec.get("email", "")
        company  = rec.get("company_name", "")

        apollo_account_id = ""
        apollo_contact_id = ""

        # Step 1: search by domain (company level)
        if domain:
            account = apollo_search_company(domain)
            if account:
                apollo_account_id = account.get("id", "")
                log.info("[%d] MATCH (domain) %-40s → Apollo ID: %s", i, company[:40], apollo_account_id)

        # Step 2: if no domain match, search by email (contact level)
        if not apollo_account_id and email:
            contact = apollo_search_person(email)
            if contact:
                apollo_contact_id = contact.get("id", "")
                apollo_account_id = contact.get("account_id", "")
                log.info("[%d] MATCH (email)  %-40s → Contact ID: %s", i, company[:40], apollo_contact_id)

        apollo_matched = bool(apollo_account_id or apollo_contact_id)
        if apollo_matched:
            matched += 1
        else:
            not_matched += 1

        # Update in-memory record
        if not args.dry_run and mem_num in record_index:
            record_index[mem_num]["apollo_matched"]    = apollo_matched
            record_index[mem_num]["apollo_account_id"] = apollo_account_id
            record_index[mem_num]["apollo_contact_id"] = apollo_contact_id

            # Update Notion if DB is accessible
            if apollo_matched and NOTION_API_KEY:
                page_id = notion_find_page(mem_num)
                if page_id:
                    notion_update_match(page_id, apollo_account_id, apollo_contact_id)
                    time.sleep(0.35)

        checked.add(mem_num)

        if i % 50 == 0 or i == len(to_check):
            log.info("[%d/%d] Matched: %d | Not matched: %d", i, len(to_check), matched, not_matched)
            if not args.dry_run:
                save_checkpoint(checked)
                OUTPUT_FILE.write_text(
                    json.dumps(list(record_index.values()), ensure_ascii=False, indent=2),
                    encoding="utf-8"
                )

        time.sleep(RATE_LIMIT)

    if not args.dry_run:
        save_checkpoint(checked)
        OUTPUT_FILE.write_text(
            json.dumps(list(record_index.values()), ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

    log.info("=" * 60)
    log.info("DONE — Matched: %d / Not matched: %d / Total checked: %d",
             matched, not_matched, len(to_check))


if __name__ == "__main__":
    main()
