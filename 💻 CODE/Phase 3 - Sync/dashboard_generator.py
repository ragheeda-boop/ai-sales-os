#!/usr/bin/env python3
"""
AI Sales OS — Sales Dashboard Generator v1.0
=============================================
Pulls live data from Notion (Contacts + Companies databases),
aggregates metrics per company, and regenerates Sales_Dashboard_Accounts.html
by injecting fresh COMPANIES data into the HTML template.

Designed to run as a GitHub Actions step after the main pipeline.

Usage:
    python dashboard_generator.py                        # default output path
    python dashboard_generator.py --output /path/to.html
    python dashboard_generator.py --dry-run              # compute only, no write
    python dashboard_generator.py --limit 500            # cap contacts for testing

Output:
    - Sales_Dashboard_Accounts.html (updated in-place)
    - dashboard_stats.json          (metrics for health_check.py)
"""

import os
import re
import sys
import json
import time
import logging
import argparse
from datetime import datetime, timezone
from collections import defaultdict, Counter
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dotenv import load_dotenv

load_dotenv()

# ─── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("dashboard_generator.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)

# ─── Config ───────────────────────────────────────────────────────────────────
try:
    import requests
except ImportError:
    logger.error("requests not installed. Run: pip install requests")
    sys.exit(1)

NOTION_API_KEY             = os.getenv("NOTION_API_KEY")
NOTION_DATABASE_ID_CONTACTS  = os.getenv("NOTION_DATABASE_ID_CONTACTS", "9ca842d20aa9460bbdd958d0aa940d9c")
NOTION_DATABASE_ID_COMPANIES = os.getenv("NOTION_DATABASE_ID_COMPANIES", "331e04a62da74afe9ab6b0efead39200")
NOTION_BASE_URL            = "https://api.notion.com/v1"
NOTION_API_VERSION         = "2022-06-28"

# Path to the dashboard HTML template (same filename, updated in-place)
SCRIPT_DIR   = Path(__file__).parent
REPO_ROOT    = SCRIPT_DIR.parent.parent.parent   # AI Sales OS/
DASHBOARD_PATH = REPO_ROOT / "Sales_Dashboard_Accounts.html"
STATS_PATH     = SCRIPT_DIR / "dashboard_stats.json"

# ─── Status ranking (lower = better) ─────────────────────────────────────────
STATUS_RANK = {
    "Meeting Booked": 0,
    "Replied":        1,
    "Opened":         2,
    "In Sequence":    3,
    "Sent":           4,
    "Bounced":        5,
}
STATUS_ORDER = ["Meeting Booked", "Replied", "Opened", "In Sequence", "Sent", "Bounced", "Unknown"]

# ─── Industry classification (from Departments field) ─────────────────────────
INDUSTRY_PRIORITY = [
    ("healthcare",        ["medical", "health", "hospital", "pharmacy", "clinical",
                            "nursing", "medicine", "biosc", "pharmaceutical", "diagnostic"]),
    ("insurance",         ["insurance", "reinsurance"]),
    ("financial_services",["finance", "financial", "accounting", "banking", "bank ",
                            "investment", "capital", "treasury", "credit", "wealth", "fintech"]),
    ("technology",        ["technology", "software", "engineer", "it serv", "data science",
                            "digital", "saas", "cloud", "cyber", "developer"]),
    ("logistics",         ["supply chain", "logistics", "transport", "shipping",
                            "cargo", "distribution"]),
    ("retail",            ["retail", "commerce", "wholesale", "trading", "ecommerce",
                            "purchasing", "procurement"]),
    ("real_estate",       ["real estate", "property", "construction", "contracting",
                            "facility", "architecture"]),
    ("education",         ["education", "training", "learning", "university", "academic"]),
    ("government",        ["government", "ministry", "public sector", "municipality"]),
    ("marketing",         ["marketing", "advertising", "media", "public relations",
                            "branding", "pr department"]),
    ("legal",             ["legal", "compliance", "law ", "regulatory", "risk"]),
    ("food",              ["food", "beverage", "restaurant", "catering", "fmcg"]),
    ("wellness",          ["beauty", "wellness", "spa", "cosmetic", "sport", "fitness",
                            "gym", "salon"]),
    ("manufacturing",     ["manufacturing", "industrial", "production", "factory", "equipment"]),
]
INDUSTRY_LABELS_AR = {
    "healthcare":         "الرعاية الصحية",
    "insurance":          "التأمين",
    "financial_services": "الخدمات المالية",
    "technology":         "التكنولوجيا",
    "logistics":          "اللوجستيات",
    "retail":             "التجارة والتجزئة",
    "real_estate":        "العقارات",
    "education":          "التعليم",
    "government":         "الحكومة",
    "marketing":          "التسويق والإعلام",
    "legal":              "القانوني والامتثال",
    "food":               "الغذاء",
    "wellness":           "الجمال واللياقة",
    "manufacturing":      "الصناعة",
    "other":              "أخرى",
}

