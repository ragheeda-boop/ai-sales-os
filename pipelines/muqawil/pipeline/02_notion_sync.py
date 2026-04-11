"""
02_notion_sync.py — Bulk push muqawil contractors to Notion DB
DB: 🏗️ مقاولين - هيئة المقاولين (ID: 25384c7f9128462b8737773004e7d1bd)
Owner: ragheed (29dd872b-594c-810b-8b67-00029d209fc0)

Usage:
  python 02_notion_sync.py              # full push (resumes from checkpoint)
  python 02_notion_sync.py --dry-run    # preview first 5 records, no writes
  python 02_notion_sync.py --limit 50   # push first N records only
  python 02_notion_sync.py --reset      # clear checkpoint and restart from scratch
"""

import json, os, sys, time, argparse, logging
from datetime import datetime, timezone
from pathlib import Path

try:
    import requests
except ImportError:
    print("ERROR: requests not installed. Run: pip install requests")
    sys.exit(1)

# ── Config ────────────────────────────────────────────────────────────────────
BASE_DIR      = Path(__file__).parent
ROOT_DIR      = BASE_DIR.parent
ENV_PATH      = ROOT_DIR / "💻 CODE" / "Phase 3 - Sync" / ".env"
INPUT_FILE    = BASE_DIR / "cleaned_contractors.json"
CHECKPOINT    = BASE_DIR / "02_notion_sync_checkpoint.json"
LOG_FILE      = BASE_DIR / "02_notion_sync.log"

NOTION_DB_ID  = "25384c7f9128462b8737773004e7d1bd"
OWNER_ID      = "29dd872b-594c-810b-8b67-00029d209fc0"   # ragheed
RATE_LIMIT    = 0.34   # seconds between requests (~3 req/s)
BATCH_SAVE    = 100    # save checkpoint every N records
MAX_RETRIES   = 5

# ── Logging ───────────────────────────────────────────────────────────────────
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
NOTION_API_KEY = env.get("NOTION_API_KEY") or os.environ.get("NOTION_API_KEY", "")
if not NOTION_API_KEY:
    log.error("NOTION_API_KEY not found. Check .env at: %s", ENV_PATH)
    sys.exit(1)

HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28",
}

# ── Helper: rich_text property ────────────────────────────────────────────────
def rt(text: str) -> dict:
    return {"rich_text": [{"text": {"content": str(text)[:2000]}}]} if text else {"rich_text": []}

# ── Field mapping ─────────────────────────────────────────────────────────────
VALID_REGIONS = {"الرياض","مكة المكرمة","المنطقة الشرقية","القصيم","المدينة المنورة",
                 "عسير","نجران","حائل","جازان","تبوك","الجوف","الباحة","الحدود الشمالية","أخرى"}
VALID_GRADES  = {"غير مصنف","مصنف درجة أولى","مصنف درجة ثانية","مصنف درجة ثالثة",
                 "مصنف درجة رابعة","مصنف درجة خامسة","مصنف درجة سادسة"}
VALID_SIZES   = {"منشأة متناهية الصغر","منشأة صغيرة","منشأة متوسطة","منشأة كبيرة"}
VALID_BADGES  = {"عضوية بلاتينية","عضوية ذهبية","عضوية فضية"}
VALID_STAGES  = {"Ready for Initial Outreach","In Sequence","Opened Not Replied","Replied",
                 "Meeting Scheduled","No Valid Email","Needs Manual Review","Previous Outreach"}
VALID_ACTIONS = {"Enroll in Sequence","Follow-up","Human Follow-up Required",
                 "Book Meeting","Find Contact / Enrich","No Action"}
BADGE_TO_TIER = {"عضوية بلاتينية":"Premium Membership","عضوية ذهبية":"Standard","عضوية فضية":"Basic"}


