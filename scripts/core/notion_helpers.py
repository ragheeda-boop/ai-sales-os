#!/usr/bin/env python3
"""
Shared Notion helpers: RateLimiter, smart retry, pre-load lookups.
Used by initial_load_from_csv.py and daily_sync.py.
"""
import os
import time
import logging
import threading
import requests
from typing import Dict, Optional
from dotenv import load_dotenv

load_dotenv()

NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_DATABASE_ID_CONTACTS = os.getenv("NOTION_DATABASE_ID_CONTACTS", "9ca842d20aa9460bbdd958d0aa940d9c")
NOTION_DATABASE_ID_COMPANIES = os.getenv("NOTION_DATABASE_ID_COMPANIES", "331e04a62da74afe9ab6b0efead39200")
NOTION_BASE_URL = "https://api.notion.com/v1"
NOTION_API_VERSION = "2022-06-28"

logger = logging.getLogger(__name__)


# ─── Rate Limiter ─────────────────────────────────────────────────────────────

class RateLimiter:
    """Thread-safe rate limiter for Notion API (max ~3 req/sec)."""

    def __init__(self, max_per_second: float = 3.0):
        self.delay = 1.0 / max_per_second
        self.lock = threading.Lock()
        self.last_call = 0.0

    def wait(self):
        with self.lock:
            now = time.time()
            elapsed = now - self.last_call
            if elapsed < self.delay:
                time.sleep(self.delay - elapsed)
            self.last_call = time.time()


rate_limiter = RateLimiter(max_per_second=3.0)


# ─── Smart Request with Retry ────────────────────────────────────────────────

def notion_headers() -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Notion-Version": NOTION_API_VERSION,
        "Content-Type": "application/json",
    }


def notion_request(method: str, url: str, max_retries: int = 5, **kwargs) -> requests.Response:
    """
    Smart Notion request with comprehensive retry logic:
    - No fixed delay — uses RateLimiter instead
    - Retries on 429 (rate limit) with Retry-After header
    - Retries on 5xx (server errors) with exponential backoff
    - Retries on timeout (ReadTimeout, ConnectTimeout) with exponential backoff
    - Retries on connection errors (ConnectionResetError, ConnectionError)
    """
    kwargs.setdefault("timeout", 30)
    kwargs.setdefault("headers", {}).update(notion_headers())

    for attempt in range(max_retries):
        rate_limiter.wait()

        try:
            resp = requests.request(method, url, **kwargs)
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            # Retry on timeout and connection errors (covers ReadTimeout,
            # ConnectTimeout, ConnectionResetError, etc.)
            if attempt < max_retries - 1:
                wait = min(2 ** attempt, 30)  # Cap at 30 seconds
                logger.warning(
                    f"Connection error (attempt {attempt + 1}/{max_retries}): "
                    f"{type(e).__name__}: {e}, retrying in {wait}s"
                )
                time.sleep(wait)
                continue
            logger.error(f"Connection error after {max_retries} retries: {e}")
            raise
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                wait = 2 ** attempt
                logger.warning(f"Request error (attempt {attempt + 1}): {e}, retrying in {wait}s")
                time.sleep(wait)
                continue
            raise

        if resp.status_code == 429:
            wait = float(resp.headers.get("Retry-After", min(2 ** attempt, 30)))
            logger.warning(f"Rate limited (attempt {attempt + 1}), waiting {wait}s...")
            time.sleep(wait)
            continue

        if resp.status_code >= 500:
            wait = min(2 ** attempt, 30)
            logger.warning(f"Server error {resp.status_code} (attempt {attempt + 1}), retrying in {wait}s")
            time.sleep(wait)
            continue

        if resp.status_code >= 400:
            logger.error(f"Notion API error {resp.status_code}: {resp.text[:300]}")

        resp.raise_for_status()
        return resp

    raise Exception(f"Failed after {max_retries} retries: {method} {url}")


# ─── Pre-load Lookups ────────────────────────────────────────────────────────

def preload_companies() -> Dict[str, str]:
    """
    Pre-load all companies from Notion into memory.
    Returns: { apollo_account_id: page_id, domain: page_id }
    """
    lookup = {}
    has_more = True
    start_cursor = None
    count = 0

    logger.info("Pre-loading companies from Notion...")

    while has_more:
        body = {"page_size": 100}
        if start_cursor:
            body["start_cursor"] = start_cursor

        resp = notion_request(
            "POST",
            f"{NOTION_BASE_URL}/databases/{NOTION_DATABASE_ID_COMPANIES}/query",
            json=body,
        )
        data = resp.json()

        for page in data.get("results", []):
            pid = page["id"]
            props = page.get("properties", {})

            # Apollo Account Id
            aid_rt = props.get("Apollo Account Id", {}).get("rich_text", [])
            if aid_rt:
                val = aid_rt[0].get("plain_text", "").strip()
                if val:
                    lookup[f"aid:{val}"] = pid

            # Domain
            dom_rt = props.get("Domain", {}).get("rich_text", [])
            if dom_rt:
                val = dom_rt[0].get("plain_text", "").strip()
                if val:
                    lookup[f"dom:{val}"] = pid

            count += 1

        has_more = data.get("has_more", False)
        start_cursor = data.get("next_cursor")

    logger.info(f"Pre-loaded {count} companies ({len(lookup)} lookup keys)")
    return lookup


def preload_contacts() -> Dict[str, str]:
    """
    Pre-load all contacts from Notion into memory.
    Returns: { apollo_contact_id: page_id, email: page_id }
    """
    lookup = {}
    has_more = True
    start_cursor = None
    count = 0

    logger.info("Pre-loading contacts from Notion...")

    while has_more:
        body = {"page_size": 100}
        if start_cursor:
            body["start_cursor"] = start_cursor

        resp = notion_request(
            "POST",
            f"{NOTION_BASE_URL}/databases/{NOTION_DATABASE_ID_CONTACTS}/query",
            json=body,
        )
        data = resp.json()

        for page in data.get("results", []):
            pid = page["id"]
            props = page.get("properties", {})

            # Apollo Contact Id
            aid_rt = props.get("Apollo Contact Id", {}).get("rich_text", [])
            if aid_rt:
                val = aid_rt[0].get("plain_text", "").strip()
                if val:
                    lookup[f"aid:{val}"] = pid

            # Email
            email_val = props.get("Email", {}).get("email")
            if email_val:
                lookup[f"email:{email_val.strip().lower()}"] = pid

            count += 1

        has_more = data.get("has_more", False)
        start_cursor = data.get("next_cursor")

    logger.info(f"Pre-loaded {count} contacts ({len(lookup)} lookup keys)")
    return lookup


# ─── Notion Create/Update ─────────────────────────────────────────────────────

def create_page(database_id: str, properties: Dict) -> Optional[str]:
    """Create a page in Notion. Returns page_id or None."""
    resp = notion_request(
        "POST",
        f"{NOTION_BASE_URL}/pages",
        json={
            "parent": {"database_id": database_id},
            "properties": properties,
        },
    )
    return resp.json().get("id")


def update_page(page_id: str, properties: Dict) -> bool:
    """Update a page in Notion. Returns True on success."""
    notion_request(
        "PATCH",
        f"{NOTION_BASE_URL}/pages/{page_id}",
        json={"properties": properties},
    )
    return True