def classify_industry(text: str) -> str:
    text = text.lower()
    for key, keywords in INDUSTRY_PRIORITY:
        if any(kw in text for kw in keywords):
            return INDUSTRY_LABELS_AR[key]
    return INDUSTRY_LABELS_AR["other"]


# ─── Notion API helpers ───────────────────────────────────────────────────────

def _headers() -> Dict:
    return {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Notion-Version": NOTION_API_VERSION,
        "Content-Type": "application/json",
    }

_last_call = 0.0

def _throttle():
    """Simple rate limiter: max 3 req/sec to stay within Notion limits."""
    global _last_call
    gap = 1.0 / 3.0
    now = time.time()
    wait = gap - (now - _last_call)
    if wait > 0:
        time.sleep(wait)
    _last_call = time.time()


def notion_post(url: str, payload: dict, max_retries: int = 5) -> dict:
    """POST with exponential-backoff retry on 429/5xx."""
    for attempt in range(max_retries):
        _throttle()
        try:
            resp = requests.post(url, headers=_headers(), json=payload, timeout=30)
        except requests.exceptions.RequestException as exc:
            logger.warning(f"Request error (attempt {attempt+1}): {exc}")
            time.sleep(min(2 ** attempt, 30))
            continue

        if resp.status_code == 200:
            return resp.json()
        elif resp.status_code == 429:
            wait = float(resp.headers.get("Retry-After", min(2 ** attempt, 30)))
            logger.warning(f"Rate limited — sleeping {wait:.1f}s")
            time.sleep(wait)
        elif resp.status_code >= 500:
            wait = min(2 ** attempt, 30)
            logger.warning(f"Server error {resp.status_code} — retry in {wait}s")
            time.sleep(wait)
        else:
            logger.error(f"Notion API error {resp.status_code}: {resp.text[:300]}")
            return {}

    logger.error(f"Exhausted retries for {url}")
    return {}


def query_db_all(database_id: str, filter_body: Optional[dict] = None,
                 page_size: int = 100, limit: int = 0) -> List[dict]:
    """
    Paginate through a Notion database query and return all pages.
    Applies optional filter. Stops at `limit` records if set.
    """
    url = f"{NOTION_BASE_URL}/databases/{database_id}/query"
    results = []
    cursor = None
    page_num = 0

    while True:
        payload: dict = {"page_size": page_size}
        if filter_body:
            payload["filter"] = filter_body
        if cursor:
            payload["start_cursor"] = cursor

        page_num += 1
        data = notion_post(url, payload)
        if not data:
            break

        batch = data.get("results", [])
        results.extend(batch)
        logger.debug(f"  Page {page_num}: +{len(batch)} records (total={len(results)})")

        if limit and len(results) >= limit:
            results = results[:limit]
            logger.info(f"  Hit limit of {limit} records")
            break

        if not data.get("has_more"):
            break
        cursor = data.get("next_cursor")

    return results


# ─── Property extractors ──────────────────────────────────────────────────────

def prop_text(props: dict, name: str) -> str:
    """Extract plain text from rich_text or title property."""
    field = props.get(name, {})
    for key in ("rich_text", "title"):
        items = field.get(key, [])
        if items:
            return items[0].get("plain_text", "").strip()
    return ""


def prop_select(props: dict, name: str) -> str:
    sel = props.get(name, {}).get("select")
    return sel.get("name", "") if sel else ""


def prop_checkbox(props: dict, name: str) -> bool:
    return bool(props.get(name, {}).get("checkbox", False))


