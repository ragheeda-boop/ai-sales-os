#!/usr/bin/env python3
"""
Verify and fix Company-Contact relationships in Notion.
Identifies contacts with Apollo Account ID but no Company relation,
then links them to the correct company in Notion.
"""

import os
import sys
import logging
import requests
import time
from typing import Dict, List, Optional, Tuple
from dotenv import load_dotenv

load_dotenv()

# Configuration
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_DATABASE_ID_CONTACTS = os.getenv("NOTION_DATABASE_ID_CONTACTS", "9ca842d20aa9460bbdd958d0aa940d9c")
NOTION_DATABASE_ID_COMPANIES = os.getenv("NOTION_DATABASE_ID_COMPANIES", "331e04a62da74afe9ab6b0efead39200")

NOTION_BASE_URL = "https://api.notion.com/v1"
NOTION_API_VERSION = "2022-06-28"

# Rate limiting
NOTION_RATE_LIMIT_DELAY = 0.2  # 5 requests/second

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("verify_links.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def get_contact_property_value(properties: Dict, prop_name: str) -> Optional[str]:
    """Extract property value from Notion contact properties."""
    if prop_name not in properties:
        return None

    prop = properties[prop_name]

    if "text" in prop and prop["text"]:
        return prop["text"][0].get("text", {}).get("content") if isinstance(prop["text"], list) else prop["text"]

    if "rich_text" in prop and prop["rich_text"]:
        return prop["rich_text"][0].get("text", {}).get("content") if isinstance(prop["rich_text"], list) else None

    if "email" in prop:
        return prop["email"]

    return None


def get_contact_relation(properties: Dict, prop_name: str) -> List[str]:
    """Extract relation IDs from Notion contact properties."""
    if prop_name not in properties:
        return []

    prop = properties[prop_name]

    if "relation" in prop:
        return [item.get("id") for item in prop["relation"] if "id" in item]

    return []


def fetch_all_contacts_with_account_id() -> List[Dict]:
    """Fetch all contacts from Notion that have Apollo Account ID."""
    all_contacts = []
    cursor = None
    page_count = 0

    url = f"{NOTION_BASE_URL}/databases/{NOTION_DATABASE_ID_CONTACTS}/query"
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Notion-Version": NOTION_API_VERSION,
        "Content-Type": "application/json"
    }

    while True:
        page_count += 1
        logger.info(f"Fetching contacts page {page_count}...")

        body = {
            "filter": {
                "property": "Apollo Account Id",
                "rich_text": {
                    "is_not_empty": True
                }
            },
            "page_size": 100
        }

        if cursor:
            body["start_cursor"] = cursor

        try:
            response = requests.post(url, json=body, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()

            results = data.get("results", [])
            if not results:
                logger.info(f"No more contacts. Total fetched: {len(all_contacts)}")
                break

            all_contacts.extend(results)
            logger.info(f"Fetched {len(results)} contacts on page {page_count}. Total: {len(all_contacts)}")

            cursor = data.get("next_cursor")
            if not cursor:
                break

            time.sleep(NOTION_RATE_LIMIT_DELAY)

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching contacts page {page_count}: {e}")
            break

    return all_contacts


def find_company_by_apollo_id(apollo_account_id: str) -> Optional[str]:
    """Find company page ID by Apollo Account ID."""
    url = f"{NOTION_BASE_URL}/databases/{NOTION_DATABASE_ID_COMPANIES}/query"
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Notion-Version": NOTION_API_VERSION,
        "Content-Type": "application/json"
    }

    body = {
        "filter": {
            "property": "Apollo Account Id",
            "rich_text": {
                "equals": apollo_account_id
            }
        },
        "page_size": 1
    }

    try:
        response = requests.post(url, json=body, headers=headers, timeout=30)
        response.raise_for_status()
        results = response.json().get("results", [])
        if results:
            time.sleep(NOTION_RATE_LIMIT_DELAY)
            return results[0]["id"]
        time.sleep(NOTION_RATE_LIMIT_DELAY)
    except requests.exceptions.RequestException as e:
        logger.warning(f"Error querying Notion for company {apollo_account_id}: {e}")

    return None


