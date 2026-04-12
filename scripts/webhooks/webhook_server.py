"""
Apollo Webhook Integration Server
Phase 3: Real-time Sync from Apollo to Notion

This server listens for webhook events from Apollo and automatically
updates your Notion databases with new/updated contacts and companies.

Fixed: Field names aligned with actual Notion schema (matches daily_sync.py
and initial_load_from_csv.py). Uses notion_helpers for rate limiting and retry.
"""

import sys as _sys, os as _os; _sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
import os
import sys
import json
import logging
import hashlib
import hmac
from datetime import datetime
from typing import Dict, Optional
from dotenv import load_dotenv
from flask import Flask, request, jsonify

# Load environment variables
load_dotenv()

# Import shared helpers (rate limiter, retry, create/update/preload)
sys.path.insert(0, os.path.dirname(__file__))
from core.notion_helpers import (
    NOTION_DATABASE_ID_CONTACTS,
    NOTION_DATABASE_ID_COMPANIES,
    NOTION_BASE_URL,
    preload_companies,
    preload_contacts,
    create_page,
    update_page,
    notion_request,
)

# ============================================================================
# CONFIGURATION
# ============================================================================

APOLLO_API_KEY = os.getenv("APOLLO_API_KEY")
APOLLO_WEBHOOK_SECRET = os.getenv("APOLLO_WEBHOOK_SECRET", "")
SERVER_PORT = int(os.getenv("SERVER_PORT", 5000))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# ============================================================================
# LOGGING SETUP
# ============================================================================

os.makedirs("logs", exist_ok=True)

logger = logging.getLogger(__name__)
logger.setLevel(LOG_LEVEL)

# File Handler
_webhook_log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
os.makedirs(_webhook_log_dir, exist_ok=True)
file_handler = logging.FileHandler(os.path.join(_webhook_log_dir, "webhook_events.log"))
file_handler.setLevel(LOG_LEVEL)

# Console Handler
console_handler = logging.StreamHandler()
console_handler.setLevel(LOG_LEVEL)

# Formatter
formatter = logging.Formatter(
    "%(asctime)s - %(levelname)s - [%(funcName)s] - %(message)s"
)
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(console_handler)

# ============================================================================
# FLASK APP
# ============================================================================

app = Flask(__name__)

# ============================================================================
# IN-MEMORY LOOKUPS (pre-loaded on startup)
# ============================================================================

company_lookup: Dict[str, str] = {}
contact_lookup: Dict[str, str] = {}

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================