def prop_number(props: dict, name: str) -> Optional[float]:
    val = props.get(name, {}).get("number")
    return val  # None if not set


def prop_date(props: dict, name: str) -> str:
    """Return ISO date string (YYYY-MM-DD) or empty string."""
    dt = props.get(name, {}).get("date")
    if dt and dt.get("start"):
        return dt["start"][:10]
    return ""


def prop_email(props: dict, name: str) -> str:
    return props.get(name, {}).get("email", "") or ""


# ─── Fetch contacts with email activity ───────────────────────────────────────

def fetch_active_contacts(limit: int = 0) -> List[dict]:
    """
    Query Contacts DB for contacts where at least one of:
      Email Sent = True  OR  Meeting Booked = True
      OR  Replied = True  OR  Email Opened = True
    These are contacts that have been actively reached out to.
    """
    logger.info("Fetching active contacts from Notion Contacts DB...")

    # Compound OR filter: any engagement boolean = true
    filter_body = {
        "or": [
            {"property": "Email Sent",     "checkbox": {"equals": True}},
            {"property": "Meeting Booked", "checkbox": {"equals": True}},
            {"property": "Replied",        "checkbox": {"equals": True}},
            {"property": "Email Opened",   "checkbox": {"equals": True}},
            {"property": "Email Bounced",  "checkbox": {"equals": True}},
        ]
    }

    pages = query_db_all(
        NOTION_DATABASE_ID_CONTACTS,
        filter_body=filter_body,
        page_size=100,
        limit=limit,
    )
    logger.info(f"Fetched {len(pages)} active contacts")
    return pages


def parse_contact(page: dict) -> dict:
    """Extract relevant fields from a Notion contact page."""
    props = page.get("properties", {})
    return {
        "apollo_contact_id": prop_text(props, "Apollo Contact Id"),
        "email":             prop_email(props, "Email"),
        "company_name":      prop_text(props, "Company Name for Emails"),
        "seniority":         prop_select(props, "Seniority"),
        "departments":       prop_text(props, "Departments"),
        "sub_departments":   prop_text(props, "Sub Departments"),
        "city":              prop_text(props, "City"),
        "country":           prop_text(props, "Country"),
        "lead_score":        prop_number(props, "Lead Score"),
        "lead_tier":         prop_select(props, "Lead Tier"),
        "outreach_status":   prop_select(props, "Outreach Status"),
        "email_sent":        prop_checkbox(props, "Email Sent"),
        "email_opened":      prop_checkbox(props, "Email Opened"),
        "email_bounced":     prop_checkbox(props, "Email Bounced"),
        "replied":           prop_checkbox(props, "Replied"),
        "meeting_booked":    prop_checkbox(props, "Meeting Booked"),
        "last_contacted":    prop_date(props, "Last Contacted"),
        "contact_owner":     prop_text(props, "Contact Owner"),
        "apollo_account_id": prop_text(props, "Apollo Account Id"),
    }


# ─── Fetch companies for enrichment (Industry + Employees + City) ─────────────

def fetch_companies_lookup(apollo_account_ids: set) -> Dict[str, dict]:
    """
    Query Companies DB and build a lookup by Apollo Account ID.
    Returns {apollo_account_id: {industry, employees, city, account_stage}}

    Note: We query the full Companies DB and match by Apollo Account ID.
    This is more reliable than filtering since Notion can't filter by a text
    field matching a set of values in a single request.
    """
    if not apollo_account_ids:
        return {}

    logger.info("Fetching Companies DB for industry/employees enrichment...")
    pages = query_db_all(NOTION_DATABASE_ID_COMPANIES, page_size=100)
    logger.info(f"Fetched {len(pages)} company records")

    lookup = {}
    matched = 0
    for page in pages:
        props = page.get("properties", {})
        aid = prop_text(props, "Apollo Account Id")
        if aid and aid in apollo_account_ids:
            lookup[aid] = {
                "industry": prop_text(props, "Industry"),
                "employees": prop_number(props, "Employees"),
                "employee_size": prop_text(props, "Employee Size"),
                "city": prop_text(props, "Company City"),
                "country": prop_text(props, "Company Country"),
                "account_stage": prop_select(props, "Account Stage"),
            }
            matched += 1

    logger.info(f"Matched {matched}/{len(apollo_account_ids)} companies for enrichment")
    return lookup


