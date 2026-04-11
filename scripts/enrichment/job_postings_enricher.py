#!/usr/bin/env python3
"""
AI Sales OS — Job Postings Enricher

Uses Apollo's Job Postings API as a proxy for Intent Score.
Companies that are actively hiring in relevant roles = higher buying intent.

Scoring:
  - Job Volume (0-40): Number of open positions
  - Recency (0-20): How recently jobs were posted
  - Relevance (0-25): Keywords matching our solution areas
  - Growth Signals (0-15): Hiring velocity / new departments

Writes: "Job Postings Intent" (number 0-100) on Companies,
        then propagates to linked Contacts' "Primary Intent Score".

Usage:
    python job_postings_enricher.py                    # enrich all HOT/WARM companies
    python job_postings_enricher.py --dry-run          # preview without writing
    python job_postings_enricher.py --limit 20         # limit to first N companies
    python job_postings_enricher.py --tier HOT         # only HOT companies
    python job_postings_enricher.py --no-cache         # ignore 7-day cache
"""
import sys as _sys, os as _os; _sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
import os
import sys
import json
import logging
import time
import argparse
import re
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.dirname(__file__))
from core.notion_helpers import (
    NOTION_DATABASE_ID_CONTACTS,
    NOTION_DATABASE_ID_COMPANIES,
    update_page,
    rate_limiter,
    notion_request,
    NOTION_BASE_URL,
)
from core.constants import (
    FIELD_LEAD_SCORE, FIELD_LEAD_TIER, FIELD_APOLLO_ACCOUNT_ID,
    FIELD_INTENT_SCORE_PRIMARY, FIELD_EMPLOYEES,
    TIER_HOT, TIER_WARM, SCORE_HOT, SCORE_WARM,
)

# ─── Config ──────────────────────────────────────────────────────────────────

APOLLO_API_KEY = os.getenv("APOLLO_API_KEY")
APOLLO_BASE_URL = "https://api.apollo.io/api/v1"
MAX_WORKERS = 3
CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "job_postings_cache.json")
CACHE_TTL_DAYS = 7

# Relevance keywords (matched against job titles)
RELEVANCE_KEYWORDS = {
    "high": [
        "insurance", "risk", "compliance", "legal", "finance", "cfo",
        "procurement", "purchasing", "supply chain", "operations",
        "safety", "quality", "audit", "treasury",
    ],
    "medium": [
        "director", "manager", "head", "vp", "chief",
        "sales", "business development", "account",
        "technology", "digital", "transformation", "it ",
    ],
}

# ─── Logging ─────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("job_postings.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


# ─── Apollo API ──────────────────────────────────────────────────────────────

def apollo_request(method: str, url: str, max_retries: int = 5, **kwargs):
    """Apollo API request with retry logic."""
    import requests
    kwargs.setdefault("timeout", 30)
    headers = kwargs.pop("headers", {})
    headers["Content-Type"] = "application/json"
    headers["Cache-Control"] = "no-cache"

    for attempt in range(max_retries):
        try:
            resp = requests.request(method, url, headers=headers, **kwargs)
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            if attempt < max_retries - 1:
                wait = min(2 ** attempt, 30)
                logger.warning(f"Connection error (attempt {attempt + 1}): {e}, retrying in {wait}s")
                time.sleep(wait)
                continue
            raise

        if resp.status_code == 429:
            wait = float(resp.headers.get("Retry-After", min(2 ** attempt, 30)))
            logger.warning(f"Rate limited (attempt {attempt + 1}), waiting {wait}s")
            time.sleep(wait)
            continue

        if resp.status_code >= 500:
            wait = min(2 ** attempt, 30)
            logger.warning(f"Server error {resp.status_code}, retrying in {wait}s")
            time.sleep(wait)
            continue

        resp.raise_for_status()
        return resp

    raise Exception(f"Failed after {max_retries} retries: {method} {url}")


# ─── Cache ───────────────────────────────────────────────────────────────────

def load_cache() -> Dict:
    """Load job postings cache."""
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_cache(cache: Dict):
    """Save job postings cache."""
    try:
        with open(CACHE_FILE, "w") as f:
            json.dump(cache, f, indent=2)
    except Exception as e:
        logger.warning(f"Could not save cache: {e}")


def is_cache_valid(entry: Dict) -> bool:
    """Check if a cache entry is within TTL."""
    cached_at = entry.get("cached_at", "")
    if not cached_at:
        return False
    try:
        cached_time = datetime.fromisoformat(cached_at)
        return datetime.now(timezone.utc) - cached_time < timedelta(days=CACHE_TTL_DAYS)
    except Exception:
        return False


# ─── Fetch Companies from Notion ─────────────────────────────────────────────