def verify_webhook_signature(request_body: bytes, signature: str) -> bool:
    """Verify that the webhook request came from Apollo using HMAC-SHA256."""
    if not APOLLO_WEBHOOK_SECRET:
        logger.warning("APOLLO_WEBHOOK_SECRET not set - skipping signature verification")
        return True

    expected_signature = hmac.new(
        APOLLO_WEBHOOK_SECRET.encode(),
        request_body,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(signature, expected_signature)


def _rt(value: str) -> dict:
    """Helper: build a rich_text property value (matches other sync scripts)."""
    return {"rich_text": [{"text": {"content": str(value)[:2000]}}]}


def _safe_int(val) -> Optional[int]:
    if val is None:
        return None
    try:
        return int(val)
    except (ValueError, TypeError):
        return None


def map_employee_size(count: Optional[int]) -> Optional[str]:
    if not count:
        return None
    if count <= 10:
        return "1-10"
    elif count <= 50:
        return "11-50"
    elif count <= 200:
        return "51-200"
    elif count <= 500:
        return "201-500"
    elif count <= 1000:
        return "501-1000"
    elif count <= 5000:
        return "1001-5000"
    else:
        return "5001+"


# ============================================================================
# LOOKUP HELPERS (use in-memory lookups instead of per-record API queries)
# ============================================================================


def find_contact_by_email(email: str) -> Optional[str]:
    """Find contact page_id from in-memory lookup."""
    return contact_lookup.get(f"email:{email.strip().lower()}")


def find_contact_by_apollo_id(apollo_id: str) -> Optional[str]:
    """Find contact page_id from in-memory lookup."""
    return contact_lookup.get(f"aid:{apollo_id}")


def find_company_by_apollo_id(apollo_id: str) -> Optional[str]:
    """Find company page_id from in-memory lookup."""
    return company_lookup.get(f"aid:{apollo_id}")


def find_company_by_domain(domain: str) -> Optional[str]:
    """Find company page_id from in-memory lookup."""
    return company_lookup.get(f"dom:{domain.strip().lower()}")


# ============================================================================
# FORMAT FUNCTIONS (aligned with daily_sync.py / initial_load_from_csv.py)
# ============================================================================


def format_contact_properties(contact: Dict, company_page_id: Optional[str] = None) -> Dict:
    """
    Format Apollo webhook contact data for Notion.
    Field names match the actual Notion schema used by all other sync scripts.
    """
    props = {}

    first = contact.get("first_name", "")
    last = contact.get("last_name", "")
    full = f"{first} {last}".strip() or "Unknown"

    # Title field: "Full Name" (NOT "Name")
    props["Full Name"] = {"title": [{"text": {"content": full[:300]}}]}

    # Rich text fields
    text_map = {
        "First Name": first,
        "Last Name": last,
        "Title": contact.get("title"),
        "City": contact.get("city"),
        "State": contact.get("state"),
        "Country": contact.get("country"),
        "Apollo Contact Id": contact.get("id"),
        "Apollo Account Id": contact.get("account_id"),
        "Company Name for Emails": contact.get("organization_name"),
    }
    for prop_name, value in text_map.items():
        if value and str(value).strip():
            props[prop_name] = _rt(str(value).strip())

    # Email
    email = contact.get("email")
    if email:
        props["Email"] = {"email": email}

    # LinkedIn URL
    linkedin = contact.get("linkedin_url")
    if linkedin:
        props["Person Linkedin Url"] = {"url": linkedin}

    # Seniority (select)
    seniority = contact.get("seniority")
    if seniority:
        props["Seniority"] = {"select": {"name": seniority.title()}}

    # Email Status (select)
    email_status = contact.get("email_status")
    if email_status:
        props["Email Status"] = {"select": {"name": email_status.title()}}

    # Record Source and Data Status (select)
    props["Record Source"] = {"select": {"name": "Apollo Webhook"}}
    props["Data Status"] = {"select": {"name": "Raw"}}

    # Phone numbers
    for phone_obj in (contact.get("phone_numbers") or []):
        ptype = (phone_obj.get("type") or "").lower()
        number = phone_obj.get("sanitized_number")
        if not number:
            continue
        type_map = {
            "work_hq": "Corporate Phone",
            "work": "Work Direct Phone",
            "direct": "Work Direct Phone",
            "mobile": "Mobile Phone",
            "cell": "Mobile Phone",
            "home": "Home Phone",
        }
        prop_name = type_map.get(ptype, "Other Phone")
        if prop_name not in props:
            props[prop_name] = {"phone_number": number}

    # Fallback: if no typed phones but a direct phone_number field exists
    if not any(k.endswith("Phone") for k in props):
        phone = contact.get("phone_number") or contact.get("phone")
        if phone:
            props["Mobile Phone"] = {"phone_number": phone}

    # Company relation
    if company_page_id:
        props["Company"] = {"relation": [{"id": company_page_id}]}

    return props


def format_company_properties(company: Dict) -> Dict:
    """
    Format Apollo webhook company/account data for Notion.
    Field names match the actual Notion schema used by all other sync scripts.
    """
    props = {}

    name = company.get("name", "Unknown Company")
    props["Company Name"] = {"title": [{"text": {"content": name[:300]}}]}

    # Rich text fields (NOT url, NOT select — matches actual schema)
    text_map = {
        "Domain": company.get("domain"),
        "Company Address": company.get("raw_address"),
        "Company City": company.get("city"),
        "Company State": company.get("state"),
        "Company Country": company.get("country"),
        "Industry": company.get("industry"),
        "Keywords": ", ".join(company.get("keywords") or []),
        "Technologies": ", ".join(company.get("technologies") or []),
        "Apollo Account Id": company.get("id"),
        "Short Description": company.get("short_description"),
        "Record Source": "Apollo Webhook",
        "Data Status": "Raw",
    }
    for prop_name, value in text_map.items():
        if value and str(value).strip():
            props[prop_name] = _rt(str(value).strip())

    # URL fields
    url_map = {
        "Website": company.get("website_url"),
        "Company Linkedin Url": company.get("linkedin_url"),
        "Facebook Url": company.get("facebook_url"),
        "Twitter Url": company.get("twitter_url"),
    }
    for prop_name, value in url_map.items():
        if value:
            props[prop_name] = {"url": value}

    # Phone
    phone = company.get("phone")
    if phone:
        props["Company Phone"] = {"phone_number": phone}

    # Employees (number + size range)
    emp = _safe_int(company.get("num_employees"))
    if emp:
        props["Employees"] = {"number": emp}
        es = map_employee_size(emp)
        if es:
            props["Employee Size"] = _rt(es)

    # Revenue & Funding
    rev = company.get("annual_revenue")
    if rev:
        props["Annual Revenue"] = {"number": rev}

    funding = company.get("total_funding")
    if funding:
        props["Total Funding"] = {"number": funding}

    return props


# ============================================================================
# EVENT HANDLERS
# ============================================================================


def handle_contact_event(event_data: Dict, event_type: str) -> bool:
    """Handle contact.created or contact.updated events."""
    global contact_lookup

    try:
        contact = event_data.get("data", {})

        email = contact.get("email", "")
        apollo_id = contact.get("id", "")

        if not email and not apollo_id:
            logger.warning("Contact event missing both email and apollo_id - skipping")
            return False

        # Look up by Apollo ID first, then email (matches daily_sync logic)
        existing_page_id = None
        if apollo_id:
            existing_page_id = find_contact_by_apollo_id(apollo_id)
        if not existing_page_id and email:
            existing_page_id = find_contact_by_email(email)

        # Find company for relation
        account_id = contact.get("account_id", "")
        company_page_id = find_company_by_apollo_id(account_id) if account_id else None

        props = format_contact_properties(contact, company_page_id)

        if existing_page_id:
            logger.info(f"Updating contact: {contact.get('first_name', '')} {contact.get('last_name', '')} ({email})")
            update_page(existing_page_id, props)
            return True
        else:
            logger.info(f"Creating new contact: {contact.get('first_name', '')} {contact.get('last_name', '')} ({email})")
            page_id = create_page(NOTION_DATABASE_ID_CONTACTS, props)
            if page_id:
                # Update in-memory lookup
                if apollo_id:
                    contact_lookup[f"aid:{apollo_id}"] = page_id
                if email:
                    contact_lookup[f"email:{email.strip().lower()}"] = page_id
            return page_id is not None

    except Exception as e:
        logger.error(f"Error handling contact event: {str(e)}")
        return False


def handle_company_event(event_data: Dict, event_type: str) -> bool:
    """Handle company.created or company.updated events."""
    global company_lookup

    try:
        company = event_data.get("data", {})

        domain = company.get("domain", "")
        name = company.get("name", "")
        apollo_id = company.get("id", "")

        if not name:
            logger.warning("Company event missing name - skipping")
            return False

        # Look up by Apollo ID first, then domain
        existing_page_id = None
        if apollo_id:
            existing_page_id = find_company_by_apollo_id(apollo_id)
        if not existing_page_id and domain:
            existing_page_id = find_company_by_domain(domain)

        props = format_company_properties(company)

        if existing_page_id:
            logger.info(f"Updating company: {name}")
            update_page(existing_page_id, props)
            return True
        else:
            logger.info(f"Creating new company: {name}")
            page_id = create_page(NOTION_DATABASE_ID_COMPANIES, props)
            if page_id:
                # Update in-memory lookup
                if apollo_id:
                    company_lookup[f"aid:{apollo_id}"] = page_id
                if domain:
                    company_lookup[f"dom:{domain.strip().lower()}"] = page_id
            return page_id is not None

    except Exception as e:
        logger.error(f"Error handling company event: {str(e)}")
        return False


# ============================================================================
# ROUTES
# ============================================================================


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0",
        "contacts_loaded": len(contact_lookup),
        "companies_loaded": len(company_lookup),
    }), 200