# ─── Contact Owner → display name mapping ────────────────────────────────────

def map_owner(email: str) -> str:
    e = email.lower()
    if "ragheed" in e or "ratlfintech" in e:
        return "رغيد"
    if "ibrahim" in e or "muhide" in e:
        return "إبراهيم"
    if "soha" in e:
        return "سها"
    return ""


# ─── Aggregate contacts into company-level records ───────────────────────────

def aggregate_companies(contacts: List[dict], companies_lookup: Dict[str, dict]) -> List[dict]:
    """
    Group contacts by company and aggregate:
    - contact_count, meeting_booked, replied, email_opened, email_sent, bounced
    - avg_score, top_seniority, most common city/owner
    - best_status (highest engagement level)
    - last_contacted (latest date)
    - industry (from Companies DB first, then inferred from Departments)
    - employees (from Companies DB)
    """
    # Deduplicate contacts by Apollo Contact ID first
    seen_ids: set = set()
    unique: List[dict] = []
    for c in contacts:
        cid = c["apollo_contact_id"] or c["email"]
        if cid and cid not in seen_ids:
            seen_ids.add(cid)
            unique.append(c)
    logger.info(f"Deduped to {len(unique)} unique contacts")

    # Aggregate
    agg: Dict[str, dict] = defaultdict(lambda: {
        "contact_count": 0,
        "meeting_booked": 0,
        "replied": 0,
        "email_opened": 0,
        "email_sent": 0,
        "bounced": 0,
        "scores": [],
        "seniority_counts": Counter(),
        "city_counts": Counter(),
        "owner_counts": Counter(),
        "dept_texts": [],
        "last_contacted_dates": [],
        "apollo_account_ids": set(),
        "best_rank": 999,
        "best_status": None,
        "country": "",
    })

    for c in unique:
        company = c["company_name"]
        if not company:
            continue

        a = agg[company]
        a["contact_count"] += 1

        if c["meeting_booked"]:  a["meeting_booked"] += 1
        if c["replied"]:         a["replied"] += 1
        if c["email_opened"]:    a["email_opened"] += 1
        if c["email_sent"] or c["email_bounced"]: a["email_sent"] += 1
        if c["email_bounced"]:   a["bounced"] += 1

        if c["lead_score"] is not None:
            a["scores"].append(c["lead_score"])

        if c["seniority"]:
            # Normalize C-Suite variants
            sen = c["seniority"]
            if sen.lower().replace("-", " ").replace("_", " ").strip() in {"c suite", "c-suite"}:
                sen = "C-Suite"
            a["seniority_counts"][sen] += 1

        if c["city"]:    a["city_counts"][c["city"]] += 1
        if c["country"]: a["country"] = c["country"]

        owner_email = c["contact_owner"]
        owner = map_owner(owner_email)
        if owner: a["owner_counts"][owner] += 1

        dept_text = f"{c['departments']} {c['sub_departments']}"
        if dept_text.strip(): a["dept_texts"].append(dept_text)

        if c["last_contacted"]:
            a["last_contacted_dates"].append(c["last_contacted"])

        if c["apollo_account_id"]:
            a["apollo_account_ids"].add(c["apollo_account_id"])

        # Track best outreach status
        status = c["outreach_status"] or ""
        rank = STATUS_RANK.get(status, 999)
        if rank < a["best_rank"]:
            a["best_rank"] = rank
            a["best_status"] = status

    # Build final list
    results = []
    for company, data in agg.items():
        if data["best_status"] is None or data["best_rank"] == 999:
            # Include if has meetings/replies even without tracked status
            if data["meeting_booked"] == 0 and data["replied"] == 0:
                continue

        # Top values
        avg_score = (
            round(sum(data["scores"]) / len(data["scores"]), 1)
            if data["scores"] else 0
        )
        top_seniority = (
            data["seniority_counts"].most_common(1)[0][0]
            if data["seniority_counts"] else ""
        )
        city = (
            data["city_counts"].most_common(1)[0][0]
            if data["city_counts"] else ""
        )
        owner = (
            data["owner_counts"].most_common(1)[0][0]
            if data["owner_counts"] else ""
        )
        last_contacted = (
            max(data["last_contacted_dates"])
            if data["last_contacted_dates"] else ""
        )

        # Industry: Companies DB first → infer from departments
        industry = ""
        employees = 0
        co_city = city  # fallback to contact city

        for aid in data["apollo_account_ids"]:
            if aid in companies_lookup:
                co = companies_lookup[aid]
                if co.get("industry"):
                    industry = co["industry"]
                if co.get("employees"):
                    employees = int(co["employees"])
                if co.get("city") and not city:
                    co_city = co["city"]
                if co.get("country") and not data["country"]:
                    data["country"] = co["country"]
                break

        if not industry and data["dept_texts"]:
            all_depts = " ".join(data["dept_texts"])
            industry = classify_industry(all_depts)

        results.append({
            "company":       company,
            "contact_count": data["contact_count"],
            "meeting_booked":data["meeting_booked"],
            "replied":       data["replied"],
            "email_opened":  data["email_opened"],
            "email_sent":    data["email_sent"],
            "bounced":       data["bounced"],
            "best_status":   data["best_status"] or "Unknown",
            "avg_score":     avg_score,
            "top_seniority": top_seniority,
            "country":       data["country"] or "Saudi Arabia",
            "last_contacted":last_contacted,
            "city":          co_city,
            "owner":         owner,
            "industry":      industry,
            "employees":     employees,
        })

    # Sort: best status first, then by contact count
    results.sort(key=lambda x: (
        STATUS_ORDER.index(x["best_status"]) if x["best_status"] in STATUS_ORDER else 99,
        -x["contact_count"]
    ))

    logger.info(f"Aggregated {len(results)} companies")
    return results


