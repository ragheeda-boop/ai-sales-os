"""
05_rules_engine.py — Rules engine for muqawil contractor pipeline
Applies priority/status/stage rules based on signals from Apollo, Gmail, and scraped data.
Updates cleaned_contractors.json and patches Notion pages.

Rules applied:
  R1  Previous Outreach detected               → Follow-up Stage = "Previous Outreach"
  R2  has_email=False                          → Follow-up Stage = "No Valid Email", Next Action = "Find Contact / Enrich"
  R3  duplicate_suspected=True                 → Needs Manual Review = True, Next Action = "Human Follow-up Required"
  R4  needs_manual_review=True                 → Follow-up Stage = "Needs Manual Review"
  R5  apollo_matched=True + in_sequence=False  → Follow-up Stage = "Ready for Initial Outreach" (already in Apollo = priority)
  R6  in_sequence=True                         → Follow-up Stage = "In Sequence"
  R7  Default (has email, no flags)            → Follow-up Stage = "Ready for Initial Outreach"

Priority rules (written to Notion Priority field):
  P1  Classification Grade = درجة أولى/ثانية + email present + Riyadh/EasternProv/Makkah
  P2  Classification Grade = درجة ثالثة/رابعة + email present
  P3  Everything else with email
  P4  No email / duplicate / manual review

Usage:
  python 05_rules_engine.py              # apply all rules
  python 05_rules_engine.py --dry-run    # show what would change
  python 05_rules_engine.py --limit 100
"""

import json, os, sys, time, argparse, logging
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
LOG_FILE    = BASE_DIR / "05_rules_engine.log"
NOTION_DB   = "25384c7f9128462b8737773004e7d1bd"
RATE_LIMIT  = 0.35

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

# ── Priority regions (Tier 1 markets for MUHIDE) ───────────────────────────────
TIER1_REGIONS = {"الرياض", "المنطقة الشرقية", "مكة المكرمة"}
HIGH_GRADES   = {"مصنف درجة أولى", "مصنف درجة ثانية"}
MID_GRADES    = {"مصنف درجة ثالثة", "مصنف درجة رابعة"}

# ── Rules engine ──────────────────────────────────────────────────────────────
def apply_rules(rec: dict) -> dict:
    """Apply all rules to a record. Returns dict of changed fields."""
    changes = {}

    has_email   = bool(rec.get("has_email"))
    dup         = bool(rec.get("duplicate_suspected"))
    manual      = bool(rec.get("needs_manual_review"))
    in_seq      = bool(rec.get("in_sequence"))
    prev_out    = bool(rec.get("previous_outreach_detected"))
    grade       = rec.get("classification_grade", "")
    region      = rec.get("region", "")

    # ── Follow-up Stage ──
    if in_seq:
        stage  = "In Sequence"
        action = "Follow-up"
    elif prev_out:
        stage  = "Previous Outreach"
        action = "Human Follow-up Required"
    elif dup:
        stage  = "Needs Manual Review"
        action = "Human Follow-up Required"
        changes["needs_manual_review"] = True
    elif manual:
        stage  = "Needs Manual Review"
        action = "Human Follow-up Required"
    elif not has_email:
        stage  = "No Valid Email"
        action = "Find Contact / Enrich"
    else:
        stage  = "Ready for Initial Outreach"
        action = "Enroll in Sequence"

    changes["follow_up_stage"] = stage
    changes["next_action"]     = action

    # ── Priority ──
    if not has_email or dup or manual:
        priority = "P4 - Monitor"
    elif grade in HIGH_GRADES and region in TIER1_REGIONS:
        priority = "P1 - High"
    elif grade in HIGH_GRADES or region in TIER1_REGIONS:
        priority = "P2 - Medium"
    elif grade in MID_GRADES and has_email:
        priority = "P2 - Medium"
    elif has_email:
        priority = "P3 - Low"
    else:
        priority = "P4 - Monitor"

    changes["priority"] = priority

    # ── Company Status ──
    if in_seq:
        status = "Outreach Sent"
    elif prev_out:
        status = "Prospect"
    else:
        status = "New"

    changes["company_status"] = status

    # ── Ready for Outreach (re-evaluate) ──
    changes["ready_for_outreach"] = has_email and not dup and not manual and not in_seq

    return changes


