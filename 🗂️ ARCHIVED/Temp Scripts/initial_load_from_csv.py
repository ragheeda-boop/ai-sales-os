#!/usr/bin/env python3
"""
Initial Load: CSV → Notion
Reads Apollo CSV export, creates Companies then Contacts in Notion.
Run once for the initial data load, then use daily_sync.py for updates.

Usage:
    python initial_load_from_csv.py "path/to/apollo-contacts-export.csv"
    python initial_load_from_csv.py  # uses default path
"""
import os
import sys
import csv
import logging
import time
from typing import Dict, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Add parent dir to path for imports
sys.path.insert(0, os.path.dirname(__file__))
from notion_helpers import (
    NOTION_DATABASE_ID_CONTACTS,
    NOTION_DATABASE_ID_COMPANIES,
    preload_companies,
    preload_contacts,
    create_page,
    update_page,
    logger as helpers_logger,
)

# ─── Config ──────────────────────────────────────────────────────────────────

DEFAULT_CSV_PATH = os.path.join(
    os.path.expanduser("~"), "Downloads", "apollo-contacts-export (16).csv"
)
MAX_WORKERS = 3  # Concurrent Notion writes

# ─── Logging ─────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("initial_load.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


# ─── CSV Reading ─────────────────────────────────────────────────────────────

