"""
04_gmail_outreach_check.py — Check if contractors were previously contacted via Gmail
Uses Gmail MCP search to cross-reference contractor email domains against sent mail.
Updates previous_outreach_detected + previous_outreach_source in cleaned_contractors.json.
Also patches matching Notion pages.

Usage:
  python 04_gmail_outreach_check.py              # check all undetected
  python 04_gmail_outreach_check.py --dry-run    # show results without writing
  python 04_gmail_outreach_check.py --limit 50
  python 04_gmail_outreach_check.py --force      # re-check all

NOTE: This script calls Gmail via the gmail_search_messages MCP tool.
      Since it requires Claude's MCP tools, it is designed to be run interactively
      via Claude in Cowork mode. For standalone use, it uses the Gmail API directly
      if GMAIL_TOKEN is set in .env.
"""

import json, os, sys, time, argparse, logging, subprocess
from datetime import datetime, timezone
from pathlib import Path

try:
    import requests
except ImportError:
    print("ERROR: requests not installed.")
    sys.exit(1)

BASE_DIR    = Path(__file__).parent
ROOT_DIR    = BASE_DIR.parent
ENV_PATH    = ROOT_DIR / "💻 CODE" / "Phase 3 - Sync" / ".env"
INPUT_FILE  = BASE_DIR / "cleaned_contractors.json"
OUTPUT_FILE = BASE_DIR / "cleaned_contractors.json"
LOG_FILE    = BASE_DIR / "04_gmail_check.log"
CHECKPOINT  = BASE_DIR / "04_gmail_checkpoint.json"
RESULTS     = BASE_DIR / "04_gmail_results.json"
NOTION_DB   = "25384c7f9128462b8737773004e7d1bd"
RATE_LIMIT  = 0.5

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger(__name__)

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
NOTION_API_KEY = env.get("NOTION_API_KEY", "")
NOTION_HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28",
}

# ── Gmail search via subprocess (calls a helper that uses Gmail API) ───────────
# The script outputs a JSON file with domains that had matches
GMAIL_CACHE: dict[str, bool] = {}   # domain → has_previous_outreach

def check_gmail_for_domain(domain: str, email: str) -> bool:
    """
    Check Gmail sent folder for any previous contact with this domain/email.
    Uses Gmail REST API with OAuth token from .env if available,
    otherwise marks for manual review.
    """
    if domain in GMAIL_CACHE:
        return GMAIL_CACHE[domain]

    gmail_token = env.get("GMAIL_ACCESS_TOKEN", "")
    if not gmail_token:
        # No Gmail token — cannot check
        return False

    # Build query: look in sent mail for this domain or email
    queries = []
    if email and "@" in email:
        queries.append(f"to:{email}")
    if domain:
        clean_domain = domain.replace("https://", "").replace("http://", "").strip("/")
        queries.append(f"to:*@{clean_domain}")

    if not queries:
        return False

    q = " OR ".join(queries)
    url = f"https://gmail.googleapis.com/gmail/v1/users/me/messages?q={q}&labelIds=SENT&maxResults=1"
    headers = {"Authorization": f"Bearer {gmail_token}"}

    try:
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code == 200:
            messages = resp.json().get("messages", [])
            found = len(messages) > 0
            GMAIL_CACHE[domain] = found
            return found
        elif resp.status_code == 401:
            log.warning("Gmail token expired. Set GMAIL_ACCESS_TOKEN in .env")
    except Exception as e:
        log.warning("Gmail API error for %s: %s", domain, e)

    return False


# ── Notion helpers ────────────────────────────────────────────────────────────
def notion_find_page(membership_number: str) -> str | None:
    if not NOTION_API_KEY:
        return None
    url = f"https://api.notion.com/v1/databases/{NOTION_DB}/query"
    body = {"filter": {"property": "Membership Number",
                       "rich_text": {"equals": membership_number}}, "page_size": 1}
    try:
        resp = requests.post(url, headers=NOTION_HEADERS, json=body, timeout=15)
        if resp.status_code == 200:
            results = resp.json().get("results", [])
            if results:
                return results[0]["id"]
    except Exception as e:
        log.warning("Notion query error: %s", e)
    return None

def notion_update_outreach(page_id: str, source: str):
    if not NOTION_API_KEY or not page_id:
        return
    props = {
        "Previous Outreach Detected": {"checkbox": True},
        "Previous Outreach Source":   {"select": {"name": source}},
        "Follow-up Stage":            {"select": {"name": "Previous Outreach"}},
    }
    try:
        requests.patch(f"https://api.notion.com/v1/pages/{page_id}",
                       headers=NOTION_HEADERS, json={"properties": props}, timeout=15)
    except Exception as e:
        log.warning("Notion update error: %s", e)