# ── Notion update ─────────────────────────────────────────────────────────────
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

def notion_patch(page_id: str, changes: dict):
    if not NOTION_API_KEY or not page_id:
        return

    def sel(v): return {"select": {"name": v}}
    def rt(v):  return {"rich_text": [{"text": {"content": str(v)[:2000]}}]}
    def chk(v): return {"checkbox": bool(v)}

    props = {}
    if "follow_up_stage" in changes:
        props["Follow-up Stage"] = sel(changes["follow_up_stage"])
    if "next_action" in changes:
        props["Next Action"] = sel(changes["next_action"])
    if "priority" in changes:
        props["Priority"] = sel(changes["priority"])
    if "company_status" in changes:
        props["Company Status"] = sel(changes["company_status"])
    if "ready_for_outreach" in changes:
        props["Ready for Outreach"]       = chk(changes["ready_for_outreach"])
        props["Sequence Enrollment Ready"] = chk(changes["ready_for_outreach"])
    if "needs_manual_review" in changes:
        props["Needs Manual Review"] = chk(changes["needs_manual_review"])

    if not props:
        return
    try:
        requests.patch(f"https://api.notion.com/v1/pages/{page_id}",
                       headers=NOTION_HEADERS, json={"properties": props}, timeout=15)
    except Exception as e:
        log.warning("Notion patch error for %s: %s", page_id, e)

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run",       action="store_true")
    parser.add_argument("--limit",         type=int, default=0)
    parser.add_argument("--update-notion", action="store_true",
                        help="Patch Notion pages too (slower — requires DB access)")
    args = parser.parse_args()

    log.info("=" * 60)
    log.info("05_rules_engine.py — Rules Engine")
    log.info("Mode: %s | Notion: %s",
             "DRY-RUN" if args.dry_run else "LIVE",
             "YES" if args.update_notion else "LOCAL ONLY")

    records = json.loads(INPUT_FILE.read_text(encoding="utf-8"))
    log.info("Records: %d", len(records))

    if args.limit:
        records_to_process = records[:args.limit]
    else:
        records_to_process = records

    stats = {"P1 - High": 0, "P2 - Medium": 0, "P3 - Low": 0, "P4 - Monitor": 0}
    stage_stats: dict[str, int] = {}
    changed_count = 0

    for i, rec in enumerate(records_to_process, 1):
        changes = apply_rules(rec)
        mem_num = rec.get("membership_number", "")

        # Track stats
        p = changes.get("priority", "")
        if p in stats:
            stats[p] += 1
        s = changes.get("follow_up_stage", "")
        stage_stats[s] = stage_stats.get(s, 0) + 1

        # Check if anything actually changed
        actually_changed = any(rec.get(k) != v for k, v in changes.items())
        if actually_changed:
            changed_count += 1

        if args.dry_run and i <= 5:
            log.info("[%d] %s → Stage: %s | Priority: %s | Status: %s",
                     i, rec.get("company_name", "")[:40],
                     changes["follow_up_stage"], changes["priority"], changes["company_status"])
            continue

        if not args.dry_run:
            rec.update(changes)

            if args.update_notion and NOTION_API_KEY:
                page_id = notion_find_page(mem_num)
                if page_id:
                    notion_patch(page_id, changes)
                    time.sleep(RATE_LIMIT)

        if i % 500 == 0 or i == len(records_to_process):
            log.info("[%d/%d] Changed: %d | P1: %d | P2: %d | P3: %d | P4: %d",
                     i, len(records_to_process), changed_count,
                     stats["P1 - High"], stats["P2 - Medium"], stats["P3 - Low"], stats["P4 - Monitor"])

    if not args.dry_run:
        OUTPUT_FILE.write_text(
            json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
        log.info("Saved: %s", OUTPUT_FILE)

    log.info("=" * 60)
    log.info("PRIORITY DISTRIBUTION:")
    for k, v in stats.items():
        pct = v / len(records_to_process) * 100 if records_to_process else 0
        log.info("  %-15s %5d  (%.1f%%)", k, v, pct)
    log.info("STAGE DISTRIBUTION:")
    for k, v in sorted(stage_stats.items(), key=lambda x: -x[1]):
        log.info("  %-35s %5d", k, v)
    log.info("Records changed: %d", changed_count)


if __name__ == "__main__":
    main()
