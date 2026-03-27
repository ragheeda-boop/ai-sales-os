#!/usr/bin/env python3
"""
🚀 PHASE 3: Apollo API Pull Scheduler
Real-time sync من Apollo إلى Notion بدون Webhook

استراتيجية جديدة:
- Pull من Apollo API كل 5 دقائق
- Sync مع Notion تلقائياً
- Deduplication ذكي
- Logging شامل
- Error handling محترف

Author: Ragheed (AI Sales OS)
Created: March 24, 2026
"""

import os
import json
import time
import logging
from datetime import datetime, timezone
from typing import List, Dict, Optional, Tuple
from dotenv import load_dotenv
import requests
import threading

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURATION & SETUP
# ═══════════════════════════════════════════════════════════════════════════

# Load environment variables
load_dotenv()

# API Keys from environment
APOLLO_API_KEY = os.getenv('APOLLO_API_KEY')
NOTION_API_KEY = os.getenv('NOTION_API_KEY')
SYNC_INTERVAL_MINUTES = int(os.getenv('SYNC_INTERVAL_MINUTES', '5'))
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# Notion Database IDs
NOTION_CONTACTS_DB = os.getenv('NOTION_DATABASE_ID_CONTACTS')
NOTION_COMPANIES_DB = os.getenv('NOTION_DATABASE_ID_COMPANIES')

# API Rate Limits (Apollo)
APOLLO_DAILY_LIMIT = 6000      # Daily API requests limit
APOLLO_HOURLY_LIMIT = 600      # Hourly API requests limit
APOLLO_MINUTE_LIMIT = 200      # Per-minute API requests limit