@app.route("/webhook", methods=["POST"])
def webhook_listener():
    """
    Main webhook listener endpoint.
    Receives events from Apollo and syncs to Notion.
    """
    try:
        request_body = request.get_data()
        event_data = request.get_json()

        # Verify signature (optional, but recommended)
        signature = request.headers.get("X-Webhook-Signature", "")
        if signature and not verify_webhook_signature(request_body, signature):
            logger.error("Invalid webhook signature")
            return jsonify({"error": "Invalid signature"}), 401

        event_type = event_data.get("type", "unknown")
        logger.info(f"Webhook received: {event_type}")
        logger.debug(f"Event data: {json.dumps(event_data, indent=2)}")

        # Process based on event type
        success = False

        if event_type in ("contact.created", "contact.updated"):
            success = handle_contact_event(event_data, event_type)

        elif event_type in ("company.created", "company.updated"):
            success = handle_company_event(event_data, event_type)

        else:
            logger.warning(f"Unknown event type: {event_type}")

        if success:
            return jsonify({
                "status": "processed",
                "event_type": event_type,
                "timestamp": datetime.now().isoformat()
            }), 200
        else:
            return jsonify({
                "status": "error",
                "event_type": event_type,
                "timestamp": datetime.now().isoformat()
            }), 400

    except Exception as e:
        logger.error(f"Webhook handler error: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/reload", methods=["POST"])
