#!/usr/bin/env python3
"""
Sync contacts from Apollo to Notion.
Pulls all contacts from Apollo and syncs to Notion Contacts database.
"""

import os
import sys
import logging
import requests
import time
from typing import Dict, List, Optional, Set, Tuple
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

# Configuration
APOLLO_API_KEY = os.getenv("APOLLO_API_KEY")
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_DATABASE_ID_CONTACTS = os.getenv("NOTION_DATABASE_ID_CONTACTS", "9ca842d20aa9460bbdd958d0aa940d9c")
NOTION_DATABASE_ID_COMPANIES = os.getenv("NOTION_DATABASE_ID_COMPANIES", "331e04a62da74afe9ab6b0efead39200")

APOLLO_BASE_URL = "https://api.apollo.io/v1"
NOTION_BASE_URL = "https://api.notion.com/v1"
NOTION_API_VERSION = "2022-06-28"

# Rate limiting
NOTION_RATE_LIMIT_DELAY = 0.2  # 5 requests/second
APOLLO_RATE_LIMIT_DELAY = 0.1  # 10 requests/second

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("sync_contacts.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def map_seniority(title: Optional[str]) -> Optional[str]:
    """Map job title to seniority level."""
    if not title:
        return None

    title_lower = title.lower()

    if any(word in title_lower for word in ["ceo", "chief executive", "president", "founder", "chairman"]):
        return "C-Suite"
    elif any(word in title_lower for word in ["vp", "vice president", "executive vice president"]):
        return "VP"
    elif any(word in title_lower for word in ["director", "head of", "chief"]):
        return "Director"
    elif any(word in title_lower for word in ["manager", "lead", "supervisor"]):
        return "Manager"
    else:
        return "Individual Contributor"


def map_outreach_status(contact_campaign_statuses: List[Dict], email_unsubscribed: bool, call_opted_out: bool) -> str:
    """Map campaign statuses and opt-out flags to outreach status."""
    if email_unsubscribed or call_opted_out:
        return "Do Not Contact"

    if not contact_campaign_statuses:
        return "Not Started"

    # Check for any active campaigns
    for campaign in contact_campaign_statuses:
        status = campaign.get("status", "").lower()
        if status == "active":
            return "In Sequence"
        elif status == "finished":
            return "Completed"
        elif status == "paused":
            return "Paused"

    return "Not Started"


def map_sequence_status(contact_campaign_statuses: List[Dict]) -> str:
    """Map campaign statuses to sequence status."""
    if not contact_campaign_statuses:
        return "Not Started"

    statuses = {campaign.get("status", "").lower() for campaign in contact_campaign_statuses}

    if "active" in statuses:
        return "Active"
    elif "finished" in statuses:
        return "Completed"
    elif "paused" in statuses:
        return "Paused"
    else:
        return "Not Started"


def extract_engagement_flags(contact_campaign_statuses: List[Dict]) -> Dict[str, bool]:
    """Extract engagement flags from campaign statuses."""
    flags = {
        "email_sent": False,
        "email_opened": False,
        "replied": False,
        "email_bounced": False,
        "meeting_booked": False
    }

    for campaign in contact_campaign_statuses:
        status = campaign.get("status", "").lower()

        # If in any campaign, email was sent
        if status in ["active", "finished", "paused"]:
            flags["email_sent"] = True

        # Check for specific statuses in campaigns
        if campaign.get("stats", {}).get("opened", 0) > 0:
            flags["email_opened"] = True
        if campaign.get("stats", {}).get("replied", 0) > 0:
            flags["replied"] = True
        if campaign.get("stats", {}).get("bounced", 0) > 0:
            flags["email_bounced"] = True

    return flags


def extract_phone_numbers(phone_numbers: List[Dict]) -> Dict[str, Optional[str]]:
    """Extract phone numbers by type."""
    phones = {
        "work_direct": None,
        "mobile": None,
        "home": None,
        "corporate": None,
        "other": None
    }

    if not phone_numbers:
        return phones

    type_map = {
        "work_hq": "corporate",
        "work": "work_direct",
        "direct": "work_direct",
        "mobile": "mobile",
        "cell": "mobile",
        "home": "home",
        "other": "other"
    }

    for phone_obj in phone_numbers:
        phone_type = phone_obj.get("type", "").lower()
        sanitized = phone_obj.get("sanitized_number")

        if sanitized:
            mapped_type = type_map.get(phone_type, "other")
            if phones[mapped_type] is None:  # Use first occurrence
                phones[mapped_type] = sanitized

    return phones


def extract_primary_email(contact: Dict) -> Optional[str]:
    """Extract primary email from contact."""
    if contact.get("email"):
        return contact.get("email")

    contact_emails = contact.get("contact_emails", [])
    if contact_emails:
        return contact_emails[0].get("email")

    return None


def find_company_in_notion(apollo_account_id: Optional[str]) -> Optional[str]:
    """Find company page ID in Notion by Apollo Account ID."""
    if not apollo_account_id:
        return None

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
        }
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