def update_contact_company_relation(contact_page_id: str, company_page_id: str) -> Tuple[bool, str]:
    """Update contact with company relation."""
    url = f"{NOTION_BASE_URL}/pages/{contact_page_id}"
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Notion-Version": NOTION_API_VERSION,
        "Content-Type": "application/json"
    }

    body = {
        "properties": {
            "Company": {
                "relation": [
                    {
                        "id": company_page_id
                    }
                ]
            }
        }
    }

    try:
        response = requests.patch(url, json=body, headers=headers, timeout=30)
        response.raise_for_status()
        time.sleep(NOTION_RATE_LIMIT_DELAY)
        return True, "Linked"
    except requests.exceptions.RequestException as e:
        error_msg = f"Failed to link company: {str(e)}"
        logger.error(error_msg)
        return False, error_msg


def get_contact_name(contact: Dict) -> str:
    """Extract contact name for logging."""
    try:
        title_prop = contact.get("properties", {}).get("Full Name", {})
        if "title" in title_prop and title_prop["title"]:
            return title_prop["title"][0].get("text", {}).get("content", "Unknown")
    except Exception:
        pass
    return "Unknown"


def verify_and_fix_links():
    """Main verification and linking function."""
    logger.info("=" * 80)
    logger.info("Starting contact-company link verification")
    logger.info("=" * 80)

    stats = {
        "total_contacts": 0,
        "contacts_with_account_id": 0,
        "already_linked": 0,
        "orphans_fixed": 0,
        "orphans_not_found": 0,
        "errors": 0
    }

    # Validate API key
    if not NOTION_API_KEY:
        logger.error("NOTION_API_KEY not set in environment")
        return

    # Fetch all contacts with Apollo Account ID
    logger.info("Fetching contacts with Apollo Account ID...")
    contacts = fetch_all_contacts_with_account_id()
    logger.info(f"Fetched {len(contacts)} contacts with Apollo Account ID")

    stats["total_contacts"] = len(contacts)

    # Process each contact
    logger.info("Verifying company links...")
    for idx, contact in enumerate(contacts, 1):
        try:
            contact_id = contact.get("id")
            properties = contact.get("properties", {})
            contact_name = get_contact_name(contact)

            # Get Apollo Account ID
            apollo_account_id = get_contact_property_value(properties, "Apollo Account Id")
            if not apollo_account_id:
                logger.warning(f"[{idx}/{len(contacts)}] Contact {contact_name} missing Apollo Account ID")
                continue

            stats["contacts_with_account_id"] += 1

            # Check if company relation exists
            company_relations = get_contact_relation(properties, "Company")
            if company_relations:
                stats["already_linked"] += 1
                logger.info(f"[{idx}/{len(contacts)}] Already linked: {contact_name}")
                continue

            # Find company in Notion
            company_page_id = find_company_by_apollo_id(apollo_account_id)
            if not company_page_id:
                stats["orphans_not_found"] += 1
                logger.warning(f"[{idx}/{len(contacts)}] Orphan not found: {contact_name} (Account ID: {apollo_account_id})")
                continue

            # Link company to contact
            success, message = update_contact_company_relation(contact_id, company_page_id)
            if success:
                stats["orphans_fixed"] += 1
                logger.info(f"[{idx}/{len(contacts)}] Linked: {contact_name} (Account ID: {apollo_account_id})")
            else:
                stats["errors"] += 1
                logger.error(f"[{idx}/{len(contacts)}] Error linking {contact_name}: {message}")

            # Progress reporting
            if idx % 10 == 0:
                logger.info(f"Progress: {idx}/{len(contacts)} | Already Linked: {stats['already_linked']} | Fixed: {stats['orphans_fixed']} | Errors: {stats['errors']}")

        except Exception as e:
            stats["errors"] += 1
            logger.error(f"[{idx}/{len(contacts)}] Unexpected error: {e}")

    # Final report
    logger.info("=" * 80)
    logger.info("Link verification completed")
    logger.info(f"Total contacts:      {stats['total_contacts']}")
    logger.info(f"With Account ID:     {stats['contacts_with_account_id']}")
    logger.info(f"Already linked:      {stats['already_linked']}")
    logger.info(f"Orphans fixed:       {stats['orphans_fixed']}")
    logger.info(f"Orphans not found:   {stats['orphans_not_found']}")
    logger.info(f"Errors:              {stats['errors']}")
    logger.info("=" * 80)


if __name__ == "__main__":
    verify_and_fix_links()
