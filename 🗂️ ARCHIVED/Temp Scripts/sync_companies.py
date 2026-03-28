#!/usr/bin/env python3
"""
Sync companies from Apollo to Notion.
Extracts unique companies from contacts and syncs to Notion Companies database.

Uses notion_helpers for pre-loading, rate limiting, and smart retry.
"""

import os
import sys
import logging
import requests
import time
from typing import Dict, List, Optional, Set, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

# Add parent dir to path for imports
sys.path.insert(0, os.path.dirname(__file__))
from notion_helpers import (
    NOTION_DATABASE_ID_COMPANIES,
    NOTION_DATABASE_ID_CONTACTS,
    preload_companies,
    create_page,
    update_page,
    logger as helpers_logger,
)

# Configuration
APOLLO_API_KEY = os.getenv("APOLLO_API_KEY")
APOLLO_BASE_URL = "https://api.apollo.io/v1"
APOLLO_RATE_LIMIT_DELAY = 0.1  # 10 requests/second
MAX_WORKERS = 3  # Concurrent Notion writes

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("sync_companies.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def map_employee_size(employee_count: Optional[int]) -> Optional[str]:
    """Map employee count to employee size range."""
    if not employee_count:
        return None
    if employee_count <= 10:
        return "1-10"
    elif employee_count <= 50:
        return "11-50"
    elif employee_count <= 200:
        return "51-200"
    elif employee_count <= 500:
        return "201-500"
    elif employee_count <= 1000:
        return "501-1000"
    elif employee_count <= 5000:
        return "1001-5000"
    else:
        return "5001+"


def map_revenue_range(annual_revenue: Optional[int]) -> Optional[str]:
    """Map annual revenue to revenue range."""
    if not annual_revenue:
        return None
    if annual_revenue < 1_000_000:
        return "<$1M"
    elif annual_revenue < 10_000_000:
        return "$1M-$10M"
    elif annual_revenue < 50_000_000:
        return "$10M-$50M"
    elif annual_revenue < 100_000_000:
        return "$50M-$100M"
    elif annual_revenue < 500_000_000:
        return "$100M-$500M"
    else:
        return "$500M+"


def fetch_all_apollo_contacts(page_size: int = 100) -> List[Dict]:
    """Fetch all contacts from Apollo with pagination."""
    all_contacts = []
    page = 1

    while True:
        logger.info(f"Fetching Apollo contacts page {page}...")

        url = f"{APOLLO_BASE_URL}/contacts/search"
        params = {
            "page": page,
            "per_page": page_size
        }
        headers = {
            "Content-Type": "application/json",
            "X-Api-Key": APOLLO_API_KEY
        }

        try:
            response = requests.get(url, params=params, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()

            contacts = data.get("contacts", [])
            if not contacts:
                logger.info(f"No more contacts. Total fetched: {len(all_contacts)}")
                break

            all_contacts.extend(contacts)
            logger.info(f"Fetched {len(contacts)} contacts on page {page}. Total: {len(all_contacts)}")

            page += 1
            time.sleep(APOLLO_RATE_LIMIT_DELAY)

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching Apollo contacts page {page}: {e}")
            break

    return all_contacts


def extract_unique_companies(contacts: List[Dict]) -> Dict[str, Dict]:
    """Extract unique companies from contacts, deduplicate by Apollo Account ID then Domain."""
    companies_by_id = {}
    companies_by_domain = {}

    for contact in contacts:
        account = contact.get("account")
        if not account:
            continue

        account_id = account.get("id")
        domain = account.get("domain")

        # Skip if no ID
        if not account_id:
            continue

        # Deduplicate by ID first
        if account_id in companies_by_id:
            continue

        # Deduplicate by domain (if we already have a company with this domain)
        if domain and domain in companies_by_domain:
            continue

        companies_by_id[account_id] = account
        if domain:
            companies_by_domain[domain] = account

    return companies_by_id


def _rt(value: str) -> dict:
    """Helper: format a string as Notion rich_text property."""
    return {"rich_text": [{"text": {"content": str(value)[:2000]}}]}


def format_company_for_notion(company: Dict) -> Dict:
    """Format Apollo company data for Notion."""
    employee_count = company.get("num_employees")
    annual_revenue = company.get("annual_revenue")

    properties = {}

    # Title (required)
    name = company.get("name", "Unknown Company")
    properties["Company Name"] = {
        "title": [{"text": {"content": name[:300]}}]
    }

    # Rich text fields
    text_mappings = {
        "Domain": company.get("domain"),
        "Company Address": company.get("raw_address"),
        "Company City": company.get("city"),
        "Company State": company.get("state"),
        "Company Country": company.get("country"),
        "Industry": company.get("industry"),
        "Keywords": ", ".join(company.get("keywords", []) or []) if company.get("keywords") else None,
        "Technologies": ", ".join(company.get("technologies", []) or []) if company.get("technologies") else None,
        "Apollo Account Id": company.get("id"),
        "Employee Size": map_employee_size(employee_count),
        "Revenue Range": map_revenue_range(annual_revenue),
        "Record Source": "Apollo",
        "Data Status": "Raw",
        "Short Description": company.get("short_description"),
        "Company Postal Code": company.get("postal_code"),
        "SIC Codes": company.get("sic_codes"),
        "NAICS Codes": company.get("naics_codes"),
        "Account Owner": company.get("owner", {}).get("name") if isinstance(company.get("owner"), dict) else None,
    }

    for prop_name, value in text_mappings.items():
        if value:
            properties[prop_name] = _rt(str(value))

    # URL fields
    url_mappings = {
        "Website": company.get("website_url"),
        "Company Linkedin Url": company.get("linkedin_url"),
        "Facebook Url": company.get("facebook_url"),
        "Twitter Url": company.get("twitter_url"),
        "Logo URL": company.get("logo_url"),
    }

    for prop_name, value in url_mappings.items():
        if value:
            properties[prop_name] = {"url": value}

    # Phone
    phone = company.get("phone")
    if phone:
        properties["Company Phone"] = {"phone_number": phone}

    # Number fields
    if employee_count:
        properties["Employees"] = {"number": employee_count}
    if annual_revenue:
        properties["Annual Revenue"] = {"number": annual_revenue}

    total_funding = company.get("total_funding")
    if total_funding:
        properties["Total Funding"] = {"number": total_funding}

    latest_funding_amount = company.get("latest_funding_amount")
    if latest_funding_amount:
        properties["Latest Funding Amount"] = {"number": latest_funding_amount}

    founded_year = company.get("founded_year")
    if founded_year:
        properties["Founded Year"] = {"number": founded_year}

    return properties


def sync_companies():
    """
    Main sync function.
    Uses pre-loading to avoid per-company API queries (much faster).
    Uses notion_helpers for rate limiting and smart retry.
    """
    logger.info("=" * 80)
    logger.info("Starting company sync from Apollo to Notion")
    logger.info("=" * 80)

    stats = {
        "created": 0,
        "updated": 0,
        "skipped": 0,
        "errors": 0
    }

    # Validate API keys
    if not APOLLO_API_KEY:
        logger.error("APOLLO_API_KEY not set in environment")
        return

    # Step 1: Pre-load existing companies from Notion (avoids per-company queries)
    logger.info("Pre-loading existing companies from Notion...")
    company_lookup = preload_companies()

    # Step 2: Fetch all contacts from Apollo
    logger.info("Fetching all contacts from Apollo...")
    contacts = fetch_all_apollo_contacts()
    logger.info(f"Fetched {len(contacts)} contacts")

    # Step 3: Extract unique companies
    logger.info("Extracting unique companies...")
    companies = extract_unique_companies(contacts)
    logger.info(f"Extracted {len(companies)} unique companies")

    # Step 4: Sync with multi-threading
    def process_company(item):
        apollo_id, company = item
        company_name = company.get("name", "Unknown")
        domain = company.get("domain")

        # Check if exists using pre-loaded lookup
        existing_page_id = company_lookup.get(f"aid:{apollo_id}")
        if not existing_page_id and domain:
            existing_page_id = company_lookup.get(f"dom:{domain}")

        company_data = format_company_for_notion(company)

        try:
            if existing_page_id:
                update_page(existing_page_id, company_data)
                return "updated", apollo_id, company_name
            else:
                page_id = create_page(NOTION_DATABASE_ID_COMPANIES, company_data)
                if page_id:
                    # Update lookup for future dedup
                    company_lookup[f"aid:{apollo_id}"] = page_id
                    if domain:
                        company_lookup[f"dom:{domain}"] = page_id
                return "created", apollo_id, company_name
        except Exception as e:
            logger.error(f"Error syncing company '{company_name}' ({apollo_id}): {e}")
            return "errors", apollo_id, company_name

    logger.info(f"Starting company sync ({MAX_WORKERS} threads)...")
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(process_company, item): item
            for item in companies.items()
        }
        for i, fut in enumerate(as_completed(futures), 1):
            status, apollo_id, company_name = fut.result()
            stats[status] = stats.get(status, 0) + 1

            if i % 50 == 0 or i == len(companies):
                logger.info(
                    f"Progress: {i}/{len(companies)} | "
                    f"Created: {stats['created']} | Updated: {stats['updated']} | "
                    f"Errors: {stats['errors']}"
                )

    # Final report
    logger.info("=" * 80)
    logger.info("Company sync completed")
    logger.info(f"Created:  {stats['created']}")
    logger.info(f"Updated:  {stats['updated']}")
    logger.info(f"Skipped:  {stats['skipped']}")
    logger.info(f"Errors:   {stats['errors']}")
    logger.info("=" * 80)


if __name__ == "__main__":
    sync_companies()