def format_contact_for_notion(contact: Dict, company_page_id: Optional[str] = None) -> Dict:
    """Format Apollo contact data for Notion."""
    first_name = contact.get("first_name", "")
    last_name = contact.get("last_name", "")
    full_name = contact.get("name", f"{first_name} {last_name}".strip())
    title = contact.get("title", "")
    email = extract_primary_email(contact)
    email_status = contact.get("email_status", "")
    phones = extract_phone_numbers(contact.get("phone_numbers", []))
    engagement = extract_engagement_flags(contact.get("contact_campaign_statuses", []))
    outreach_status = map_outreach_status(
        contact.get("contact_campaign_statuses", []),
        contact.get("email_unsubscribed", False),
        contact.get("call_opted_out", False)
    )
    sequence_status = map_sequence_status(contact.get("contact_campaign_statuses", []))

    properties = {
        "Full Name": {
            "title": [
                {
                    "text": {
                        "content": full_name[:300]
                    }
                }
            ]
        },
        "First Name": {
            "rich_text": [{"text": {"content": first_name}}]
        } if first_name else None,
        "Last Name": {
            "rich_text": [{"text": {"content": last_name}}]
        } if last_name else None,
        "Email": {
            "email": email or None
        },
        "Email Status": {
            "select": {
                "name": email_status if email_status in ["verified", "unavailable"] else None
            } if email_status else None
        },
        "Title": {
            "rich_text": [{"text": {"content": title}}]
        } if title else None,
        "Seniority": {
            "select": {
                "name": map_seniority(title)
            } if title else None
        },
        "Work Direct Phone": {
            "phone_number": phones["work_direct"] or None
        },
        "Mobile Phone": {
            "phone_number": phones["mobile"] or None
        },
        "Home Phone": {
            "phone_number": phones["home"] or None
        },
        "Corporate Phone": {
            "phone_number": phones["corporate"] or None
        },
        "Other Phone": {
            "phone_number": phones["other"] or None
        },
        "City": {
            "rich_text": [{"text": {"content": contact.get("city", "")}}]
        } if contact.get("city") else None,
        "State": {
            "rich_text": [{"text": {"content": contact.get("state", "")}}]
        } if contact.get("state") else None,
        "Country": {
            "rich_text": [{"text": {"content": contact.get("country", "")}}]
        } if contact.get("country") else None,
        "Person Linkedin Url": {
            "url": contact.get("linkedin_url") or None
        },
        "Apollo Contact Id": {
            "rich_text": [{"text": {"content": contact.get("id", "")}}]
        } if contact.get("id") else None,
        "Apollo Account Id": {
            "rich_text": [{"text": {"content": contact.get("account_id", "")}}]
        } if contact.get("account_id") else None,
        "Company Name for Emails": {
            "rich_text": [{"text": {"content": contact.get("organization_name", "")}}]
        } if contact.get("organization_name") else None,
        "Email Sent": {
            "checkbox": engagement["email_sent"]
        },
        "Email Opened": {
            "checkbox": engagement["email_opened"]
        },
        "Email Bounced": {
            "checkbox": engagement["email_bounced"]
        },
        "Replied": {
            "checkbox": engagement["replied"]
        },
        "Outreach Status": {
            "select": {
                "name": outreach_status
            }
        },
        "Sequence Status": {
            "select": {
                "name": sequence_status
            }
        },
        "Record Source": {
            "select": {
                "name": "Apollo"
            }
        },
        "Data Status": {
            "select": {
                "name": "Raw"
            }
        }
    }

    # Add company relation if found
    if company_page_id:
        properties["Company"] = {
            "relation": [
                {
                    "id": company_page_id
                }
            ]
        }

    # Remove None values and empty selects
    cleaned_properties = {}
    for key, value in properties.items():
        if value is None:
            continue
        if isinstance(value, dict):
            # Handle phone_number fields
            if "phone_number" in value and value["phone_number"] is None:
                continue
            # Handle email fields
            if "email" in value and value["email"] is None:
                continue
            # Handle URL fields
            if "url" in value and value["url"] is None:
                continue
            # Handle select with None name
            if "select" in value and value["select"] is None:
                continue
            if "select" in value and value["select"].get("name") is None:
                continue
            # Handle relation fields
            if "relation" in value and value["relation"] == []:
                continue

        cleaned_properties[key] = value

    return cleaned_properties


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


def deduplicate_contacts(contacts: List[Dict]) -> Dict[str, Dict]:
    """Deduplicate contacts by Apollo Contact ID first, then by email."""
    contacts_by_id = {}
    contacts_by_email = {}

    for contact in contacts:
        contact_id = contact.get("id")
        email = extract_primary_email(contact)

        # Deduplicate by ID first
        if contact_id:
            if contact_id in contacts_by_id:
                continue
            contacts_by_id[contact_id] = contact
        # Then by email
        elif email:
            if email in contacts_by_email:
                continue
            contacts_by_email[email] = contact

    # Merge, preferring ID-based deduplication
    result = {}
    result.update(contacts_by_email)
    result.update(contacts_by_id)
    return result