def read_csv(csv_path: str) -> List[Dict]:
    """Read CSV into list of dicts."""
    rows = []
    with open(csv_path, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    logger.info(f"Read {len(rows)} rows from CSV")
    return rows


# ─── Company Extraction & Formatting ─────────────────────────────────────────

def extract_unique_companies(rows: List[Dict]) -> Dict[str, Dict]:
    """Extract unique companies from CSV rows, keyed by Apollo Account Id."""
    companies = {}
    for row in rows:
        aid = (row.get("Apollo Account Id") or "").strip()
        if not aid or aid in companies:
            continue
        companies[aid] = row
    logger.info(f"Extracted {len(companies)} unique companies")
    return companies


def _rt(value: str) -> dict:
    """Format string as Notion rich_text."""
    return {"rich_text": [{"text": {"content": str(value)[:2000]}}]}


def _safe_int(val: str) -> Optional[int]:
    """Parse integer from CSV, return None if invalid."""
    if not val or not val.strip():
        return None
    try:
        return int(float(val.strip().replace(",", "")))
    except (ValueError, TypeError):
        return None


def _safe_float(val: str) -> Optional[float]:
    """Parse float from CSV, return None if invalid."""
    if not val or not val.strip():
        return None
    try:
        return float(val.strip().replace(",", "").replace("$", ""))
    except (ValueError, TypeError):
        return None


def map_employee_size(count: Optional[int]) -> Optional[str]:
    if not count:
        return None
    if count <= 10: return "1-10"
    elif count <= 50: return "11-50"
    elif count <= 200: return "51-200"
    elif count <= 500: return "201-500"
    elif count <= 1000: return "501-1000"
    elif count <= 5000: return "1001-5000"
    else: return "5001+"


def map_revenue_range(revenue: Optional[float]) -> Optional[str]:
    if not revenue:
        return None
    if revenue < 1_000_000: return "<$1M"
    elif revenue < 10_000_000: return "$1M-$10M"
    elif revenue < 50_000_000: return "$10M-$50M"
    elif revenue < 100_000_000: return "$50M-$100M"
    elif revenue < 500_000_000: return "$100M-$500M"
    else: return "$500M+"


def format_company(row: Dict) -> Dict:
    """Format CSV row as Notion company properties."""
    props = {}
    name = (row.get("Company Name") or "Unknown Company").strip()
    props["Company Name"] = {"title": [{"text": {"content": name[:300]}}]}

    # Rich text fields
    text_map = {
        "Domain": None,  # extract from Website
        "Company Address": row.get("Company Address"),
        "Company City": row.get("Company City"),
        "Company State": row.get("Company State"),
        "Company Country": row.get("Company Country"),
        "Industry": row.get("Industry"),
        "Keywords": row.get("Keywords"),
        "Technologies": row.get("Technologies"),
        "Apollo Account Id": row.get("Apollo Account Id"),
        "Record Source": "Apollo",
        "Data Status": "Raw",
        "Account Owner": row.get("Account Owner"),
        "Company Name for Emails": row.get("Company Name for Emails"),
        "Subsidiary of": row.get("Subsidiary of"),
        "Subsidiary of Organization ID": row.get("Subsidiary of (Organization ID)"),
        "NAICS Codes": None,
        "SIC Codes": None,
    }

    # Extract domain from website URL
    website = (row.get("Website") or "").strip()
    if website:
        domain = website.replace("https://", "").replace("http://", "").rstrip("/")
        text_map["Domain"] = domain

    for prop_name, value in text_map.items():
        if value and value.strip():
            props[prop_name] = _rt(value.strip())

    # URL fields
    url_map = {
        "Website": website,
        "Company Linkedin Url": row.get("Company Linkedin Url"),
        "Facebook Url": row.get("Facebook Url"),
        "Twitter Url": row.get("Twitter Url"),
    }
    for prop_name, value in url_map.items():
        if value and value.strip():
            props[prop_name] = {"url": value.strip()}

    # Phone
    phone = (row.get("Company Phone") or "").strip().lstrip("'")
    if phone:
        props["Company Phone"] = {"phone_number": phone}

    # Number fields
    emp_count = _safe_int(row.get("# Employees"))
    if emp_count:
        props["Employees"] = {"number": emp_count}
        emp_size = map_employee_size(emp_count)
        if emp_size:
            props["Employee Size"] = _rt(emp_size)

    annual_rev = _safe_float(row.get("Annual Revenue"))
    if annual_rev:
        props["Annual Revenue"] = {"number": annual_rev}
        rev_range = map_revenue_range(annual_rev)
        if rev_range:
            props["Revenue Range"] = _rt(rev_range)

    total_funding = _safe_float(row.get("Total Funding"))
    if total_funding:
        props["Total Funding"] = {"number": total_funding}

    latest_funding = _safe_float(row.get("Latest Funding Amount"))
    if latest_funding:
        props["Latest Funding Amount"] = {"number": latest_funding}

    latest_funding_num = _safe_float(row.get("Latest Funding"))
    if latest_funding_num:
        props["Latest Funding"] = {"number": latest_funding_num}

    # Last Raised At (date)
    last_raised = (row.get("Last Raised At") or "").strip()
    if last_raised:
        try:
            dt = datetime.fromisoformat(last_raised.replace("Z", "+00:00"))
            props["Last Raised At"] = {"date": {"start": dt.strftime("%Y-%m-%d")}}
        except ValueError:
            pass

    retail = _safe_int(row.get("Number of Retail Locations"))
    if retail:
        props["Number of Retail Locations"] = {"number": retail}

    # Intent fields
    for field in ["Primary Intent Topic", "Secondary Intent Topic"]:
        val = (row.get(field) or "").strip()
        if val:
            props[field] = _rt(val)

    for field in ["Primary Intent Score", "Secondary Intent Score"]:
        val = _safe_int(row.get(field))
        if val is not None:
            props[field] = {"number": val}

    return props


# ─── Contact Formatting ──────────────────────────────────────────────────────

def _parse_bool(val: str) -> bool:
    return (val or "").strip().lower() == "true"


def _parse_date(val: str) -> Optional[str]:
    """Parse ISO date string, return YYYY-MM-DD or full ISO."""
    if not val or not val.strip():
        return None
    try:
        dt = datetime.fromisoformat(val.strip().replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%dT%H:%M:%S+00:00")
    except ValueError:
        return None


def format_contact(row: Dict, company_page_id: Optional[str] = None) -> Dict:
    """Format CSV row as Notion contact properties."""
    props = {}

    first = (row.get("First Name") or "").strip()
    last = (row.get("Last Name") or "").strip()
    full_name = f"{first} {last}".strip() or "Unknown"

    props["Full Name"] = {"title": [{"text": {"content": full_name[:300]}}]}

    # Rich text fields
    text_map = {
        "First Name": first,
        "Last Name": last,
        "Title": row.get("Title"),
        "Departments": row.get("Departments"),
        "Sub Departments": row.get("Sub Departments"),
        "City": row.get("City"),
        "State": row.get("State"),
        "Country": row.get("Country"),
        "Apollo Contact Id": row.get("Apollo Contact Id"),
        "Apollo Account Id": row.get("Apollo Account Id"),
        "Company Name for Emails": row.get("Company Name for Emails"),
        "Company 1": row.get("Company Name"),
        "Primary Email Source": row.get("Primary Email Source"),
        "Primary Email Verification Source": row.get("Primary Email Verification Source"),
        "Primary Email Catch-all Status": row.get("Primary Email Catch-all Status"),
        "Secondary Email Source": row.get("Secondary Email Source"),
        "Secondary Email Verification Source": row.get("Secondary Email Verification Source"),
        "Notes": None,
        "Lists": row.get("Lists"),
        "Contact Owner": row.get("Contact Owner"),
        "Primary Intent Topic": row.get("Primary Intent Topic"),
        "Secondary Intent Topic": row.get("Secondary Intent Topic"),
    }

    for prop_name, value in text_map.items():
        if value and value.strip():
            props[prop_name] = _rt(value.strip())

    # Email fields
    email = (row.get("Email") or "").strip()
    if email:
        props["Email"] = {"email": email}

    secondary_email = (row.get("Secondary Email") or "").strip()
    if secondary_email:
        props["Secondary Email"] = {"email": secondary_email}

    # Phone fields (strip leading apostrophe from CSV)
    phone_map = {
        "Work Direct Phone": row.get("Work Direct Phone"),
        "Mobile Phone": row.get("Mobile Phone"),
        "Home Phone": row.get("Home Phone"),
        "Corporate Phone": row.get("Corporate Phone"),
        "Other Phone": row.get("Other Phone"),
    }
    for prop_name, value in phone_map.items():
        if value and value.strip():
            props[prop_name] = {"phone_number": value.strip().lstrip("'")}

    # URL fields
    linkedin = (row.get("Person Linkedin Url") or "").strip()
    if linkedin:
        props["Person Linkedin Url"] = {"url": linkedin}

    # Select fields
    seniority = (row.get("Seniority") or "").strip()
    if seniority:
        props["Seniority"] = {"select": {"name": seniority}}

    stage = (row.get("Stage") or "").strip()
    if stage:
        props["Stage"] = {"select": {"name": stage}}

    email_status = (row.get("Email Status") or "").strip()
    if email_status:
        props["Email Status"] = {"select": {"name": email_status}}

    secondary_email_status = (row.get("Secondary Email Status") or "").strip()
    if secondary_email_status:
        props["Secondary Email Status"] = _rt(secondary_email_status)

    props["Record Source"] = {"select": {"name": "Apollo"}}
    props["Data Status"] = {"select": {"name": "Raw"}}

    # Checkbox fields
    props["Email Sent"] = {"checkbox": _parse_bool(row.get("Email Sent", ""))}
    props["Email Opened"] = {"checkbox": _parse_bool(row.get("Email Open", ""))}
    props["Email Bounced"] = {"checkbox": _parse_bool(row.get("Email Bounced", ""))}
    props["Replied"] = {"checkbox": _parse_bool(row.get("Replied", ""))}
    props["Demoed"] = {"checkbox": _parse_bool(row.get("Demoed", ""))}
    props["Do Not Call"] = {"checkbox": _parse_bool(row.get("Do Not Call", ""))}
    props["Meeting Booked"] = {"checkbox": False}

    # Date fields
    last_contacted = _parse_date(row.get("Last Contacted"))
    if last_contacted:
        props["Last Contacted"] = {"date": {"start": last_contacted}}

    email_verified = _parse_date(row.get("Primary Email Last Verified At"))
    if email_verified:
        props["Primary Email Last Verified At"] = {"date": {"start": email_verified}}

    # Number fields
    lead_score = _safe_int(row.get("Lead Score"))
    if lead_score is not None:
        props["Lead Score"] = {"number": lead_score}

    for field in ["Primary Intent Score", "Secondary Intent Score"]:
        val = _safe_int(row.get(field))
        if val is not None:
            props[field] = {"number": val}

    # Company relation
    if company_page_id:
        props["Company"] = {"relation": [{"id": company_page_id}]}

    return props


# ─── Sync Logic ───────────────────────────────────────────────────────────────

def sync_companies(rows: List[Dict], company_lookup: Dict[str, str]) -> Dict[str, str]:
    """
    Sync companies to Notion. Returns updated lookup.
    """
    companies = extract_unique_companies(rows)
    stats = {"created": 0, "exists": 0, "errors": 0}

    def process_company(item):
        aid, row = item
        # Check if already exists
        existing = company_lookup.get(f"aid:{aid}")
        if existing:
            return "exists", aid, existing

        props = format_company(row)
        try:
            page_id = create_page(NOTION_DATABASE_ID_COMPANIES, props)
            return "created", aid, page_id
        except Exception as e:
            name = (row.get("Company Name") or "?")[:50]
            logger.error(f"Error creating company '{name}': {e}")
            return "error", aid, None

    logger.info(f"Syncing {len(companies)} companies to Notion ({MAX_WORKERS} threads)...")

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(process_company, item): item
            for item in companies.items()
        }
        for i, fut in enumerate(as_completed(futures), 1):
            status, aid, page_id = fut.result()
            stats[status] = stats.get(status, 0) + 1

            if status == "created" and page_id:
                company_lookup[f"aid:{aid}"] = page_id

            if i % 100 == 0 or i == len(companies):
                logger.info(f"Companies: {i}/{len(companies)} | {stats}")

    logger.info(f"Company sync done: {stats}")
    return company_lookup


def sync_contacts(rows: List[Dict], company_lookup: Dict, contact_lookup: Dict):
    """Sync contacts to Notion."""
    stats = {"created": 0, "exists": 0, "errors": 0}

    # Deduplicate by Apollo Contact Id
    seen_ids = set()
    unique_rows = []
    for row in rows:
        cid = (row.get("Apollo Contact Id") or "").strip()
        if not cid or cid in seen_ids:
            continue
        seen_ids.add(cid)
        unique_rows.append(row)

    logger.info(f"Syncing {len(unique_rows)} unique contacts to Notion ({MAX_WORKERS} threads)...")

    def process_contact(row):
        cid = (row.get("Apollo Contact Id") or "").strip()
        email = (row.get("Email") or "").strip().lower()

        # Check if already exists
        existing = contact_lookup.get(f"aid:{cid}")
        if not existing and email:
            existing = contact_lookup.get(f"email:{email}")
        if existing:
            return "exists", cid

        # Find company
        aid = (row.get("Apollo Account Id") or "").strip()
        company_page_id = company_lookup.get(f"aid:{aid}") if aid else None

        props = format_contact(row, company_page_id)
        try:
            page_id = create_page(NOTION_DATABASE_ID_CONTACTS, props)
            return "created", cid
        except Exception as e:
            name = f"{row.get('First Name', '')} {row.get('Last Name', '')}".strip()[:50]
            logger.error(f"Error creating contact '{name}': {e}")
            return "error", cid

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(process_contact, row): row
            for row in unique_rows
        }
        for i, fut in enumerate(as_completed(futures), 1):
            status, cid = fut.result()
            stats[status] = stats.get(status, 0) + 1

            if i % 200 == 0 or i == len(unique_rows):
                logger.info(f"Contacts: {i}/{len(unique_rows)} | {stats}")

    logger.info(f"Contact sync done: {stats}")


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    csv_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_CSV_PATH

    if not os.path.exists(csv_path):
        logger.error(f"CSV file not found: {csv_path}")
        sys.exit(1)

    logger.info("=" * 80)
    logger.info("INITIAL LOAD: CSV → Notion")
    logger.info(f"CSV: {csv_path}")
    logger.info("=" * 80)

    start_time = time.time()

    # Step 1: Read CSV
    rows = read_csv(csv_path)

    # Step 2: Pre-load existing data from Notion (skip duplicates)
    logger.info("Pre-loading existing Notion data...")
    company_lookup = preload_companies()
    contact_lookup = preload_contacts()

    # Step 3: Sync companies first
    logger.info("─" * 40)
    logger.info("PHASE 1: Syncing Companies")
    logger.info("─" * 40)
    company_lookup = sync_companies(rows, company_lookup)

    # Step 4: Sync contacts (with company relations)
    logger.info("─" * 40)
    logger.info("PHASE 2: Syncing Contacts")
    logger.info("─" * 40)
    sync_contacts(rows, company_lookup, contact_lookup)

    elapsed = time.time() - start_time
    logger.info("=" * 80)
    logger.info(f"INITIAL LOAD COMPLETE in {elapsed / 60:.1f} minutes")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