# ─── Build JavaScript COMPANIES array ────────────────────────────────────────

def build_js_array(companies: List[dict]) -> str:
    """Serialize company list to a compact JavaScript const COMPANIES = [...] block."""
    lines = ["const COMPANIES = ["]
    for c in companies:
        name  = c["company"].replace("\\", "\\\\").replace('"', '\\"').replace("\n", "")
        city  = (c["city"] or "").replace('"', '\\"')
        owner = c["owner"] or ""
        ind   = (c["industry"] or "").replace('"', '\\"')
        sen   = (c["top_seniority"] or "").replace('"', '\\"')
        line = (
            f'  {{company:"{name}",cnt:{c["contact_count"]},mtg:{c["meeting_booked"]},'
            f'rpl:{c["replied"]},opn:{c["email_opened"]},snt:{c["email_sent"]},'
            f'bnc:{c["bounced"]},status:"{c["best_status"]}",'
            f'score:{c["avg_score"]},seniority:"{sen}",'
            f'country:"{c["country"]}",lc:"{c["last_contacted"]}",'
            f'city:"{city}",owner:"{owner}",industry:"{ind}",employees:{c["employees"]}}},'
        )
        lines.append(line)
    lines.append("];")
    return "\n".join(lines)


# ─── Inject into HTML template ────────────────────────────────────────────────

def inject_into_html(html_path: Path, js_array: str, generated_at: str) -> str:
    """
    Read the existing dashboard HTML and replace:
      1. The COMPANIES array (between 'const COMPANIES = [' and '];')
      2. The GENERATED_AT timestamp
    Returns the updated HTML string.
    """
    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Replace COMPANIES array
    pattern = r"const COMPANIES = \[.*?\];"
    replacement = js_array
    updated, count = re.subn(pattern, replacement, content, flags=re.DOTALL)
    if count == 0:
        logger.error("Could not find 'const COMPANIES = [...]' in the HTML template")
        raise ValueError("COMPANIES array not found in HTML — template may be corrupted")
    logger.info(f"Replaced COMPANIES array ({count} occurrence(s))")

    # Replace GENERATED_AT timestamp
    ts_pattern = r'const GEN = "[^"]*"'
    ts_replacement = f'const GEN = "{generated_at}"'
    updated = re.sub(ts_pattern, ts_replacement, updated)

    return updated


# ─── Stats output ─────────────────────────────────────────────────────────────