def find_existing_contact(apollo_contact_id: str, email: Optional[str] = None) -> Optional[str]:
    """Find existing contact in Notion by Apollo Contact ID or email."""
    url = f"{NOTION_BASE_URL}/databases/{NOTION_DATABASE_ID_CONTACTS}/query"
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Notion-Version": NOTION_API_VERSION,
        "Content-Type": "application/json"
    }

    # Try Apollo Contact ID first
    if apollo_contact_id:
        body = {
            "filter": {
                "property": "Apollo Contact Id",
                "rich_text": {
                    "equals": apollo_contact_id
                }
            }
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
            logger.warning(f"Error querying Notion for contact {apollo_contact_id}: {e}")

    # Try email as fallback
    if email:
        body = {
            "filter": {
                "property": "Email",
                "email": {
                    "equals": email
                }
            }
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
            logger.warning(f"Error querying Notion for email {email}: {e}")

    return None


def create_contact_in_notion(contact_data: Dict) -> Tuple[bool, Optional[str], str]:
    """Create a new contact in Notion."""
    url = f"{NOTION_BASE_URL}/pages"
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Notion-Version": NOTION_API_VERSION,
        "Content-Type": "application/json"
    }

    body = {
        "parent": {
            "database_id": NOTION_DATABASE_ID_CONTACTS
        },
        "properties": contact_data
    }

    try:
        response = requests.post(url, json=body, headers=headers, timeout=30)
        response.raise_for_status()
        page_id = response.json().get("id")
        time.sleep(NOTION_RATE_LIMIT_DELAY)
        return True, page_id, "Created"
    except requests.exceptions.RequestException as e:
        error_msg = f"Failed to create contact: {str(e)}"
        logger.error(error_msg)
        return False, None, error_msg


def update_contact_in_notion(page_id: str, contact_data: Dict) -> Tuple[bool, str]:
    """Update an existing contact in Notion."""
    url = f"{NOTION_BASE_URL}/pages/{page_id}"
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Notion-Version": NOTION_API_VERSION,
        "Content-Type": "application/json"
    }

    body = {
        "properties": contact_data
    }

    try:
        response = requests.patch(url, json=body, headers=headers, timeout=30)
        response.raise_for_status()
        time.sleep(NOTION_RATE_LIMIT_DELAY)
        return True, "Updated"
    except requests.exceptions.RequestException as e:
        error_msg = f"Failed to update contact: {str(e)}"
        logger.error(error_msg)
        return False, error_msg


def sync_contacts():
    """Main sync function."""
    logger.info("=" * 80)
    logger.info("Starting contact sync from Apollo to Notion")
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
    if not NOTION_API_KEY:
        logger.error("NOTION_API_KEY not set in environment")
        return

    # Fetch all contacts
    logger.info("Fetching all contacts from Apollo...")
    contacts = fetch_all_apollo_contacts()
    logger.info(f"Fetched {len(contacts)} contacts")

    # Deduplicate contacts
    logger.info("Deduplicating contacts...")
    unique_contacts = deduplicate_contacts(contacts)
    logger.info(f"Unique contacts: {len(unique_contacts)}")

    # Sync each contact
    logger.info("Starting contact sync...")
    for idx, (contact_key, contact) in enumerate(unique_contacts.items(), 1):
        try:
            apollo_contact_id = contact.get("id", "")
            email = extract_primary_email(contact)
            full_name = contact.get("name", "Unknown")

            # Find company
            apollo_account_id = contact.get("account_id")
            company_page_id = find_company_in_notion(apollo_account_id) if apollo_account_id else None

            # Format for Notion
            contact_data = format_contact_for_notion(contact, company_page_id)

            # Check if exists
            existing_page_id = find_existing_contact(apollo_contact_id, email)

            if existing_page_id:
                # Update
                success, message = update_contact_in_notion(existing_page_id, contact_data)
                if success:
                    stats["updated"] += 1
                    logger.info(f"[{idx}/{len(unique_contacts)}] Updated: {full_name} ({apollo_contact_id})")
                else:
                    stats["errors"] += 1
                    logger.error(f"[{idx}/{len(unique_contacts)}] Error updating {full_name}: {message}")
            else:
                # Create
                success, page_id, message = create_contact_in_notion(contact_data)
                if success:
                    stats["created"] += 1
                    logger.info(f"[{idx}/{len(unique_contacts)}] Created: {full_name} ({apollo_contact_id})")
                else:
                    stats["errors"] += 1
                    logger.error(f"[{idx}/{len(unique_contacts)}] Error creating {full_name}: {message}")

            # Progress reporting
            if idx % 10 == 0:
                logger.info(f"Progress: {idx}/{len(unique_contacts)} | Created: {stats['created']} | Updated: {stats['updated']} | Errors: {stats['errors']}")

        except Exception as e:
            stats["errors"] += 1
            logger.error(f"[{idx}/{len(unique_contacts)}] Unexpected error: {e}")

    # Final report
    logger.info("=" * 80)
    logger.info("Contact sync completed")
    logger.info(f"Created:  {stats['created']}")
    logger.info(f"Updated:  {stats['updated']}")
    logger.info(f"Skipped:  {stats['skipped']}")
    logger.info(f"Errors:   {stats['errors']}")
    logger.info("=" * 80)


if __name__ == "__main__":
    sync_contacts()