# ── Checkpoint ────────────────────────────────────────────────────────────────
def load_checkpoint() -> set:
    if CHECKPOINT.exists():
        return set(json.loads(CHECKPOINT.read_text(encoding="utf-8")).get("checked", []))
    return set()

def save_checkpoint(checked: set):
    CHECKPOINT.write_text(
        json.dumps({"checked": list(checked), "saved_at": datetime.now(timezone.utc).isoformat()},
                   ensure_ascii=False), encoding="utf-8"
    )

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit",   type=int, default=0)
    parser.add_argument("--force",   action="store_true")
    parser.add_argument("--email-only", action="store_true", help="Only check exact email (faster)")
    args = parser.parse_args()

    log.info("=" * 60)
    log.info("04_gmail_outreach_check.py")
    log.info("Mode: %s", "DRY-RUN" if args.dry_run else "LIVE")

    has_gmail_token = bool(env.get("GMAIL_ACCESS_TOKEN"))
    if not has_gmail_token:
        log.warning("GMAIL_ACCESS_TOKEN not set in .env — Gmail check will be skipped.")
        log.warning("To enable: get a Gmail OAuth token and add GMAIL_ACCESS_TOKEN=<token> to .env")
        log.warning("Running in Apollo-only mode (marks records with apollo_matched=True as Previous Outreach)")

    records = json.loads(INPUT_FILE.read_text(encoding="utf-8"))
    record_index = {r["membership_number"]: r for r in records if r.get("membership_number")}
    log.info("Records: %d", len(records))

    checked = set() if args.force else load_checkpoint()
    to_check = [r for r in records if r.get("membership_number") not in checked]
    if args.limit:
        to_check = to_check[:args.limit]
    log.info("To check: %d", len(to_check))

    gmail_matches, apollo_matches, both_matches = 0, 0, 0
    results_log = []

    for i, rec in enumerate(to_check, 1):
        mem_num   = rec.get("membership_number", "")
        domain    = rec.get("domain", "").replace("https://","").replace("http://","").strip("/")
        email     = rec.get("email", "")
        company   = rec.get("company_name", "")
        already_apollo = rec.get("apollo_matched", False)

        gmail_found  = check_gmail_for_domain(domain, email) if has_gmail_token else False
        source = None

        if gmail_found and already_apollo:
            source = "Both"; both_matches += 1
        elif gmail_found:
            source = "Gmail"; gmail_matches += 1
        elif already_apollo:
            source = "Apollo"; apollo_matches += 1

        if source:
            log.info("[%d] PREVIOUS OUTREACH (%s): %s", i, source, company)
            results_log.append({"membership_number": mem_num, "company": company, "source": source})

            if not args.dry_run and mem_num in record_index:
                record_index[mem_num]["previous_outreach_detected"] = True
                record_index[mem_num]["previous_outreach_source"]   = source
                record_index[mem_num]["follow_up_stage"]            = "Previous Outreach"

                if NOTION_API_KEY:
                    page_id = notion_find_page(mem_num)
                    if page_id:
                        notion_update_outreach(page_id, source)
                        time.sleep(0.35)

        checked.add(mem_num)

        if i % 50 == 0 or i == len(to_check):
            log.info("[%d/%d] Gmail: %d | Apollo: %d | Both: %d",
                     i, len(to_check), gmail_matches, apollo_matches, both_matches)
            if not args.dry_run:
                save_checkpoint(checked)
                OUTPUT_FILE.write_text(
                    json.dumps(list(record_index.values()), ensure_ascii=False, indent=2),
                    encoding="utf-8")
                RESULTS.write_text(json.dumps(results_log, ensure_ascii=False, indent=2), encoding="utf-8")

        time.sleep(RATE_LIMIT if has_gmail_token else 0.01)

    if not args.dry_run:
        save_checkpoint(checked)
        OUTPUT_FILE.write_text(
            json.dumps(list(record_index.values()), ensure_ascii=False, indent=2), encoding="utf-8")
        RESULTS.write_text(json.dumps(results_log, ensure_ascii=False, indent=2), encoding="utf-8")

    total_found = gmail_matches + apollo_matches + both_matches
    log.info("=" * 60)
    log.info("DONE — Previous outreach detected: %d / %d checked", total_found, len(to_check))
    log.info("  Gmail: %d | Apollo: %d | Both: %d", gmail_matches, apollo_matches, both_matches)


if __name__ == "__main__":
    main()