def fetch_companies_for_enrichment(tier_filter: Optional[str] = None, limit: Optional[int] = None) -> List[Dict]:
    """
    Fetch companies that have linked contacts with HOT or WARM tiers.
    We query contacts by tier, then collect their company IDs.
    """
    results = []
    company_map = {}  # company_page_id -> company_info
    cursor = None

    # Build filter based on tier
    min_score = SCORE_HOT if tier_filter == "HOT" else SCORE_WARM

    while True:
        body = {
            "page_size": 100,
            "filter": {
                "property": FIELD_LEAD_SCORE,
                "number": {"greater_than_or_equal_to": min_score},
            },
        }
        if cursor:
            body["start_cursor"] = cursor

        rate_limiter.wait()
        try:
            resp = notion_request("POST", f"{NOTION_BASE_URL}/databases/{NOTION_DATABASE_ID_CONTACTS}/query", json=body)
            data = resp.json()
        except Exception as e:
            logger.error(f"Error fetching contacts: {e}")
            break

        for page in data.get("results", []):
            props = page.get("properties", {})
            company_rel = props.get("Company", {}).get("relation", [])
            for rel in company_rel:
                cid = rel.get("id")
                if cid and cid not in company_map:
                    company_map[cid] = {"page_id": cid, "contact_ids": []}
                if cid:
                    company_map[cid]["contact_ids"].append(page["id"])

        if not data.get("has_more"):
            break
        cursor = data.get("next_cursor")

    # Now fetch Apollo Account IDs for these companies
    logger.info(f"Found {len(company_map)} unique companies linked to scored contacts")

    for company_id in list(company_map.keys()):
        if limit and len(results) >= limit:
            break

        rate_limiter.wait()
        try:
            resp = notion_request("GET", f"{NOTION_BASE_URL}/pages/{company_id}")
            page = resp.json()
            props = page.get("properties", {})

            apollo_id_rt = props.get(FIELD_APOLLO_ACCOUNT_ID, {}).get("rich_text", [])
            apollo_id = apollo_id_rt[0]["plain_text"].strip() if apollo_id_rt else ""

            name_title = props.get("Company Name", {}).get("title", [])
            name = name_title[0]["text"]["content"] if name_title else "Unknown"

            if apollo_id:
                company_map[company_id]["apollo_id"] = apollo_id
                company_map[company_id]["name"] = name
                results.append(company_map[company_id])
        except Exception as e:
            logger.warning(f"Could not fetch company {company_id}: {e}")

        if len(results) % 50 == 0 and results:
            logger.info(f"  Processed {len(results)} companies...")

    logger.info(f"Found {len(results)} companies with Apollo IDs for enrichment")
    return results


# ─── Fetch Job Postings from Apollo ──────────────────────────────────────────

def fetch_job_postings(apollo_org_id: str) -> List[Dict]:
    """Fetch job postings for a company from Apollo API."""
    try:
        resp = apollo_request(
            "GET",
            f"{APOLLO_BASE_URL}/organizations/{apollo_org_id}/job_postings",
            params={"api_key": APOLLO_API_KEY, "per_page": 100},
        )
        data = resp.json()
        return data.get("job_postings", [])
    except Exception as e:
        logger.warning(f"Could not fetch job postings for {apollo_org_id}: {e}")
        return []


# ─── Intent Score Calculation ────────────────────────────────────────────────

def calculate_intent_score(postings: List[Dict]) -> Tuple[int, Dict]:
    """
    Calculate intent score (0-100) from job postings.

    Components:
    - Volume (0-40): Number of open jobs
    - Recency (0-20): How recently posted
    - Relevance (0-25): Keyword matching
    - Growth (0-15): Hiring velocity signals
    """
    if not postings:
        return 0, {"volume": 0, "recency": 0, "relevance": 0, "growth": 0, "total": 0, "job_count": 0}

    now = datetime.now(timezone.utc)

    # 1. Volume Score (0-40)
    count = len(postings)
    if count >= 50:
        volume = 40
    elif count >= 20:
        volume = 35
    elif count >= 10:
        volume = 28
    elif count >= 5:
        volume = 20
    elif count >= 2:
        volume = 12
    else:
        volume = 5

    # 2. Recency Score (0-20)
    recency = 0
    recent_count = 0
    for job in postings:
        posted_at = job.get("last_seen_at") or job.get("posted_at") or ""
        if posted_at:
            try:
                post_date = datetime.fromisoformat(posted_at.replace("Z", "+00:00"))
                days_ago = (now - post_date).days
                if days_ago <= 7:
                    recent_count += 1
                elif days_ago <= 30:
                    recent_count += 0.5
            except Exception:
                pass

    if recent_count >= 10:
        recency = 20
    elif recent_count >= 5:
        recency = 16
    elif recent_count >= 2:
        recency = 10
    elif recent_count >= 1:
        recency = 6
    else:
        recency = 0

    # 3. Relevance Score (0-25)
    relevance = 0
    high_match = 0
    medium_match = 0
    for job in postings:
        title = (job.get("title") or "").lower()
        for kw in RELEVANCE_KEYWORDS["high"]:
            if kw in title:
                high_match += 1
                break
        for kw in RELEVANCE_KEYWORDS["medium"]:
            if kw in title:
                medium_match += 1
                break

    if high_match >= 3:
        relevance = 25
    elif high_match >= 1:
        relevance = 18
    elif medium_match >= 3:
        relevance = 12
    elif medium_match >= 1:
        relevance = 6

    # 4. Growth Signals (0-15)
    growth = 0
    unique_departments = set()
    for job in postings:
        dept = (job.get("department") or "").strip()
        if dept:
            unique_departments.add(dept.lower())

    if len(unique_departments) >= 5:
        growth = 15
    elif len(unique_departments) >= 3:
        growth = 10
    elif len(unique_departments) >= 1:
        growth = 5

    total = min(volume + recency + relevance + growth, 100)

    breakdown = {
        "volume": volume,
        "recency": recency,
        "relevance": relevance,
        "growth": growth,
        "total": total,
        "job_count": count,
        "high_match": high_match,
        "recent_count": int(recent_count),
    }

    return total, breakdown