def build_properties(rec: dict) -> dict:
    p = {}

    # Title
    name = (rec.get("company_name") or "").strip()
    p["اسم الشركة"] = {"title": [{"text": {"content": name[:2000]}}]}

    # Rich text fields
    for notion_key, data_key in [
        ("Membership Number",  "membership_number"),
        ("Normalized Name",    "normalized_name"),
        ("Source Row ID",      "contractor_id"),
        ("City",               "city"),
        ("Address",            "address"),
        ("Training Hours",     "training_hours"),
        ("Import Batch",       "import_batch"),
        ("Apollo Account ID",  "apollo_account_id"),
        ("Apollo Contact ID",  "apollo_contact_id"),
    ]:
        val = str(rec.get(data_key) or "").strip()
        p[notion_key] = rt(val)

    # Email
    email = (rec.get("email") or "").strip()
    if email and "@" in email:
        p["Main Email"] = {"email": email}

    # Phone
    phone = (rec.get("phone") or "").strip()
    if phone:
        p["Mobile"] = {"phone_number": phone}

    # URLs
    domain = (rec.get("domain") or "").strip()
    if domain:
        if not domain.startswith("http"):
            domain = "https://" + domain
        p["Domain"] = {"url": domain}

    src_url = (rec.get("source_url") or "").strip()
    if src_url:
        p["Source URL"] = {"url": src_url}

    # Numbers
    try:
        stars = rec.get("rating_stars")
        if stars not in (None, ""):
            p["Rating Stars"] = {"number": float(stars)}
    except (ValueError, TypeError):
        pass

    score = rec.get("data_completeness_score")
    if score is not None:
        p["Data Completeness Score"] = {"number": float(score)}

    # Selects — only write if value is a valid option
    region = (rec.get("region") or "").strip()
    p["Region"] = {"select": {"name": region}} if region in VALID_REGIONS else {"select": {"name": "أخرى"}}

    grade = (rec.get("classification_grade") or "").strip()
    if grade in VALID_GRADES:
        p["Classification Grade"] = {"select": {"name": grade}}

    size = (rec.get("establishment_size") or "").strip()
    if size in VALID_SIZES:
        p["Establishment Size"] = {"select": {"name": size}}

    badge = (rec.get("membership_badge") or "").strip()
    if badge in VALID_BADGES:
        p["Membership Badge"] = {"select": {"name": badge}}
        p["Account Tier"]     = {"select": {"name": BADGE_TO_TIER[badge]}}

    ctype = (rec.get("contractor_type") or "").strip()
    if ctype in {"مقاول سعودي","مقاول غير سعودي","مهتم - منشأة"}:
        p["Contractor Type"] = {"select": {"name": ctype}}

    stage = (rec.get("follow_up_stage") or "").strip()
    if stage in VALID_STAGES:
        p["Follow-up Stage"] = {"select": {"name": stage}}

    action = (rec.get("next_action") or "").strip()
    if action in VALID_ACTIONS:
        p["Next Action"] = {"select": {"name": action}}

    p["Company Status"]  = {"select": {"name": "New"}}
    p["Sequence Status"] = {"select": {"name": "Not Enrolled"}}

    return p


def build_properties_cont(rec: dict, p: dict) -> dict:
    """Continue building properties — checkboxes, dates, owner."""

    # Checkboxes
    for notion_key, data_key, invert in [
        ("Ready for Outreach",       "ready_for_outreach",       False),
        ("Apollo Matched",           "apollo_matched",           False),
        ("In Apollo List",           "in_apollo_list",           False),
        ("In Sequence",              "in_sequence",              False),
        ("Duplicate Suspected",      "duplicate_suspected",      False),
        ("Needs Manual Review",      "needs_manual_review",      False),
        ("Previous Outreach Detected","previous_outreach_detected",False),
        ("Missing Email",            "has_email",                True),
        ("Missing Mobile",           "has_phone",                True),
        ("Sequence Enrollment Ready","ready_for_outreach",       False),
    ]:
        val = bool(rec.get(data_key, False))
        p[notion_key] = {"checkbox": (not val) if invert else val}

    # Dates
    member_since = (rec.get("member_since") or "").strip()
    if member_since:
        try:
            p["Member Since"] = {"date": {"start": member_since.replace("/", "-")[:10]}}
        except Exception:
            pass

    scraped_at = (rec.get("scraped_at") or "").strip()
    if scraped_at:
        p["Last Synced At"] = {"date": {"start": scraped_at[:10]}}

    # Owner
    p["Owner"] = {"people": [{"id": OWNER_ID}]}

    return p


def make_page_body(rec: dict) -> dict:
    props = build_properties(rec)
    props = build_properties_cont(rec, props)
    return {
        "parent": {"database_id": NOTION_DB_ID},
        "properties": props,
    }


# ── Notion API call with retry ────────────────────────────────────────────────
def create_page(body: dict) -> dict | None:
    url = "https://api.notion.com/v1/pages"
    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.post(url, headers=HEADERS, json=body, timeout=30)
            if resp.status_code == 200:
                return resp.json()
            elif resp.status_code == 429:
                wait = float(resp.headers.get("Retry-After", 2 ** attempt))
                log.warning("Rate limited — sleeping %.1fs", wait)
                time.sleep(wait)
            elif resp.status_code in (500, 502, 503):
                wait = 2 ** attempt
                log.warning("Server error %s — retry %d in %.1fs", resp.status_code, attempt+1, wait)
                time.sleep(wait)
            else:
                log.error("Notion API error %s: %s", resp.status_code, resp.text[:300])
                return None
        except requests.exceptions.RequestException as e:
            log.warning("Request exception: %s — retry %d", e, attempt+1)
            time.sleep(2 ** attempt)
    log.error("All retries exhausted for record")
    return None