def reload_lookups():
    """Force reload in-memory lookups from Notion (useful after manual edits)."""
    global company_lookup, contact_lookup
    try:
        logger.info("Reloading lookups from Notion...")
        company_lookup = preload_companies()
        contact_lookup = preload_contacts()
        return jsonify({
            "status": "reloaded",
            "companies": len(company_lookup),
            "contacts": len(contact_lookup),
        }), 200
    except Exception as e:
        logger.error(f"Error reloading lookups: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/status", methods=["GET"])
def get_status():
    """Get current status and configuration."""
    return jsonify({
        "status": "running",
        "apollo_key_configured": bool(APOLLO_API_KEY),
        "contacts_db": bool(NOTION_DATABASE_ID_CONTACTS),
        "companies_db": bool(NOTION_DATABASE_ID_COMPANIES),
        "contacts_loaded": len(contact_lookup),
        "companies_loaded": len(company_lookup),
        "timestamp": datetime.now().isoformat()
    }), 200


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("Apollo Webhook Server v2.0 Starting...")
    logger.info("=" * 60)

    # Validate configuration
    if not os.getenv("NOTION_API_KEY"):
        logger.error("NOTION_API_KEY not set in .env")
        exit(1)

    if not APOLLO_API_KEY:
        logger.error("APOLLO_API_KEY not set in .env")
        exit(1)

    if not NOTION_DATABASE_ID_CONTACTS:
        logger.error("NOTION_DATABASE_ID_CONTACTS not set in .env")
        exit(1)

    if not NOTION_DATABASE_ID_COMPANIES:
        logger.error("NOTION_DATABASE_ID_COMPANIES not set in .env")
        exit(1)

    # Pre-load existing data into memory (same pattern as daily_sync.py)
    logger.info("Pre-loading Notion data into memory...")
    company_lookup = preload_companies()
    contact_lookup = preload_contacts()

    logger.info(f"Configuration validated")
    logger.info(f"Server listening on 0.0.0.0:{SERVER_PORT}")
    logger.info(f"Webhook endpoint: http://YOUR_IP:{SERVER_PORT}/webhook")
    logger.info(f"Reload endpoint: POST http://YOUR_IP:{SERVER_PORT}/reload")
    logger.info("=" * 60)

    app.run(
        host="0.0.0.0",
        port=SERVER_PORT,
        debug=(LOG_LEVEL == "DEBUG"),
        use_reloader=False
    )