def write_stats(companies: List[dict], stats_path: Path, elapsed: float):
    stats = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "elapsed_seconds": round(elapsed, 1),
        "total_companies": len(companies),
        "companies_with_meetings": sum(1 for c in companies if c["meeting_booked"] > 0),
        "companies_with_replies": sum(1 for c in companies if c["replied"] > 0),
        "total_contacts_reached": sum(c["contact_count"] for c in companies),
        "total_meetings": sum(c["meeting_booked"] for c in companies),
        "status_distribution": dict(Counter(c["best_status"] for c in companies)),
        "top_industries": dict(Counter(c["industry"] for c in companies if c["industry"]).most_common(10)),
        "top_cities": dict(Counter(c["city"] for c in companies if c["city"]).most_common(8)),
    }
    with open(stats_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    logger.info(f"Stats written to {stats_path}")
    return stats


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Regenerate Sales Dashboard from Notion live data")
    parser.add_argument("--output",  default=str(DASHBOARD_PATH), help="Output HTML path")
    parser.add_argument("--dry-run", action="store_true", help="Compute data but don't write files")
    parser.add_argument("--limit",   type=int, default=0,   help="Max contacts to fetch (0 = all)")
    args = parser.parse_args()

    if not NOTION_API_KEY:
        logger.error("NOTION_API_KEY not set. Check .env or GitHub Secrets.")
        sys.exit(1)

    output_path = Path(args.output)
    if not output_path.exists():
        logger.error(f"Dashboard HTML not found at: {output_path}")
        logger.error("Run from the AI Sales OS repo root, or pass --output <path>")
        sys.exit(1)

    start = time.time()
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    logger.info(f"=== Dashboard Generator v1.0 | {generated_at} ===")

    # 1. Fetch active contacts
    contact_pages = fetch_active_contacts(limit=args.limit)
    contacts = [parse_contact(p) for p in contact_pages]

    # 2. Collect Apollo Account IDs for company enrichment
    account_ids = {c["apollo_account_id"] for c in contacts if c["apollo_account_id"]}
    logger.info(f"Unique Apollo Account IDs from contacts: {len(account_ids)}")

    # 3. Fetch Companies DB for enrichment (industry, employees, city)
    companies_lookup = fetch_companies_lookup(account_ids)

    # 4. Aggregate into company-level records
    companies = aggregate_companies(contacts, companies_lookup)

    if not companies:
        logger.warning("No companies found — dashboard would be empty. Aborting.")
        sys.exit(1)

    # 5. Print summary
    meetings_total = sum(c["meeting_booked"] for c in companies)
    contacts_total = sum(c["contact_count"] for c in companies)
    logger.info(f"Summary: {len(companies)} companies | {contacts_total} contacts | {meetings_total} meetings")

    # 6. Build JS array
    js_array = build_js_array(companies)
    logger.info(f"Built JS array: {len(js_array):,} chars for {len(companies)} companies")

    if args.dry_run:
        logger.info("Dry run — skipping file writes")
        print(f"\n{'='*60}")
        print(f"DRY RUN RESULTS")
        print(f"  Companies:      {len(companies)}")
        print(f"  Contacts:       {contacts_total}")
        print(f"  Meetings:       {meetings_total}")
        print(f"  JS array size:  {len(js_array):,} chars")
        print(f"{'='*60}\n")
        return

    # 7. Inject into HTML template
    try:
        updated_html = inject_into_html(output_path, js_array, generated_at)
    except ValueError as e:
        logger.error(str(e))
        sys.exit(1)

    # 8. Write updated HTML
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(updated_html)
    logger.info(f"Dashboard written: {output_path} ({len(updated_html):,} bytes)")

    # 9. Write stats
    elapsed = time.time() - start
    stats = write_stats(companies, STATS_PATH, elapsed)

    print(f"\n{'='*60}")
    print(f"DASHBOARD GENERATOR — COMPLETE")
    print(f"  Runtime:        {elapsed:.1f}s")
    print(f"  Companies:      {stats['total_companies']}")
    print(f"  Contacts:       {stats['total_contacts_reached']}")
    print(f"  Meetings:       {stats['total_meetings']}")
    print(f"  HTML written:   {output_path}")
    print(f"  Generated at:   {generated_at}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