# ── Checkpoint helpers ────────────────────────────────────────────────────────
def load_checkpoint() -> set:
    if CHECKPOINT.exists():
        data = json.loads(CHECKPOINT.read_text(encoding="utf-8"))
        return set(data.get("done", []))
    return set()

def save_checkpoint(done: set):
    CHECKPOINT.write_text(
        json.dumps({"done": list(done), "count": len(done),
                    "saved_at": datetime.now(timezone.utc).isoformat()}, ensure_ascii=False),
        encoding="utf-8"
    )


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run",  action="store_true", help="Preview 5 records, no writes")
    parser.add_argument("--limit",    type=int,  default=0,  help="Push only first N records")
    parser.add_argument("--reset",    action="store_true", help="Clear checkpoint and restart")
    parser.add_argument("--start-from", type=int, default=0, help="Skip first N records (0-based index)")
    args = parser.parse_args()

    log.info("=" * 60)
    log.info("02_notion_sync.py — Muqawil → Notion Sync")
    log.info("DB: %s", NOTION_DB_ID)
    log.info("Mode: %s", "DRY-RUN" if args.dry_run else "LIVE")
    log.info("=" * 60)

    # Load records
    if not INPUT_FILE.exists():
        log.error("Input file not found: %s", INPUT_FILE)
        sys.exit(1)

    with open(INPUT_FILE, encoding="utf-8") as f:
        records = json.load(f)
    log.info("Loaded %d records from %s", len(records), INPUT_FILE.name)

    # Checkpoint
    if args.reset and CHECKPOINT.exists():
        CHECKPOINT.unlink()
        log.info("Checkpoint cleared — starting fresh")
    done = set() if args.dry_run else load_checkpoint()
    log.info("Already synced: %d records", len(done))

    # Dry-run: preview and exit
    if args.dry_run:
        log.info("--- DRY RUN: first 5 records ---")
        for rec in records[:5]:
            body = make_page_body(rec)
            log.info("WOULD CREATE: %s | %s | %s",
                     rec.get("company_name"), rec.get("membership_number"), rec.get("follow_up_stage"))
            keys = list(body["properties"].keys())
            log.info("  Properties (%d): %s", len(keys), keys)
        log.info("Dry-run complete. No records written.")
        return

    # Determine records to process
    to_process = [r for r in records if r.get("membership_number") not in done]
    if args.start_from:
        to_process = to_process[args.start_from:]
    if args.limit:
        to_process = to_process[:args.limit]
    total = len(to_process)
    log.info("Records to push: %d", total)

    # Push
    success, failed, skipped = 0, 0, 0
    t0 = time.time()

    for i, rec in enumerate(to_process, 1):
        mem_num = rec.get("membership_number", f"idx_{i}")

        body = make_page_body(rec)
        result = create_page(body)

        if result:
            done.add(mem_num)
            success += 1
        else:
            failed += 1
            log.error("FAILED [%d/%d]: %s — %s", i, total, mem_num, rec.get("company_name"))

        # Rate limit
        time.sleep(RATE_LIMIT)

        # Progress
        if i % 50 == 0 or i == total:
            elapsed = time.time() - t0
            rate = i / elapsed if elapsed > 0 else 0
            eta_s = (total - i) / rate if rate > 0 else 0
            eta_m = int(eta_s / 60)
            log.info("[%d/%d] ✓%d ✗%d | %.1f rec/s | ETA ~%dm",
                     i, total, success, failed, rate, eta_m)

        # Checkpoint save
        if i % BATCH_SAVE == 0:
            save_checkpoint(done)

    # Final checkpoint
    save_checkpoint(done)

    elapsed = time.time() - t0
    log.info("=" * 60)
    log.info("DONE in %.0fs", elapsed)
    log.info("  Pushed:  %d", success)
    log.info("  Failed:  %d", failed)
    log.info("  Total synced ever: %d", len(done))
    log.info("Checkpoint: %s", CHECKPOINT)
    log.info("=" * 60)

    if failed:
        log.warning("%d records failed — rerun to retry (checkpoint will skip successes)", failed)


if __name__ == "__main__":
    main()