# ─── Write to Notion ─────────────────────────────────────────────────────────

def write_company_intent(company_id: str, score: int) -> bool:
    """Write intent-related data to company page."""
    try:
        update_page(company_id, {
            "Job Postings Intent": {"number": score},
        })
        return True
    except Exception as e:
        logger.error(f"Error writing company intent {company_id}: {e}")
        return False


def propagate_to_contacts(contact_ids: List[str], intent_score: int, dry_run: bool = False) -> int:
    """Write Primary Intent Score to linked contacts."""
    updated = 0
    for cid in contact_ids:
        if dry_run:
            updated += 1
            continue
        try:
            update_page(cid, {
                FIELD_INTENT_SCORE_PRIMARY: {"number": intent_score},
            })
            updated += 1
        except Exception as e:
            logger.warning(f"Error updating contact {cid}: {e}")
    return updated


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="AI Sales OS — Job Postings Enricher")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing")
    parser.add_argument("--limit", type=int, default=None, help="Limit to first N companies")
    parser.add_argument("--tier", choices=["HOT", "WARM"], default=None, help="Only process specific tier")
    parser.add_argument("--no-cache", action="store_true", help="Ignore cache, re-fetch all")
    args = parser.parse_args()

    logger.info("=" * 70)
    logger.info(f"JOB POSTINGS ENRICHER | Dry Run: {args.dry_run} | Limit: {args.limit or 'ALL'} | Tier: {args.tier or 'ALL'}")
    logger.info("=" * 70)

    start_time = time.time()
    cache = {} if args.no_cache else load_cache()

    # Step 1: Fetch companies
    logger.info("Step 1: Fetching companies for enrichment...")
    companies = fetch_companies_for_enrichment(tier_filter=args.tier, limit=args.limit)

    if not companies:
        logger.info("No companies found. Done!")
        return

    # Step 2: Process each company
    logger.info(f"Step 2: Processing {len(companies)} companies...")
    stats = {
        "enriched": 0, "cached": 0, "no_postings": 0,
        "contacts_updated": 0, "errors": 0,
    }

    for i, company in enumerate(companies, 1):
        apollo_id = company["apollo_id"]
        name = company.get("name", "Unknown")

        # Check cache
        if apollo_id in cache and is_cache_valid(cache[apollo_id]):
            cached = cache[apollo_id]
            score = cached["score"]
            stats["cached"] += 1
            logger.info(f"  [{i}/{len(companies)}] {name}: cached score={score}")

            if not args.dry_run and score > 0:
                write_company_intent(company["page_id"], score)
                propagate_to_contacts(company["contact_ids"], score)
                stats["contacts_updated"] += len(company["contact_ids"])
            continue

        # Fetch from Apollo
        postings = fetch_job_postings(apollo_id)
        score, breakdown = calculate_intent_score(postings)

        # Update cache
        cache[apollo_id] = {
            "score": score,
            "breakdown": breakdown,
            "cached_at": datetime.now(timezone.utc).isoformat(),
            "company_name": name,
        }

        if score == 0:
            stats["no_postings"] += 1
            logger.info(f"  [{i}/{len(companies)}] {name}: no relevant postings (score=0)")
            continue

        stats["enriched"] += 1
        logger.info(f"  [{i}/{len(companies)}] {name}: score={score} | jobs={breakdown['job_count']} | {breakdown}")

        if not args.dry_run:
            if write_company_intent(company["page_id"], score):
                cnt = propagate_to_contacts(company["contact_ids"], score)
                stats["contacts_updated"] += cnt
            else:
                stats["errors"] += 1

        # Rate limit between Apollo calls
        time.sleep(0.5)

    # Save cache
    save_cache(cache)

    elapsed = time.time() - start_time

    logger.info("=" * 70)
    logger.info(f"JOB POSTINGS ENRICHER COMPLETE")
    logger.info(f"  Enriched: {stats['enriched']}")
    logger.info(f"  Cached (reused): {stats['cached']}")
    logger.info(f"  No postings: {stats['no_postings']}")
    logger.info(f"  Contacts updated: {stats['contacts_updated']}")
    logger.info(f"  Errors: {stats['errors']}")
    logger.info(f"  Time: {elapsed:.1f}s")
    logger.info("=" * 70)

    # Save stats for health check
    stats_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "last_job_postings_stats.json")
    try:
        with open(stats_file, "w") as f:
            json.dump(stats, f, indent=2)
    except Exception:
        pass


if __name__ == "__main__":
    main()