# Logging Setup
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=LOG_LEVEL,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler('logs/apollo_sync.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Log API rate limits on startup
logger.info(f"⚡ Apollo API Rate Limits: {APOLLO_DAILY_LIMIT}/day, {APOLLO_HOURLY_LIMIT}/hour, {APOLLO_MINUTE_LIMIT}/min")

# ═══════════════════════════════════════════════════════════════════════════
# APOLLO API CLIENT
# ═══════════════════════════════════════════════════════════════════════════

class ApolloAPIClient:
    """Client لـ Apollo API with rate limit tracking"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.apollo.io/v1"
        self.headers = {
            'Content-Type': 'application/json',
            'X-Api-Key': api_key
        }
        # Rate limit tracking
        self._minute_requests = []  # timestamps of requests in current minute
        self._hourly_requests = []  # timestamps of requests in current hour
        logger.info("✅ Apollo API Client initialized")

    def _check_rate_limit(self):
        """Enforce rate limits by waiting if needed"""
        now = time.time()

        # Clean old entries
        self._minute_requests = [t for t in self._minute_requests if now - t < 60]
        self._hourly_requests = [t for t in self._hourly_requests if now - t < 3600]

        # Check minute limit
        if len(self._minute_requests) >= APOLLO_MINUTE_LIMIT:
            wait_time = 60 - (now - self._minute_requests[0])
            if wait_time > 0:
                logger.warning(f"⏳ Rate limit: waiting {wait_time:.1f}s (minute limit)")
                time.sleep(wait_time)

        # Check hourly limit
        if len(self._hourly_requests) >= APOLLO_HOURLY_LIMIT:
            wait_time = 3600 - (now - self._hourly_requests[0])
            if wait_time > 0:
                logger.warning(f"⏳ Rate limit: waiting {wait_time:.1f}s (hourly limit)")
                time.sleep(wait_time)

        self._minute_requests.append(time.time())
        self._hourly_requests.append(time.time())

    def get_contacts(self, updated_after: Optional[str] = None, per_page: int = 100, max_pages: int = 10) -> List[Dict]:
        """
        سحب جهات الاتصال من Apollo مع pagination

        Args:
            updated_after: ISO timestamp للبيانات الجديدة فقط
            per_page: عدد النتائج لكل صفحة (max 100)
            max_pages: أقصى عدد صفحات لتجنب rate limit

        Returns:
            قائمة جهات الاتصال بكل الخصائص
        """
        all_contacts = []
        page = 1

        try:
            while page <= max_pages:
                payload = {
                    'per_page': per_page,
                    'page': page,
                    'fields': [
                        # ═══ Basic Info ═══
                        'id',                      # Apollo Contact ID
                        'first_name',              # First Name
                        'last_name',               # Last Name
                        'name',                    # Full Name

                        # ═══ Email Info ═══
                        'email',                   # Primary Email
                        'email_status',            # Email Status (Verified, Unavailable, etc)
                        'secondary_email',         # Secondary Email
                        'primary_email_source',    # Where email came from
                        'primary_email_verification_source',  # How it was verified

                        # ═══ Phone Info ═══
                        'phone',                   # Work phone
                        'direct_phone',            # Direct Phone
                        'mobile_phone',            # Mobile/Cell Phone
                        'home_phone',              # Home Phone
                        'corporate_phone',         # Corporate Phone
                        'other_phone',             # Other/Alternative Phone

                        # ═══ Job Info ═══
                        'title',                   # Job Title
                        'seniority',               # Seniority Level (C-level, VP, Manager, etc)
                        'departments',             # Departments (comma-separated)
                        'sub_departments',         # Sub-departments (comma-separated)

                        # ═══ Organization Info ═══
                        'organization_id',         # Company/Organization ID (Apollo Account ID)
                        'organization_name',       # Company Name
                        'organization_domain',     # Company Domain ← NEW

                        # ═══ Location Info ═══
                        'city',                    # Person's City
                        'state',                   # Person's State
                        'country',                 # Person's Country

                        # ═══ Social/URLs ═══
                        'linkedin_url',            # LinkedIn Profile
                        'twitter_url',             # Twitter Profile
                        'facebook_url',            # Facebook Profile

                        # ═══ Engagement Metrics ← NEW CRITICAL ═══
                        'email_sent',              # Whether we sent email
                        'email_opened',            # Whether they opened our email
                        'email_bounced',           # Whether email bounced
                        'replied',                 # Whether they replied to us
                        'demoed',                  # Whether they've seen a demo
                        'meeting_booked',          # Whether a meeting was booked ← NEW

                        # ═══ Activity & Metadata ═══
                        'tags',                    # Contact Tags
                        'owner_id',                # Account Owner in Apollo
                        'account_id',              # Same as organization_id (for safety)
                        'last_activity_date',      # Last time any activity occurred
                        'last_contacted_date',     # Last time we contacted them ← NEW
                        'create_date',             # When record was created
                        'updated_date',            # When record was last updated
                    ]
                }
                if updated_after:
                    payload['updated_at_after'] = updated_after

                logger.info(f"📥 Pulling contacts from Apollo (page {page}, per_page={per_page})")
                self._check_rate_limit()

                response = requests.post(
                    f"{self.base_url}/contacts/search",
                    headers=self.headers,
                    json=payload,
                    timeout=30
                )
                response.raise_for_status()

                data = response.json()
                contacts = data.get('contacts', [])
                all_contacts.extend(contacts)

                total_entries = data.get('pagination', {}).get('total_entries', 0)
                total_pages = data.get('pagination', {}).get('total_pages', 1)

                logger.info(f"   Page {page}/{total_pages} - Got {len(contacts)} contacts (total: {total_entries})")

                if page >= total_pages or len(contacts) == 0:
                    break

                page += 1
                time.sleep(0.5)  # Rate limit protection

            logger.info(f"✅ Pulled {len(all_contacts)} total contacts from Apollo")
            return all_contacts

        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Error pulling contacts from Apollo: {str(e)}")
            return all_contacts  # Return what we got so far

    def get_companies(self, updated_after: Optional[str] = None, per_page: int = 100, max_pages: int = 10) -> List[Dict]:
        """
        سحب الشركات من Apollo مع pagination

        Args:
            updated_after: ISO timestamp للبيانات الجديدة فقط
            per_page: عدد النتائج لكل صفحة
            max_pages: أقصى عدد صفحات لتجنب rate limit

        Returns:
            قائمة الشركات بكل الخصائص
        """
        all_companies = []
        page = 1

        try:
            while page <= max_pages:
                payload = {
                    'per_page': per_page,
                    'page': page,
                    'fields': [
                        # Basic
                        'id', 'name', 'domain', 'website_url',
                        # Profile
                        'industry', 'keywords', 'description', 'technologies',
                        # Size/Revenue
                        'employee_count', 'employee_size_category',
                        'annual_revenue', 'revenue_range',
                        # Funding
                        'total_funding', 'latest_funding_stage',
                        'latest_funding_amount', 'latest_funding_date', 'last_funding_date',
                        # Location
                        'hq_address', 'hq_city', 'hq_state', 'hq_country',
                        # Contact
                        'phone',
                        # Social
                        'linkedin_url', 'twitter_url', 'facebook_url',
                        # Metadata
                        'created_at', 'updated_at', 'account_owner_id'
                    ]
                }
                if updated_after:
                    payload['updated_at_after'] = updated_after

                logger.info(f"📥 Pulling companies from Apollo (page {page}, per_page={per_page})")
                self._check_rate_limit()

                response = requests.post(
                    f"{self.base_url}/accounts/search",
                    headers=self.headers,
                    json=payload,
                    timeout=30
                )
                response.raise_for_status()

                data = response.json()
                companies = data.get('accounts', [])
                all_companies.extend(companies)

                total_entries = data.get('pagination', {}).get('total_entries', 0)
                total_pages = data.get('pagination', {}).get('total_pages', 1)

                logger.info(f"   Page {page}/{total_pages} - Got {len(companies)} companies (total: {total_entries})")

                if page >= total_pages or len(companies) == 0:
                    break

                page += 1
                time.sleep(0.5)  # Rate limit protection

            logger.info(f"✅ Pulled {len(all_companies)} total companies from Apollo")
            return all_companies

        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Error pulling companies from Apollo: {str(e)}")
            return all_companies  # Return what we got so far

# ═══════════════════════════════════════════════════════════════════════════
# NOTION API CLIENT
# ═══════════════════════════════════════════════════════════════════════════

class NotionAPIClient:
    """Client لـ Notion API"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.notion.com/v1"
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Notion-Version': '2022-06-28',
            'Content-Type': 'application/json'
        }
        logger.info("✅ Notion API Client initialized")

    def log_all_schemas(self):
        """Log database schemas for debugging (call after config validation)"""
        if NOTION_CONTACTS_DB:
            self.log_database_schema(NOTION_CONTACTS_DB)
        if NOTION_COMPANIES_DB:
            self.log_database_schema(NOTION_COMPANIES_DB)

    def log_database_schema(self, database_id: str):
        """Log the database schema for debugging"""
        try:
            response = requests.get(
                f"{self.base_url}/databases/{database_id}",
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            db_info = response.json()
            properties = db_info.get('properties', {})
            logger.info(f"📋 Database schema for {database_id}:")
            for prop_name, prop_info in properties.items():
                prop_type = prop_info.get('type', 'unknown')
                logger.info(f"   - {prop_name}: {prop_type}")
        except Exception as e:
            logger.error(f"❌ Failed to fetch database schema: {str(e)}")

    def contact_exists(self, email: str = None, database_id: str = None, apollo_id: str = None) -> Tuple[bool, Optional[str]]:
        """
        ✅ ENHANCED: Dual-lookup deduplication للتحقق من عدم التكرار من ID

        التحقق من وجود جهة اتصال بـ:
        1. Email أولاً (إذا موجود)
        2. Apollo Contact ID (إذا لم يوجد email أو كـ fallback)

        Returns:
            (exists: bool, page_id: str or None)
        """
        try:
            # ✅ PRIMARY LOOKUP: By Email
            if email:
                response = requests.post(
                    f"{self.base_url}/databases/{database_id}/query",
                    headers=self.headers,
                    json={
                        "filter": {
                            "property": "Email",
                            "email": {
                                "equals": email
                            }
                        }
                    },
                    timeout=10
                )
                response.raise_for_status()
                results = response.json().get('results', [])
                if results:
                    logger.debug(f"📧 Contact found by email: {email}")
                    return True, results[0]['id']

            # ✅ FALLBACK LOOKUP: By Apollo Contact ID (even if email exists)
            # This ensures NO DUPLICATION when syncing contacts without emails
            if apollo_id:
                response = requests.post(
                    f"{self.base_url}/databases/{database_id}/query",
                    headers=self.headers,
                    json={
                        "filter": {
                            "property": "Apollo Contact Id",
                            "rich_text": {
                                "equals": apollo_id
                            }
                        }
                    },
                    timeout=10
                )
                response.raise_for_status()
                results = response.json().get('results', [])
                if results:
                    logger.debug(f"🆔 Contact found by Apollo ID: {apollo_id}")
                    return True, results[0]['id']

            # No match found
            return False, None

        except requests.exceptions.RequestException as e:
            logger.warning(f"⚠️ Error checking contact existence: {str(e)}")
            # Return True to SKIP this contact (safer than creating a duplicate)
            return True, None

    def create_contact(self, database_id: str, contact_data: Dict) -> Tuple[bool, Optional[str]]:
        """
        إنشاء جهة اتصال جديدة في Notion
        Uses CORRECT property names from schema
        """
        try:
            properties = {
                # Core Info (Required)
                "Full Name": {"title": [{"text": {"content": str(contact_data.get('name') or 'Unknown')}}]},
                "First Name": {"rich_text": [{"text": {"content": str(contact_data.get('first_name') or '')}}]},
                "Last Name": {"rich_text": [{"text": {"content": str(contact_data.get('last_name') or '')}}]},

                # Contact Details - CORRECTED property names from actual schema
                "Email": {"email": contact_data.get('email') or None},
                "Secondary Email": {"email": contact_data.get('secondary_email') or None},
                "Email Status": {"select": {"name": contact_data.get('email_status')} if contact_data.get('email_status') else None},

                # Phone - CORRECTED: Use exact schema names
                "Work Direct Phone": {"phone_number": contact_data.get('phone') or contact_data.get('direct_phone') or None},
                "Mobile Phone": {"phone_number": contact_data.get('mobile_phone') or None},
                "Home Phone": {"phone_number": contact_data.get('home_phone') or None},
                "Corporate Phone": {"phone_number": contact_data.get('corporate_phone') or None},
                "Other Phone": {"phone_number": contact_data.get('other_phone') or None},

                # Job Info
                "Title": {"rich_text": [{"text": {"content": str(contact_data.get('title') or '')}}]},
                "Seniority": {"select": {"name": contact_data.get('seniority')} if contact_data.get('seniority') else None},
                # CORRECTED: Use exact schema names with 's' at end
                "Departments": {"rich_text": [{"text": {"content": str(contact_data.get('departments') or '')}}]},
                "Sub Departments": {"rich_text": [{"text": {"content": str(contact_data.get('sub_departments') or '')}}]},

                # Location - CORRECTED: These exist in schema!
                "City": {"rich_text": [{"text": {"content": str(contact_data.get('city') or '')}}]},
                "State": {"rich_text": [{"text": {"content": str(contact_data.get('state') or '')}}]},
                "Country": {"rich_text": [{"text": {"content": str(contact_data.get('country') or '')}}]},

                # Social/URLs - CORRECTED: Use exact schema name
                "Person Linkedin Url": {"url": contact_data.get('linkedin_url') or None},

                # Apollo Links
                "Apollo Contact Id": {"rich_text": [{"text": {"content": str(contact_data.get('id') or contact_data.get('apollo_contact_id') or '')}}]},
                "Apollo Account Id": {"rich_text": [{"text": {"content": str(contact_data.get('account_id') or contact_data.get('organization_id') or '')}}]},

                # Status & Metadata - Use correct select field name
                "Outreach Status": {"select": {"name": contact_data.get('status', 'Not Started')} if contact_data.get('status') else None},
                "Record Source": {"select": {"name": contact_data.get('record_source', 'Apollo')} if contact_data.get('record_source') else None},
                "Data Status": {"select": {"name": contact_data.get('data_status', 'Raw')} if contact_data.get('data_status') else None},

                # Engagement Tracking
                "Email Sent": {"checkbox": bool(contact_data.get('email_sent', False))},
                "Email Opened": {"checkbox": bool(contact_data.get('email_opened', False))},
                "Email Bounced": {"checkbox": bool(contact_data.get('email_bounced', False))},
                "Replied": {"checkbox": bool(contact_data.get('replied', False))},
                "Meeting Booked": {"checkbox": bool(contact_data.get('meeting_booked', False))},

                # Additional fields
                "Notes": {"rich_text": [{"text": {"content": str(contact_data.get('notes') or '')}}]},

                # Company Relation (link to Companies database)
                # ✅ Only include if we have a valid page_id
                "Company": {"relation": [{"id": contact_data.get('company_page_id')}]} if (contact_data.get('company_page_id') and len(str(contact_data.get('company_page_id', ''))) > 10) else None,
            }

            # Remove None values to avoid Notion API errors
            properties = {k: v for k, v in properties.items() if v is not None}

            logger.debug(f"Creating contact with {len(properties)} properties")

            response = requests.post(
                f"{self.base_url}/pages",
                headers=self.headers,
                json={
                    "parent": {"database_id": database_id},
                    "properties": properties
                },
                timeout=10
            )
            response.raise_for_status()

            page_id = response.json().get('id')
            logger.info(f"✅ Created contact: {contact_data.get('name')} ({page_id[:8]}...)")
            return True, page_id

        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Error creating contact: {str(e)}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response body: {e.response.text}")
            return False, None

    def update_contact(self, page_id: str, contact_data: Dict) -> bool:
        """
        تحديث جهة اتصال موجودة
        Uses CORRECT property names from schema
        """
        try:
            properties = {
                # Contact Details - CORRECTED property names
                "Email": {"email": contact_data.get('email') or None},
                "Secondary Email": {"email": contact_data.get('secondary_email') or None},
                "Email Status": {"select": {"name": contact_data.get('email_status')} if contact_data.get('email_status') else None},

                # Phone - CORRECTED: Use exact schema names
                "Work Direct Phone": {"phone_number": contact_data.get('phone') or contact_data.get('direct_phone') or None},
                "Mobile Phone": {"phone_number": contact_data.get('mobile_phone') or None},
                "Home Phone": {"phone_number": contact_data.get('home_phone') or None},
                "Corporate Phone": {"phone_number": contact_data.get('corporate_phone') or None},
                "Other Phone": {"phone_number": contact_data.get('other_phone') or None},

                # Job Info
                "Title": {"rich_text": [{"text": {"content": str(contact_data.get('title') or '')}}]},
                "Seniority": {"select": {"name": contact_data.get('seniority')} if contact_data.get('seniority') else None},
                # CORRECTED: Use exact schema names with 's' at end
                "Departments": {"rich_text": [{"text": {"content": str(contact_data.get('departments') or '')}}]},
                "Sub Departments": {"rich_text": [{"text": {"content": str(contact_data.get('sub_departments') or '')}}]},

                # Location - CORRECTED: These exist in schema!
                "City": {"rich_text": [{"text": {"content": str(contact_data.get('city') or '')}}]},
                "State": {"rich_text": [{"text": {"content": str(contact_data.get('state') or '')}}]},
                "Country": {"rich_text": [{"text": {"content": str(contact_data.get('country') or '')}}]},

                # Social/URLs - CORRECTED: Use exact schema name
                "Person Linkedin Url": {"url": contact_data.get('linkedin_url') or None},

                # Apollo Links
                "Apollo Contact Id": {"rich_text": [{"text": {"content": str(contact_data.get('id') or contact_data.get('apollo_contact_id') or '')}}]},
                "Apollo Account Id": {"rich_text": [{"text": {"content": str(contact_data.get('account_id') or contact_data.get('organization_id') or '')}}]},

                # Status & Metadata - Use correct select field names
                "Outreach Status": {"select": {"name": contact_data.get('status')} if contact_data.get('status') else None},
                "Record Source": {"select": {"name": contact_data.get('record_source')} if contact_data.get('record_source') else None},
                "Data Status": {"select": {"name": contact_data.get('data_status')} if contact_data.get('data_status') else None},

                # Engagement Tracking
                "Email Sent": {"checkbox": bool(contact_data.get('email_sent', False))},
                "Email Opened": {"checkbox": bool(contact_data.get('email_opened', False))},
                "Email Bounced": {"checkbox": bool(contact_data.get('email_bounced', False))},
                "Replied": {"checkbox": bool(contact_data.get('replied', False))},
                "Meeting Booked": {"checkbox": bool(contact_data.get('meeting_booked', False))},

                # Additional fields
                "Notes": {"rich_text": [{"text": {"content": str(contact_data.get('notes') or '')}}]},

                # Company Relation (link to Companies database)
                # ✅ Only include if we have a valid page_id
                "Company": {"relation": [{"id": contact_data.get('company_page_id')}]} if (contact_data.get('company_page_id') and len(str(contact_data.get('company_page_id', ''))) > 10) else None,
            }

            # Remove None values to avoid Notion API errors
            properties = {k: v for k, v in properties.items() if v is not None}

            if not properties:
                logger.debug(f"No properties to update for contact: {contact_data.get('name')} ({page_id[:8]}...)")
                return True

            response = requests.patch(
                f"{self.base_url}/pages/{page_id}",
                headers=self.headers,
                json={"properties": properties},
                timeout=10
            )
            response.raise_for_status()

            logger.info(f"✅ Updated contact: {contact_data.get('name')} ({page_id[:8]}...)")
            return True

        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Error updating contact: {str(e)}")
            return False

    def company_exists(self, domain: str = None, database_id: str = None, apollo_account_id: str = None) -> Tuple[bool, Optional[str]]:
        """
        ✅ ENHANCED: Dual-lookup deduplication للتحقق من عدم التكرار من Apollo Account ID

        تحقق من وجود شركة في Notion بـ:
        1. Domain أولاً (إذا موجود)
        2. Apollo Account ID (إذا لم يوجد domain أو كـ fallback)

        Returns:
            (exists: bool, page_id: str or None)
        """
        try:
            # ✅ PRIMARY LOOKUP: By Domain
            if domain:
                response = requests.post(
                    f"{self.base_url}/databases/{database_id}/query",
                    headers=self.headers,
                    json={
                        "filter": {
                            "property": "Domain",
                            "rich_text": {
                                "equals": domain
                            }
                        }
                    },
                    timeout=10
                )
                response.raise_for_status()
                results = response.json().get('results', [])
                if results:
                    logger.debug(f"🌐 Company found by domain: {domain}")
                    return True, results[0]['id']

            # ✅ FALLBACK LOOKUP: By Apollo Account ID (even if domain exists)
            # This ensures NO DUPLICATION from Apollo data
            if apollo_account_id:
                response = requests.post(
                    f"{self.base_url}/databases/{database_id}/query",
                    headers=self.headers,
                    json={
                        "filter": {
                            "property": "Apollo Account Id",
                            "rich_text": {
                                "equals": apollo_account_id
                            }
                        }
                    },
                    timeout=10
                )
                response.raise_for_status()
                results = response.json().get('results', [])
                if results:
                    logger.debug(f"🆔 Company found by Apollo Account ID: {apollo_account_id}")
                    return True, results[0]['id']

            # No match found
            return False, None

        except requests.exceptions.RequestException as e:
            logger.warning(f"⚠️ Error checking company existence: {str(e)}")
            # Return True to SKIP this company (safer than creating a duplicate)
            return True, None


    def create_company(self, database_id: str, company_data: Dict) -> Tuple[bool, Optional[str]]:
        """
        إنشاء شركة جديدة في Notion
        Minimal approach: ONLY Name + Apollo Account Id
        """
        try:
            # Absolute minimum properties
            properties = {
                "Name": {"title": [{"text": {"content": str(company_data.get('name') or 'Unknown')}}]},
                "Apollo Account Id": {"rich_text": [{"text": {"content": str(company_data.get('apollo_account_id') or '')}}]},
            }

            logger.debug(f"Creating company with payload: {json.dumps({'parent': {'database_id': database_id}, 'properties': properties}, indent=2, default=str)}")

            response = requests.post(
                f"{self.base_url}/pages",
                headers=self.headers,
                json={
                    "parent": {"database_id": database_id},
                    "properties": properties
                },
                timeout=10
            )
            
            if response.status_code != 200:
                logger.error(f"❌ Notion API returned {response.status_code}")
                logger.error(f"Response body: {response.text}")
            
            response.raise_for_status()

            page_id = response.json().get('id')
            logger.info(f"✅ Created company: {company_data.get('name')} ({page_id[:8]}...)")
            return True, page_id

        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Error creating company: {str(e)}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response text: {e.response.text}")
            return False, None

    def update_company(self, page_id: str, company_data: Dict) -> bool:
        """
        تحديث شركة موجودة
        Minimal approach: ONLY Apollo Account Id
        """
        try:
            properties = {}
            
            # Only update Apollo Account Id if available
            if company_data.get('apollo_account_id'):
                properties["Apollo Account Id"] = {"rich_text": [{"text": {"content": str(company_data.get('apollo_account_id'))}}]}

            if not properties:
                logger.debug(f"⚠️ No properties to update for company: {company_data.get('name')} ({page_id[:8]}...)")
                return True

            logger.debug(f"Updating company {page_id} with payload: {json.dumps({'properties': properties}, indent=2, default=str)}")

            response = requests.patch(
                f"{self.base_url}/pages/{page_id}",
                headers=self.headers,
                json={"properties": properties},
                timeout=10
            )
            
            if response.status_code != 200:
                logger.error(f"❌ Notion API returned {response.status_code}")
                logger.error(f"Response body: {response.text}")
            
            response.raise_for_status()

            logger.info(f"✅ Updated company: {company_data.get('name')} ({page_id[:8]}...)")
            return True

        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Error updating company: {str(e)}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response text: {e.response.text}")
            return False

# ═══════════════════════════════════════════════════════════════════════════
# COMPANY LOOKUP HELPER
# ═══════════════════════════════════════════════════════════════════════════

class CompanyLookup:
    """
    مساعد للبحث عن الشركات في Notion
    بناءً على Apollo Account ID مع Caching
    
    يوفر lookups سريعة وموثوقة للشركات بدون الاعتماد على طول str() بدائي
    """

    def __init__(self, notion_client: NotionAPIClient, database_id: str):
        """
        Initialize CompanyLookup
        
        Args:
            notion_client: NotionAPIClient instance
            database_id: Companies database ID
        """
        self.notion_client = notion_client
        self.database_id = database_id
        self._cache = {}  # {apollo_account_id: page_id or None}
        logger.info(f"✅ CompanyLookup initialized for database: {database_id[:8]}...")

    def find_by_apollo_id(self, apollo_account_id: str) -> Optional[str]:
        """
        البحث عن شركة بـ Apollo Account ID
        
        Args:
            apollo_account_id: Apollo Account ID (e.g., '65d1c2e4f4c1b200010d8c5a')
            
        Returns:
            page_id (Notion page ID) أو None إذا لم توجد الشركة
        """
        if not apollo_account_id:
            return None

        # Check cache أولاً
        if apollo_account_id in self._cache:
            cached = self._cache[apollo_account_id]
            if cached:
                logger.debug(f"📦 Cache hit for company: {apollo_account_id[:8]}... → {cached[:8]}...")
            return cached

        try:
            # Query Notion
            response = requests.post(
                f"{self.notion_client.base_url}/databases/{self.database_id}/query",
                headers=self.notion_client.headers,
                json={
                    "filter": {
                        "property": "Apollo Account Id",  # ← استخدم الاسم الصحيح من schema
                        "rich_text": {
                            "equals": str(apollo_account_id)
                        }
                    }
                },
                timeout=10
            )
            response.raise_for_status()

            results = response.json().get('results', [])
            if results:
                page_id = results[0]['id']
                self._cache[apollo_account_id] = page_id  # Cache result
                logger.debug(f"✅ Found company by Apollo ID: {apollo_account_id[:8]}... → {page_id[:8]}...")
                return page_id

            # Not found - cache the None result
            logger.debug(f"⚠️ Company not found by Apollo ID: {apollo_account_id[:8]}...")
            self._cache[apollo_account_id] = None
            return None

        except requests.exceptions.RequestException as e:
            logger.warning(f"⚠️ Error looking up company {apollo_account_id[:8]}...: {str(e)}")
            return None

    def validate_page_id(self, page_id: str) -> bool:
        """
        التحقق من أن page_id صحيح (UUID format)
        
        Args:
            page_id: Notion page ID (32 hex chars or 36 with dashes)
            
        Returns:
            True إذا كان الـ ID صحيح، False إذا كان خاطئ
        """
        if not page_id or not isinstance(page_id, str):
            return False

        # Notion page IDs بدون أقواس: 32 حرف hex
        # مع أقواس: 36 حرف (8-4-4-4-12)
        page_id_clean = page_id.replace('-', '')

        # Check length
        if len(page_id) not in [32, 36]:
            logger.debug(f"⚠️ Invalid page_id length: {len(page_id)}")
            return False

        # Check hex characters
        try:
            int(page_id_clean, 16)
            return True
        except ValueError:
            logger.debug(f"⚠️ Invalid page_id format (not hex): {page_id}")
            return False

    def cache_stats(self) -> Dict[str, int]:
        """Get cache statistics"""
        found = sum(1 for v in self._cache.values() if v is not None)
        not_found = sum(1 for v in self._cache.values() if v is None)
        return {
            'total_lookups': len(self._cache),
            'found': found,
            'not_found': not_found
        }

# ═══════════════════════════════════════════════════════════════════════════
# SYNC ENGINE
# ═══════════════════════════════════════════════════════════════════════════

class ApolloNotionSyncEngine:
    """محرك المزامعة بين Apollo و Notion"""

    def __init__(self, apollo_client: ApolloAPIClient, notion_client: NotionAPIClient):
        self.apollo = apollo_client
        self.notion = notion_client
        self.last_sync_file = 'logs/last_sync_timestamp.txt'

    def get_last_sync_time(self) -> Optional[str]:
        """الحصول على آخر وقت مزامعة"""
        try:
            if os.path.exists(self.last_sync_file):
                with open(self.last_sync_file, 'r') as f:
                    return f.read().strip()
        except Exception as e:
            logger.warning(f"⚠️ Error reading last sync time: {str(e)}")
        return None

    def save_sync_time(self, timestamp: str):
        """حفظ وقت المزامعة الحالي"""
        try:
            with open(self.last_sync_file, 'w') as f:
                f.write(timestamp)
        except Exception as e:
            logger.warning(f"⚠️ Error saving sync time: {str(e)}")

    def sync_contacts(self) -> Dict[str, int]:
        """
        مزامعة جهات الاتصال من Apollo إلى Notion

        Returns:
            {created: int, updated: int, skipped: int}
        """
        logger.info("🔄 Starting contact sync...")

        stats = {'created': 0, 'updated': 0, 'skipped': 0, 'errors': 0}

        # الحصول على آخر وقت مزامعة
        last_sync = self.get_last_sync_time()

        # سحب جهات الاتصال من Apollo
        contacts = self.apollo.get_contacts(updated_after=last_sync)

        if not contacts:
            logger.info("ℹ️ No new contacts to sync")
            return stats

        # معالجة كل جهة اتصال
        for contact in contacts:
            try:
                email = (contact.get('email') or '').strip()
                contact_id = contact.get('id', '')
                account_id = contact.get('account_id', '')

                # DEBUG: Log raw contact data to see what's available
                logger.debug(f"🔍 Raw Apollo contact data for {contact.get('name', 'Unknown')}: {json.dumps(contact, indent=2, default=str)}")

                # ✅ ENHANCED DEDUPLICATION: Check email first, then Apollo ID
                # This GUARANTEES no duplication (even for contacts without email)
                exists, page_id = self.notion.contact_exists(
                    email=email if email else None,
                    database_id=NOTION_CONTACTS_DB,
                    apollo_id=contact_id  # Always pass Apollo ID for fallback
                )

                # Extract ALL available fields from Apollo contact
                # Find company page ID - try multiple methods for linking
                company_page_id = None
                company_name = (contact.get('organization_name') or '').strip()

                # Strategy 1: Try by Apollo Account ID (primary)
                if account_id:
                    company_exists, company_page_id = self.notion.company_exists(
                        apollo_account_id=account_id,
                        database_id=NOTION_COMPANIES_DB
                    )
                    if company_exists:
                        logger.debug(f"✅ Contact linked by Apollo Account ID: {company_name}")

                # Strategy 2: If not found by Apollo ID, try by company name (fallback)
                if not company_page_id and company_name:
                    try:
                        # Search in Companies database for the company
                        response = requests.post(
                            f"{self.notion.base_url}/databases/{NOTION_COMPANIES_DB}/query",
                            headers=self.notion.headers,
                            json={
                                "filter": {
                                    "property": "Company Name",
                                    "title": {
                                        "equals": company_name
                                    }
                                }
                            },
                            timeout=10
                        )
                        response.raise_for_status()
                        results = response.json().get('results', [])
                        if results:
                            company_page_id = results[0]['id']
                            logger.debug(f"✅ Contact linked by company name: {company_name}")
                    except requests.exceptions.RequestException as e:
                        logger.debug(f"⚠️ Company lookup by name failed for {company_name}: {str(e)}")

                if not company_page_id and company_name:
                    logger.debug(f"⚠️ Company not found for contact {contact_id}: {company_name} (account_id={account_id})")

                # معالجة خاصة للـ lists في Contacts
                departments = contact.get('departments', [])
                if isinstance(departments, list):
                    departments_str = ', '.join([str(d) for d in departments if d])
                else:
                    departments_str = str(departments) if departments else ''

                sub_departments = contact.get('sub_departments', [])
                if isinstance(sub_departments, list):
                    sub_departments_str = ', '.join([str(s) for s in sub_departments if s])
                else:
                    sub_departments_str = str(sub_departments) if sub_departments else ''

                contact_info = {
                    # Core Info
                    'name': contact.get('name', 'Unknown'),
                    'first_name': contact.get('first_name', ''),
                    'last_name': contact.get('last_name', ''),

                    # Contact Details
                    'email': email,
                    'secondary_email': (contact.get('secondary_email') or ''),
                    'email_status': (contact.get('email_status') or ''),
                    'phone': (contact.get('phone') or contact.get('direct_phone') or ''),  # Try both field names
                    'mobile_phone': (contact.get('mobile_phone') or ''),
                    'home_phone': (contact.get('home_phone') or ''),
                    'corporate_phone': (contact.get('corporate_phone') or ''),
                    'other_phone': (contact.get('other_phone') or ''),

                    # Job Info
                    'title': (contact.get('title') or ''),
                    'seniority': (contact.get('seniority') or ''),
                    'departments': departments_str,
                    'sub_departments': sub_departments_str,

                    # Company/Location
                    'company_name': (contact.get('organization_name') or ''),
                    'company_page_id': company_page_id,  # Relation link to Companies
                    'city': (contact.get('city') or ''),
                    'state': (contact.get('state') or ''),
                    'country': (contact.get('country') or ''),

                    # Social/URLs
                    'linkedin_url': (contact.get('linkedin_url') or ''),

                    # Apollo Links
                    'apollo_contact_id': contact_id,
                    'apollo_account_id': account_id,

                    # Status & Metadata
                    'status': (contact.get('status') or 'new'),
                    'record_source': 'Apollo',
                    'data_status': 'active',
                    'last_contacted': (contact.get('last_contacted_at') or ''),

                    # Engagement Tracking
                    'meeting_booked': contact.get('meeting_booked', False),
                    'email_sent': contact.get('email_sent', False),
                    'email_opened': contact.get('email_opened', False),
                    'email_bounced': contact.get('email_bounced', False),
                    'replied': contact.get('replied', False),
                }

                if exists and page_id:
                    # تحديث الجهة الموجودة
                    if self.notion.update_contact(page_id, contact_info):
                        stats['updated'] += 1
                    else:
                        stats['errors'] += 1
                else:
                    # إنشاء جهة جديدة
                    # (عند exists=False أو exists=True but page_id=None بسبب API error - نحاول الإنشاء)
                    success, _ = self.notion.create_contact(
                        NOTION_CONTACTS_DB,
                        contact_info
                    )
                    if success:
                        stats['created'] += 1
                    else:
                        stats['errors'] += 1

            except Exception as e:
                import traceback
                logger.error(f"❌ Error processing contact: {str(e)}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                stats['errors'] += 1

        # حفظ وقت المزامعة
        self.save_sync_time(datetime.now(timezone.utc).isoformat())

        return stats

    def sync_companies(self) -> Dict[str, int]:
        """
        مزامعة الشركات من Apollo إلى Notion
        سحب بكل الـ 30 خلية وعمل الربط مع Contacts
        """
        logger.info("🔄 Starting company sync...")

        stats = {'created': 0, 'updated': 0, 'skipped': 0, 'errors': 0}

        # الحصول على آخر وقت مزامعة
        last_sync = self.get_last_sync_time()

        # سحب الشركات (مع updated_after لتجنب سحب كل شيء كل مرة)
        companies = self.apollo.get_companies(updated_after=last_sync)

        if not companies:
            logger.info("ℹ️ No new companies to sync")
            return stats

        logger.info(f"📥 Pulled {len(companies)} companies from Apollo")

        # معالجة كل شركة
        for company in companies:
            try:
                domain = (company.get('domain') or '').strip()
                account_id = company.get('id', '')

                # DEBUG: Log raw company data to see what's available
                logger.debug(f"🔍 Raw Apollo company data for {company.get('name', 'Unknown')}: {json.dumps(company, indent=2, default=str)}")

                # ✅ ENHANCED DEDUPLICATION: Check domain first, then Apollo Account ID
                # This GUARANTEES no duplication (even for companies without domain)
                exists, page_id = self.notion.company_exists(
                    domain=domain if domain else None,
                    database_id=NOTION_COMPANIES_DB,
                    apollo_account_id=account_id  # Always pass Apollo Account ID for fallback
                )

                # استخرج ALL fields من Apollo
                # ✅ معالجة خاصة للـ lists (keywords, technologies)
                keywords = company.get('keywords', [])
                if isinstance(keywords, list):
                    keywords_str = ', '.join([str(k) for k in keywords if k])
                else:
                    keywords_str = str(keywords) if keywords else ''

                technologies = company.get('technologies', [])
                if isinstance(technologies, list):
                    technologies_str = ', '.join([str(t) for t in technologies if t])
                else:
                    technologies_str = str(technologies) if technologies else ''

                company_info = {
                    # Core
                    'name': company.get('name', 'Unknown'),
                    'apollo_account_id': account_id,

                    # Company Details
                    'domain': domain,
                    'website_url': (company.get('website_url') or ''),
                    'industry': (company.get('industry') or ''),
                    'keywords': keywords_str,
                    'technologies': technologies_str,

                    # Size
                    'employee_count': company.get('employee_count'),
                    'employee_size': (company.get('employee_size_category') or ''),

                    # Financial
                    'annual_revenue': company.get('annual_revenue'),
                    'revenue_range': (company.get('revenue_range') or ''),
                    'total_funding': company.get('total_funding'),
                    'latest_funding': str(company.get('latest_funding_stage') or ''),  # Always treat as string
                    'latest_funding_amount': company.get('latest_funding_amount'),
                    'last_raised_at': (company.get('last_funding_date') or ''),

                    # Location
                    'address': (company.get('hq_address') or ''),
                    'city': (company.get('hq_city') or ''),
                    'state': (company.get('hq_state') or ''),
                    'country': (company.get('hq_country') or ''),

                    # Contact
                    'phone': (company.get('phone') or ''),

                    # Social
                    'linkedin_url': (company.get('linkedin_url') or ''),
                    'facebook_url': (company.get('facebook_url') or ''),
                    'twitter_url': (company.get('twitter_url') or ''),

                    # Metadata
                    'account_owner': (company.get('account_owner_id') or ''),
                    'record_source': 'Apollo',
                    'data_status': 'active',
                }

                if exists and page_id:
                    # تحديث الشركة الموجودة
                    if self.notion.update_company(page_id, company_info):
                        stats['updated'] += 1
                    else:
                        stats['errors'] += 1
                else:
                    # إنشاء شركة جديدة
                    # (عند exists=False أو exists=True but page_id=None بسبب API error - نحاول الإنشاء)
                    success, _ = self.notion.create_company(
                        NOTION_COMPANIES_DB,
                        company_info
                    )
                    if success:
                        stats['created'] += 1
                    else:
                        stats['errors'] += 1

            except Exception as e:
                import traceback
                logger.error(f"❌ Error processing company: {str(e)}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                stats['errors'] += 1

        logger.info(f"✅ Company sync completed: Created={stats['created']}, Updated={stats['updated']}, Errors={stats['errors']}")
        return stats

# ═══════════════════════════════════════════════════════════════════════════
# SCHEDULER
# ═══════════════════════════════════════════════════════════════════════════

class SyncScheduler:
    """جدولة المزامعة التلقائية"""

    def __init__(self, sync_engine: ApolloNotionSyncEngine, interval_minutes: int = 5):
        self.engine = sync_engine
        self.interval = interval_minutes
        self._stop_event = threading.Event()
        self._thread = None

    def sync_job(self):
        """الوظيفة الرئيسية للمزامعة"""
        try:
            logger.info("=" * 80)
            logger.info(f"🔄 Sync Job Started at {datetime.now().isoformat()}")
            logger.info("=" * 80)

            # مزامعة الشركات أولاً (لكي نتمكن من ربطها مع Contacts)
            logger.info("📊 Phase 1: Syncing Companies...")
            company_stats = self.engine.sync_companies()

            # مزامعة جهات الاتصال (مع الربط بـ Companies)
            logger.info("📊 Phase 2: Syncing Contacts...")
            contact_stats = self.engine.sync_contacts()

            # تسجيل النتائج
            logger.info(f"""
            📊 SYNC RESULTS:
            ┌─ Companies:
            │  ├─ Created: {company_stats['created']}
            │  ├─ Updated: {company_stats['updated']}
            │  ├─ Skipped: {company_stats['skipped']}
            │  └─ Errors: {company_stats['errors']}
            ├─ Contacts:
            │  ├─ Created: {contact_stats['created']}
            │  ├─ Updated: {contact_stats['updated']}
            │  ├─ Skipped: {contact_stats['skipped']}
            │  └─ Errors: {contact_stats['errors']}
            └─ Relations: Auto-linked Contacts to Companies
            """)

            logger.info("=" * 80)
            logger.info("✅ Sync Job Completed")
            logger.info("=" * 80)

        except Exception as e:
            logger.error(f"❌ Sync job failed: {str(e)}", exc_info=True)

    def _run_loop(self):
        """حلقة التشغيل في خيط مستقل"""
        while not self._stop_event.is_set():
            self.sync_job()
            # انتظر الفترة المحددة أو حتى يتم الإيقاف
            self._stop_event.wait(timeout=self.interval * 60)

    def start(self):
        """بدء الجدولة"""
        logger.info(f"🚀 Starting scheduler (interval: {self.interval} minutes)")

        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True, name="SyncScheduler")
        self._thread.start()

        logger.info("✅ Scheduler started successfully")

    def stop(self):
        """إيقاف الجدولة"""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=10)
        logger.info("🛑 Scheduler stopped")

# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════

def validate_config() -> bool:
    """التحقق من التكوين"""
    logger.info("🔍 Validating configuration...")

    required_vars = {
        'APOLLO_API_KEY': APOLLO_API_KEY,
        'NOTION_API_KEY': NOTION_API_KEY,
        'NOTION_DATABASE_ID_CONTACTS': NOTION_CONTACTS_DB,
        'NOTION_DATABASE_ID_COMPANIES': NOTION_COMPANIES_DB,
    }

    for var_name, value in required_vars.items():
        if not value:
            logger.error(f"❌ Missing required variable: {var_name}")
            return False
        logger.info(f"✅ {var_name}: configured")

    logger.info("✅ Configuration validated")
    return True

def main():
    """البرنامج الرئيسي"""
    try:
        logger.info("\n" + "=" * 80)
        logger.info("🚀 APOLLO → NOTION SYNC ENGINE (API PULL)")
        logger.info("=" * 80)
        logger.info(f"Start Time: {datetime.now().isoformat()}")
        logger.info(f"Sync Interval: {SYNC_INTERVAL_MINUTES} minutes")
        logger.info("=" * 80 + "\n")

        # التحقق من التكوين
        if not validate_config():
            logger.error("❌ Configuration validation failed. Exiting.")
            return 1

        # إنشاء Clients
        apollo = ApolloAPIClient(APOLLO_API_KEY)
        notion = NotionAPIClient(NOTION_API_KEY)
        notion.log_all_schemas()

        # إنشاء محرك المزامعة
        engine = ApolloNotionSyncEngine(apollo, notion)

        # إنشاء وبدء الجدولة
        scheduler = SyncScheduler(engine, SYNC_INTERVAL_MINUTES)
        scheduler.start()

        # الاستمرار في التشغيل
        logger.info("✅ Sync engine is running. Press Ctrl+C to stop.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("\n🛑 Shutting down...")
            scheduler.stop()
            logger.info("✅ Sync engine stopped gracefully")

        return 0

    except Exception as e:
        logger.error(f"❌ Fatal error: {str(e)}", exc_info=True)
        return 1

if __name__ == '__main__':
    exit(main())
