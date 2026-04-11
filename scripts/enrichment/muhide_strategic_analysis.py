#!/usr/bin/env python3
"""
MUHIDE Strategic Analysis Engine
=================================
Analyzes ALL companies in the Notion Companies DB against MUHIDE's B2B trade
governance and financing platform value proposition.

Writes 5 properties per company:
  - MUHIDE Strategic Analysis (rich text)
  - MUHIDE Fit Score (number 1-100)
  - MUHIDE Priority (P1/P2/P3)
  - MUHIDE Best Buyer (select)
  - MUHIDE Outreach Angle (rich text)

Usage:
  python muhide_strategic_analysis.py                  # process all companies
  python muhide_strategic_analysis.py --dry-run        # preview without writing
  python muhide_strategic_analysis.py --limit 50       # process first N only
  python muhide_strategic_analysis.py --resume         # resume from checkpoint
"""

import sys as _sys, os as _os; _sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
import os
import sys
import json
import time
import logging
import argparse
import re
import threading
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add the script directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.notion_helpers import (
    NOTION_BASE_URL, NOTION_DATABASE_ID_COMPANIES,
    notion_request, notion_headers, rate_limiter
)

# ═══════════════════════════════════════════════════════════════════════════════
# LOGGING
# ═══════════════════════════════════════════════════════════════════════════════

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("muhide_analysis.log", mode="w"),
    ],
)
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# MUHIDE INDUSTRY INTELLIGENCE
# ═══════════════════════════════════════════════════════════════════════════════

# Industries with strong B2B trade governance / receivables / delivery needs
HIGH_FIT_INDUSTRIES = {
    "construction", "building materials", "civil engineering",
    "healthcare", "medical devices", "hospital & health care",
    "pharmaceuticals", "medical equipment", "health care",
    "manufacturing", "industrial manufacturing", "industrial automation",
    "machinery", "electrical/electronic manufacturing", "mechanical or industrial engineering",
    "automotive", "auto parts", "motor vehicle manufacturing",
    "logistics", "transportation", "trucking", "shipping", "freight",
    "warehousing", "supply chain", "maritime", "package/freight delivery",
    "wholesale", "distribution", "import and export", "international trade and development",
    "oil & energy", "oil & gas", "mining & metals", "chemicals",
    "food & beverages", "food production", "dairy", "farming",
    "textiles", "apparel & fashion", "consumer goods",
    "facility management", "facilities services", "building maintenance",
    "defense & space", "military", "aviation & aerospace",
    "utilities", "renewables & environment", "electrical",
    "contracting", "general contracting", "engineering services",
    "real estate", "commercial real estate", "property management",
    "insurance", "financial services", "banking",
    "telecommunications", "wireless",
    "printing", "packaging and containers", "paper & forest products",
    "plastics", "glass, ceramics & concrete", "furniture",
    "staffing and recruiting", "human resources",
    "security and investigations", "environmental services",
}

# Industries with medium B2B fit
MEDIUM_FIT_INDUSTRIES = {
    "information technology and services", "computer software",
    "internet", "computer hardware", "semiconductors",
    "education management", "higher education", "e-learning",
    "professional training & coaching",
    "accounting", "legal services", "law practice",
    "management consulting", "business supplies and equipment",
    "market research", "public relations and communications",
    "design", "architecture & planning",
    "hospitality", "restaurants", "food & beverages",
    "leisure, travel & tourism", "events services",
    "government administration", "public policy",
    "nonprofit organization management",
    "media production", "broadcast media",
    "sports", "entertainment", "music",
    "veterinary", "cosmetics",
}

# Industries that are generally LOW fit for MUHIDE
LOW_FIT_INDUSTRIES = {
    "consumer electronics", "consumer services",
    "online media", "blogs", "social media",
    "gaming", "computer games", "gambling & casinos",
    "photography", "fine art", "arts and crafts",
    "individual & family services", "mental health care",
    "religious institutions", "civic & social organization",
    "political organization", "think tanks",
    "writing and editing", "libraries",
    "animation", "graphic design",
}

# Keywords that signal HIGH MUHIDE relevance
HIGH_FIT_KEYWORDS = {
    "b2b", "supply chain", "procurement", "logistics", "distribution",
    "wholesale", "manufacturing", "construction", "contracting",
    "receivables", "invoice", "billing", "payment", "credit",
    "trade", "export", "import", "shipping", "freight",
    "delivery", "fulfillment", "warehouse", "inventory",
    "compliance", "audit", "governance", "risk management",
    "insurance", "underwriting", "claims",
    "erp", "sap", "oracle", "netsuite",
    "healthcare", "medical", "pharmaceutical", "hospital",
    "industrial", "engineering", "machinery", "equipment",
    "oil", "gas", "energy", "mining", "chemicals",
    "food", "beverage", "dairy", "agriculture",
    "automotive", "fleet", "vehicles",
    "facility", "maintenance", "services",
    "real estate", "property", "commercial",
    "infrastructure", "utilities", "telecom",
    "finance", "banking", "fintech", "lending",
    "defense", "military", "government",
    "textiles", "apparel", "furniture",
}

# MENA / GCC countries — higher priority for MUHIDE's initial market
PRIORITY_COUNTRIES = {
    "saudi arabia", "united arab emirates", "uae", "qatar", "bahrain",
    "oman", "kuwait", "jordan", "egypt", "lebanon", "iraq",
    "morocco", "tunisia", "algeria", "libya",
    "turkey", "pakistan", "india",
}

# ═══════════════════════════════════════════════════════════════════════════════
# ANALYSIS ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

def extract_company_data(page: Dict) -> Dict:
    """Extract all relevant fields from a Notion company page."""
    props = page.get("properties", {})

    def get_text(field_name: str) -> str:
        prop = props.get(field_name, {})
        ptype = prop.get("type", "")
        if ptype == "rich_text":
            parts = prop.get("rich_text", [])
            return " ".join(p.get("plain_text", "") for p in parts).strip()
        elif ptype == "title":
            parts = prop.get("title", [])
            return " ".join(p.get("plain_text", "") for p in parts).strip()
        elif ptype == "url":
            return prop.get("url") or ""
        elif ptype == "email":
            return prop.get("email") or ""
        elif ptype == "phone_number":
            return prop.get("phone_number") or ""
        return ""

    def get_number(field_name: str) -> Optional[float]:
        prop = props.get(field_name, {})
        if prop.get("type") == "number":
            return prop.get("number")
        elif prop.get("type") == "rollup":
            rollup = prop.get("rollup", {})
            return rollup.get("number")
        return None

    def get_select(field_name: str) -> str:
        prop = props.get(field_name, {})
        sel = prop.get("select")
        if sel and isinstance(sel, dict):
            return sel.get("name", "")
        return ""

    return {
        "page_id": page["id"],
        "name": get_text("Company Name"),
        "industry": get_text("Industry"),
        "domain": get_text("Domain"),
        "website": get_text("Website"),
        "keywords": get_text("Keywords"),
        "technologies": get_text("Technologies"),
        "short_description": get_text("Short Description"),
        "employees": get_number("Employees"),
        "employee_size": get_text("Employee Size"),
        "annual_revenue": get_number("Annual Revenue"),
        "revenue_range": get_text("Revenue Range"),
        "country": get_text("Company Country"),
        "city": get_text("Company City"),
        "state": get_text("Company State"),
        "account_stage": get_select("Account Stage"),
        "ai_qualification_status": get_select("AI Qualification Status"),
        "ai_qualification_detail": get_text("AI Qualification Detail"),
        "headcount_growth_6m": get_number("Headcount Growth 6M"),
        "headcount_growth_12m": get_number("Headcount Growth 12M"),
        "headcount_growth_24m": get_number("Headcount Growth 24M"),
        "total_funding": get_number("Total Funding"),
        "naics_codes": get_text("NAICS Codes"),
        "sic_codes": get_text("SIC Codes"),
        "contact_count": get_number("Contact Count"),
        "primary_intent_score": get_number("Primary Intent Score"),
        "lists": get_text("Lists"),
        "founded_year": get_number("Founded Year"),
    }


def classify_industry(industry: str) -> Tuple[str, int]:
    """Classify industry fit. Returns (fit_level, score_component)."""
    if not industry:
        return "unknown", 25  # Neutral if no data

    ind_lower = industry.lower().strip()

    # Check high fit
    for hi in HIGH_FIT_INDUSTRIES:
        if hi in ind_lower or ind_lower in hi:
            return "high", 40
    # Partial keyword matches
    high_partials = [
        "construct", "manufactur", "logistic", "wholesale", "distribut",
        "medical", "health", "pharma", "industrial", "oil", "gas",
        "mining", "chemical", "food", "beverage", "automat",
        "freight", "shipping", "transport", "supply", "warehouse",
        "insurance", "financ", "bank", "defense", "military",
        "telecom", "utilit", "electric", "energy", "engineer",
        "facility", "maintenance", "textile", "apparel",
        "real estate", "property", "packag", "printing",
        "plasti", "furniture", "staffing", "security",
        "import", "export", "trade", "agri", "farm",
    ]
    for kw in high_partials:
        if kw in ind_lower:
            return "high", 38

    # Check medium fit
    for med in MEDIUM_FIT_INDUSTRIES:
        if med in ind_lower or ind_lower in med:
            return "medium", 22
    medium_partials = [
        "consult", "legal", "account", "education", "training",
        "profession", "design", "architect", "hospitality",
        "restaurant", "travel", "event", "government", "public",
        "media", "broadcast", "nonprofit",
    ]
    for kw in medium_partials:
        if kw in ind_lower:
            return "medium", 20

    # Check low fit
    for low in LOW_FIT_INDUSTRIES:
        if low in ind_lower or ind_lower in low:
            return "low", 8
    low_partials = [
        "consumer", "gaming", "photo", "art", "blog",
        "social media", "individual", "religious", "political",
        "writing", "animation", "graphic design",
    ]
    for kw in low_partials:
        if kw in ind_lower:
            return "low", 8

    # Default: treat as medium-low
    return "medium-low", 15


def score_company_size(employees: Optional[float], employee_size: str, revenue: Optional[float], revenue_range: str) -> int:
    """Score based on company size. Larger = more complex trade operations. (0-25)"""
    size_score = 0

    # Employee count scoring
    if employees:
        if employees >= 5000:
            size_score += 25
        elif employees >= 1000:
            size_score += 22
        elif employees >= 500:
            size_score += 18
        elif employees >= 200:
            size_score += 14
        elif employees >= 50:
            size_score += 10
        elif employees >= 11:
            size_score += 6
        else:
            size_score += 3
    elif employee_size:
        es = employee_size.lower()
        if "10001" in es or "10,001" in es or "5001" in es or "5,001" in es:
            size_score += 25
        elif "1001" in es or "1,001" in es:
            size_score += 22
        elif "501" in es or "201" in es:
            size_score += 16
        elif "51" in es or "11" in es:
            size_score += 8
        elif "1-10" in es or "1,10" in es:
            size_score += 3
        else:
            size_score += 5  # has data but unclear

    # Revenue scoring (bonus, max +5 from revenue)
    if revenue:
        if revenue >= 1_000_000_000:
            size_score = min(size_score + 5, 25)
        elif revenue >= 100_000_000:
            size_score = min(size_score + 4, 25)
        elif revenue >= 10_000_000:
            size_score = min(size_score + 3, 25)
    elif revenue_range:
        rr = revenue_range.lower()
        if "billion" in rr or "$1b" in rr:
            size_score = min(size_score + 5, 25)
        elif "100m" in rr or "$500" in rr:
            size_score = min(size_score + 4, 25)

    return min(size_score, 25)


def score_keywords(keywords: str, technologies: str, description: str) -> int:
    """Score based on keyword analysis for B2B trade governance relevance. (0-20)"""
    combined = f"{keywords} {technologies} {description}".lower()
    if not combined.strip():
        return 5  # No data → neutral

    hit_count = 0
    for kw in HIGH_FIT_KEYWORDS:
        if kw in combined:
            hit_count += 1

    if hit_count >= 8:
        return 20
    elif hit_count >= 5:
        return 16
    elif hit_count >= 3:
        return 12
    elif hit_count >= 1:
        return 8
    return 3


def score_geography(country: str) -> int:
    """Score based on geographic priority. (0-10)"""
    if not country:
        return 4  # Unknown
    c = country.lower().strip()
    for pc in PRIORITY_COUNTRIES:
        if pc in c or c in pc:
            return 10
    # Other regions with B2B trade potential
    moderate_countries = {"united states", "united kingdom", "germany", "france",
                          "china", "japan", "south korea", "singapore", "malaysia",
                          "indonesia", "thailand", "brazil", "mexico", "south africa",
                          "nigeria", "kenya", "australia", "canada", "netherlands",
                          "switzerland", "italy", "spain"}
    for mc in moderate_countries:
        if mc in c or c in mc:
            return 6
    return 4


def score_growth_signals(data: Dict) -> int:
    """Score based on growth signals. (0-5)"""
    score = 0
    hg6 = data.get("headcount_growth_6m")
    hg12 = data.get("headcount_growth_12m")
    if hg6 and hg6 > 10:
        score += 2
    elif hg6 and hg6 > 0:
        score += 1
    if hg12 and hg12 > 15:
        score += 2
    elif hg12 and hg12 > 0:
        score += 1
    if data.get("total_funding") and data["total_funding"] > 0:
        score += 1
    return min(score, 5)


def determine_best_buyer(data: Dict, industry_fit: str) -> str:
    """Determine the best buyer persona based on company profile."""
    industry = (data.get("industry") or "").lower()
    employees = data.get("employees") or 0
    keywords = (data.get("keywords") or "").lower()

    # Small companies → target founder/CEO directly
    if employees and employees < 50:
        return "CEO"

    # Finance-heavy signals
    finance_signals = ["financ", "bank", "insurance", "account", "invest", "credit", "lending"]
    if any(s in industry for s in finance_signals) or any(s in keywords for s in finance_signals):
        return "CFO"

    # Operations-heavy signals
    ops_signals = ["logistic", "supply chain", "warehouse", "transport", "shipping", "freight",
                   "manufactur", "facility", "maintenance"]
    if any(s in industry for s in ops_signals) or any(s in keywords for s in ops_signals):
        return "COO"

    # Procurement-heavy signals
    proc_signals = ["procurement", "purchasing", "sourcing", "vendor"]
    if any(s in industry for s in proc_signals) or any(s in keywords for s in proc_signals):
        return "Procurement"

    # Construction / contracting → Commercial or Ops
    if "construct" in industry or "contract" in industry or "engineer" in industry:
        return "Commercial"

    # Healthcare / pharma → Ops Head
    if "health" in industry or "medical" in industry or "pharma" in industry:
        return "Ops Head"

    # Large companies with complex trade → CFO (receivables focus)
    if employees and employees >= 500:
        return "CFO"

    # Medium companies → Finance Head
    if employees and employees >= 100:
        return "Finance Head"

    # Default for B2B
    if industry_fit == "high":
        return "CFO"
    return "CEO"


def generate_analysis(data: Dict) -> Dict:
    """
    Generate the full MUHIDE strategic analysis for a company.
    Returns dict with all output fields.
    """
    name = data.get("name") or "Unknown"
    industry = data.get("industry") or ""
    country = data.get("country") or ""
    employees = data.get("employees")
    employee_size = data.get("employee_size") or ""
    revenue = data.get("annual_revenue")
    revenue_range = data.get("revenue_range") or ""
    keywords = data.get("keywords") or ""
    technologies = data.get("technologies") or ""
    description = data.get("short_description") or ""
    ai_qual = data.get("ai_qualification_status") or ""
    ai_detail = data.get("ai_qualification_detail") or ""

    # ─── SCORING ───
    industry_fit, industry_score = classify_industry(industry)
    size_score = score_company_size(employees, employee_size, revenue, revenue_range)
    keyword_score = score_keywords(keywords, technologies, description)
    geo_score = score_geography(country)
    growth_score = score_growth_signals(data)

    # Total score (0-100)
    raw_score = industry_score + size_score + keyword_score + geo_score + growth_score
    fit_score = max(1, min(100, raw_score))

    # ─── CLASSIFICATION ───
    if fit_score >= 70:
        strategic_fit = "High"
        commercial_potential = "High"
        priority = "P1"
    elif fit_score >= 45:
        strategic_fit = "Medium"
        commercial_potential = "Medium"
        priority = "P2"
    else:
        strategic_fit = "Low"
        commercial_potential = "Low"
        priority = "P3"

    # Confidence assessment
    data_richness = sum([
        bool(industry), bool(employees or employee_size),
        bool(revenue or revenue_range), bool(keywords),
        bool(description), bool(country), bool(technologies),
    ])
    if data_richness >= 5:
        confidence = "High"
    elif data_richness >= 3:
        confidence = "Medium"
    else:
        confidence = "Low"

    # Best buyer
    best_buyer = determine_best_buyer(data, industry_fit)

    # ─── GENERATE ANALYSIS TEXT ───
    why_relevant = _generate_why_relevant(data, industry_fit, fit_score)
    pain_points = _generate_pain_points(data, industry_fit)
    outreach_angle = _generate_outreach_angle(data, industry_fit, best_buyer)
    pitch = _generate_pitch(data, industry_fit, best_buyer)

    analysis_text = (
        f"Strategic Fit: {strategic_fit}\n"
        f"Commercial Potential: {commercial_potential}\n"
        f"Why Relevant: {why_relevant}\n"
        f"Likely Pain Points: {pain_points}\n"
        f"Best Entry Angle: {best_buyer}\n"
        f"Recommended Pitch: {pitch}\n"
        f"Priority: {priority}\n"
        f"Confidence: {confidence}"
    )

    return {
        "page_id": data["page_id"],
        "name": name,
        "analysis_text": analysis_text,
        "fit_score": fit_score,
        "priority": priority,
        "best_buyer": best_buyer,
        "outreach_angle": outreach_angle,
        "strategic_fit": strategic_fit,
        "confidence": confidence,
    }


def _generate_why_relevant(data: Dict, industry_fit: str, score: int) -> str:
    """Generate the 'Why Relevant' section."""
    name = data.get("name") or "This company"
    industry = data.get("industry") or ""
    employees = data.get("employees")
    description = data.get("short_description") or ""
    country = data.get("country") or ""
    revenue_range = data.get("revenue_range") or ""
    keywords = data.get("keywords") or ""

    parts = []

    if industry_fit == "high":
        if industry:
            parts.append(f"{name} operates in {industry}, a sector with inherent B2B trade complexity, multi-party transactions, and delivery validation needs.")
        else:
            parts.append(f"{name} shows strong signals of B2B operational complexity based on available data.")

        if employees and employees >= 200:
            parts.append(f"At {int(employees):,}+ employees, the organization likely manages significant supplier/buyer relationships with open-credit exposure.")
        elif employees and employees >= 50:
            parts.append(f"With {int(employees)} employees, the company is at a scale where trade governance gaps create real financial risk.")

        if description:
            # Extract relevant business model clues
            desc_lower = description.lower()
            if any(w in desc_lower for w in ["supply", "deliver", "distribut", "manufactur", "logistic", "procure"]):
                parts.append(f"Business profile suggests active supply chain and delivery operations where MUHIDE's document authentication adds direct value.")

    elif industry_fit in ("medium", "medium-low"):
        if industry:
            parts.append(f"{name} is in {industry}, which may involve B2B transactions but with less inherent trade governance complexity than core target sectors.")
        else:
            parts.append(f"Limited industry data available. Company may have B2B relevance but requires further qualification.")

        if employees and employees >= 500:
            parts.append(f"Size ({int(employees):,} employees) suggests operational complexity where receivables management and trade documentation could be pain points.")

    else:  # low
        if industry:
            parts.append(f"{name} operates in {industry}, which typically has limited B2B open-credit trade complexity.")
        else:
            parts.append(f"Insufficient data to determine strong MUHIDE relevance.")
        parts.append("May warrant revisit if deeper qualification reveals B2B procurement or supply chain operations.")

    # Geographic relevance
    if country:
        c_lower = country.lower()
        is_mena = any(pc in c_lower for pc in PRIORITY_COUNTRIES)
        if is_mena:
            parts.append(f"Located in {country} — a priority market for MUHIDE with significant trade governance gaps in the region.")

    if not parts:
        parts.append("Insufficient data for detailed relevance assessment. Recommend manual qualification.")

    return " ".join(parts[:4])  # Cap at 4 sentences


def _generate_pain_points(data: Dict, industry_fit: str) -> str:
    """Generate likely pain points MUHIDE solves."""
    industry = (data.get("industry") or "").lower()
    keywords = (data.get("keywords") or "").lower()
    description = (data.get("short_description") or "").lower()
    employees = data.get("employees") or 0
    combined = f"{industry} {keywords} {description}"

    pains = []

    # Industry-specific pain points
    if any(w in combined for w in ["construct", "contract", "engineer", "building"]):
        pains.extend(["Progress payment disputes on project milestones",
                       "Delivery proof gaps for materials and subcontractor work",
                       "Cash flow strain from delayed payment verification"])

    elif any(w in combined for w in ["manufactur", "industrial", "machin", "equipment"]):
        pains.extend(["Purchase order vs delivery discrepancies",
                       "Receivables aging from unverified shipments",
                       "Supplier payment disputes delaying production"])

    elif any(w in combined for w in ["logistic", "transport", "freight", "shipping", "warehouse"]):
        pains.extend(["Proof of delivery documentation gaps",
                       "Multi-party handoff disputes in supply chain",
                       "Invoice reconciliation delays across logistics chain"])

    elif any(w in combined for w in ["health", "medical", "pharma", "hospital"]):
        pains.extend(["Procurement verification for regulated supplies",
                       "Payment disputes on medical equipment deliveries",
                       "Compliance documentation for supply chain auditability"])

    elif any(w in combined for w in ["wholesale", "distribut", "import", "export", "trade"]):
        pains.extend(["Open-credit exposure across multiple buyers",
                       "Delivery confirmation gaps in distribution chain",
                       "Receivables financing readiness — banks need verified proof"])

    elif any(w in combined for w in ["oil", "gas", "energy", "mining", "chemical"]):
        pains.extend(["Large-value delivery verification for bulk commodities",
                       "Multi-party trade document authentication needs",
                       "Working capital tied up in unverified receivables"])

    elif any(w in combined for w in ["food", "beverage", "dairy", "agri", "farm"]):
        pains.extend(["Perishable delivery verification urgency",
                       "Distributor payment disputes on partial shipments",
                       "Receivables proof for trade financing"])

    elif any(w in combined for w in ["financ", "bank", "insurance", "lending"]):
        pains.extend(["Need for verified trade documents to underwrite receivables",
                       "Credit risk assessment gaps in B2B lending portfolios",
                       "Lack of standardized delivery/execution proof from SME clients"])

    elif any(w in combined for w in ["real estate", "property", "facility"]):
        pains.extend(["Contractor payment verification for project work",
                       "Service delivery documentation for facility management",
                       "Vendor payment disputes on recurring service contracts"])

    elif any(w in combined for w in ["telecom", "utilit"]):
        pains.extend(["B2B service delivery verification for enterprise clients",
                       "Vendor/contractor payment disputes on infrastructure work",
                       "Receivables from corporate accounts need better documentation"])

    # Generic B2B pain points if industry-specific ones not found
    if not pains:
        if industry_fit == "high":
            pains = ["Payment disputes from unverified delivery/execution",
                     "Working capital friction from slow receivables processes",
                     "Lack of digital trade governance between supplier and buyer"]
        elif industry_fit in ("medium", "medium-low"):
            pains = ["Potential receivables management inefficiencies",
                     "May face delivery/service verification gaps in B2B operations"]
        else:
            pains = ["Limited apparent trade governance pain points based on available data"]

    return "; ".join(pains[:3])


def _generate_outreach_angle(data: Dict, industry_fit: str, best_buyer: str) -> str:
    """Generate a short tailored outreach hook."""
    industry = (data.get("industry") or "").lower()
    name = data.get("name") or "your company"
    employees = data.get("employees") or 0

    if industry_fit == "high":
        if "construct" in industry or "building" in industry:
            return f"How {name} can eliminate payment disputes on project deliveries and accelerate receivables collection with digital proof of execution."
        elif "manufactur" in industry or "industrial" in industry:
            return f"Digitizing delivery verification to cut receivables aging and eliminate supplier payment disputes at {name}."
        elif "logistic" in industry or "transport" in industry or "freight" in industry:
            return f"Turning proof-of-delivery into bankable receivables — how {name} can reduce DSO and payment disputes."
        elif "health" in industry or "medical" in industry:
            return f"Streamlining procurement verification and payment proof for {name}'s supply chain."
        elif "wholesale" in industry or "distribut" in industry:
            return f"Reducing open-credit risk across {name}'s distribution chain with authenticated delivery proof."
        elif "oil" in industry or "gas" in industry or "energy" in industry:
            return f"Securing large-value trade documentation and accelerating receivables financing for {name}."
        elif "food" in industry or "beverage" in industry:
            return f"Eliminating delivery disputes and improving receivables proof for {name}'s distribution operations."
        elif "financ" in industry or "bank" in industry or "insurance" in industry:
            return f"How MUHIDE gives {name} verified trade documents to de-risk B2B lending and credit decisions."
        elif "real estate" in industry or "facility" in industry:
            return f"Digital proof of service execution to reduce contractor payment disputes at {name}."
        else:
            return f"How {name} can digitize trade governance, reduce payment disputes, and make receivables bankable."

    elif industry_fit in ("medium", "medium-low"):
        return f"Exploring how {name} manages B2B delivery verification and receivables — MUHIDE may reduce friction in your trade operations."

    else:
        return f"Qualification call to assess whether {name} has B2B trade governance needs that MUHIDE addresses."


def _generate_pitch(data: Dict, industry_fit: str, best_buyer: str) -> str:
    """Generate 1-2 line tailored pitch."""
    industry = (data.get("industry") or "").lower()

    if best_buyer == "CFO":
        return "MUHIDE reduces DSO uncertainty and makes your receivables financing-ready by digitally authenticating every delivery and trade document."
    elif best_buyer == "COO":
        return "MUHIDE gives you digital proof of every delivery and execution milestone — eliminating disputes and accelerating payment cycles."
    elif best_buyer == "Procurement":
        return "MUHIDE creates a verified paper trail between you and every supplier, reducing procurement disputes and strengthening vendor accountability."
    elif best_buyer == "Commercial":
        return "MUHIDE authenticates project deliveries and execution milestones, giving you indisputable proof when collecting from clients."
    elif best_buyer == "Ops Head":
        return "MUHIDE digitizes delivery and execution proof across your operations, reducing disputes and freeing up working capital."
    elif best_buyer == "Finance Head":
        return "MUHIDE turns your delivery documentation into verified receivables that banks trust — reducing DSO and improving cash flow."
    elif best_buyer == "Founder" or best_buyer == "CEO":
        if industry_fit == "high":
            return "MUHIDE is the missing layer between your deliveries and your payments — digital trade governance that makes your receivables bankable."
        else:
            return "MUHIDE helps B2B companies reduce payment disputes and improve receivables credibility through digital trade document authentication."

    return "MUHIDE digitizes trade governance between supplier and buyer — reducing disputes, accelerating payments, and making receivables financeable."


# ═══════════════════════════════════════════════════════════════════════════════
# NOTION READ / WRITE
# ═══════════════════════════════════════════════════════════════════════════════

def fetch_all_companies(limit: int = 0) -> List[Dict]:
    """Fetch companies from Notion, paginated. If limit > 0, stop early."""
    all_companies = []
    has_more = True
    start_cursor = None
    batch = 0

    logger.info("Fetching companies from Notion...")

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

        pages = data.get("results", [])
        for page in pages:
            company = extract_company_data(page)
            all_companies.append(company)
            if limit and len(all_companies) >= limit:
                logger.info(f"Reached limit of {limit} companies, stopping fetch.")
                return all_companies

        batch += 1
        has_more = data.get("has_more", False)
        start_cursor = data.get("next_cursor")

        if batch % 10 == 0:
            logger.info(f"  Fetched {len(all_companies)} companies so far...")

    logger.info(f"Total companies fetched: {len(all_companies)}")
    return all_companies


def _fast_notion_patch(page_id: str, properties: Dict, max_retries: int = 5) -> bool:
    """Fast Notion PATCH — no shared rate limiter, uses retry-on-429 instead."""
    import requests as req
    url = f"{NOTION_BASE_URL}/pages/{page_id}"
    headers = notion_headers()
    payload = {"properties": properties}

    for attempt in range(max_retries):
        try:
            resp = req.patch(url, json=payload, headers=headers, timeout=30)
        except (req.exceptions.Timeout, req.exceptions.ConnectionError) as e:
            if attempt < max_retries - 1:
                time.sleep(min(2 ** attempt, 15))
                continue
            raise
        if resp.status_code == 429:
            wait = float(resp.headers.get("Retry-After", min(2 ** attempt, 30)))
            time.sleep(wait)
            continue
        if resp.status_code >= 500:
            time.sleep(min(2 ** attempt, 15))
            continue
        if resp.status_code >= 400:
            logger.error(f"Notion {resp.status_code}: {resp.text[:200]}")
            return False
        return True
    return False


def write_analysis_to_notion(result: Dict, dry_run: bool = False) -> bool:
    """Write analysis results to a single Notion company page."""
    page_id = result["page_id"]
    name = result["name"]

    properties = {
        "MUHIDE Strategic Analysis": {
            "rich_text": [{
                "type": "text",
                "text": {"content": result["analysis_text"][:2000]}
            }]
        },
        "MUHIDE Fit Score": {
            "number": result["fit_score"]
        },
        "MUHIDE Priority": {
            "select": {"name": result["priority"]}
        },
        "MUHIDE Best Buyer": {
            "select": {"name": result["best_buyer"]}
        },
        "MUHIDE Outreach Angle": {
            "rich_text": [{
                "type": "text",
                "text": {"content": result["outreach_angle"][:2000]}
            }]
        },
    }

    if dry_run:
        logger.info(f"[DRY RUN] Would write to '{name}': Score={result['fit_score']}, Priority={result['priority']}, Fit={result['strategic_fit']}")
        return True

    try:
        return _fast_notion_patch(page_id, properties)
    except Exception as e:
        logger.error(f"Failed to write to '{name}' ({page_id}): {e}")
        return False


# ═══════════════════════════════════════════════════════════════════════════════
# CHECKPOINT
# ═══════════════════════════════════════════════════════════════════════════════

CHECKPOINT_FILE = "muhide_analysis_checkpoint.json"

def save_checkpoint(processed_ids: set, stats: Dict):
    """Save progress checkpoint."""
    with open(CHECKPOINT_FILE, "w") as f:
        json.dump({
            "processed_ids": list(processed_ids),
            "stats": stats,
            "timestamp": datetime.now().isoformat(),
        }, f)

def load_checkpoint() -> Tuple[set, Dict]:
    """Load progress from checkpoint."""
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE) as f:
            data = json.load(f)
            return set(data.get("processed_ids", [])), data.get("stats", {})
    return set(), {}


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="MUHIDE Strategic Analysis Engine")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing")
    parser.add_argument("--limit", type=int, help="Process first N companies only")
    parser.add_argument("--resume", action="store_true", help="Resume from checkpoint")
    parser.add_argument("--workers", type=int, default=3, help="Parallel write workers (default 3)")
    args = parser.parse_args()

    logger.info("=" * 70)
    logger.info("MUHIDE STRATEGIC ANALYSIS ENGINE")
    logger.info(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE'}")
    if args.limit:
        logger.info(f"Limit: {args.limit} companies")
    logger.info("=" * 70)

    # Load checkpoint if resuming
    processed_ids = set()
    if args.resume:
        processed_ids, prev_stats = load_checkpoint()
        logger.info(f"Resuming from checkpoint: {len(processed_ids)} already processed")

    # Step 1: Fetch all companies
    start_time = time.time()
    companies = fetch_all_companies(limit=args.limit if args.limit and not args.resume else 0)

    # Filter out already-processed if resuming
    if processed_ids:
        companies = [c for c in companies if c["page_id"] not in processed_ids]
        logger.info(f"After filtering checkpoint: {len(companies)} remaining")

    # Step 2: Analyze all companies
    logger.info(f"\nAnalyzing {len(companies)} companies...")
    results = []
    stats = {
        "total": len(companies),
        "high_fit": 0,
        "medium_fit": 0,
        "low_fit": 0,
        "p1": 0,
        "p2": 0,
        "p3": 0,
        "written": 0,
        "failed": 0,
        "low_confidence": 0,
    }

    for i, company in enumerate(companies):
        result = generate_analysis(company)
        results.append(result)

        # Track stats
        sf = result["strategic_fit"]
        if sf == "High":
            stats["high_fit"] += 1
        elif sf == "Medium":
            stats["medium_fit"] += 1
        else:
            stats["low_fit"] += 1

        if result["priority"] == "P1":
            stats["p1"] += 1
        elif result["priority"] == "P2":
            stats["p2"] += 1
        else:
            stats["p3"] += 1

        if result["confidence"] == "Low":
            stats["low_confidence"] += 1

        if (i + 1) % 500 == 0:
            logger.info(f"  Analyzed {i + 1}/{len(companies)} companies...")

    analysis_time = time.time() - start_time
    logger.info(f"Analysis complete in {analysis_time:.1f}s")

    # Step 3: Write to Notion
    logger.info(f"\nWriting results to Notion ({'DRY RUN' if args.dry_run else 'LIVE'})...")
    write_start = time.time()

    # Parallel writes with ThreadPoolExecutor
    written_count = 0
    failed_count = 0
    lock = threading.Lock()

    def _write_one(result):
        return result, write_analysis_to_notion(result, dry_run=args.dry_run)

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(_write_one, r): r for r in results}
        for i, future in enumerate(as_completed(futures)):
            result, success = future.result()
            with lock:
                if success:
                    stats["written"] += 1
                    written_count += 1
                    processed_ids.add(result["page_id"])
                else:
                    stats["failed"] += 1
                    failed_count += 1

                done = written_count + failed_count
                if done % 200 == 0:
                    elapsed = time.time() - write_start
                    rate = done / elapsed if elapsed > 0 else 0
                    remaining = (len(results) - done) / rate if rate > 0 else 0
                    logger.info(
                        f"  Written {done}/{len(results)} "
                        f"({rate:.1f}/sec, ~{remaining/60:.0f}min remaining)"
                    )
                    if not args.dry_run:
                        save_checkpoint(processed_ids, stats)

    write_time = time.time() - write_start
    total_time = time.time() - start_time

    # Final checkpoint
    if not args.dry_run:
        save_checkpoint(processed_ids, stats)

    # ─── SUMMARY REPORT ───
    logger.info("\n" + "=" * 70)
    logger.info("MUHIDE STRATEGIC ANALYSIS — EXECUTION SUMMARY")
    logger.info("=" * 70)
    logger.info(f"Total Companies Processed: {stats['total']}")
    logger.info(f"  High Fit:   {stats['high_fit']} ({stats['high_fit']/max(stats['total'],1)*100:.1f}%)")
    logger.info(f"  Medium Fit: {stats['medium_fit']} ({stats['medium_fit']/max(stats['total'],1)*100:.1f}%)")
    logger.info(f"  Low Fit:    {stats['low_fit']} ({stats['low_fit']/max(stats['total'],1)*100:.1f}%)")
    logger.info(f"Priority Distribution:")
    logger.info(f"  P1 (Immediate): {stats['p1']}")
    logger.info(f"  P2 (Qualified):  {stats['p2']}")
    logger.info(f"  P3 (Monitor):    {stats['p3']}")
    logger.info(f"Written: {stats['written']} | Failed: {stats['failed']}")
    logger.info(f"Low Confidence (sparse data): {stats['low_confidence']}")
    logger.info(f"Timing: Analysis {analysis_time:.0f}s + Write {write_time:.0f}s = {total_time:.0f}s total")
    logger.info("=" * 70)

    # Save stats JSON
    stats_file = "muhide_analysis_stats.json"
    stats["analysis_time_sec"] = round(analysis_time, 1)
    stats["write_time_sec"] = round(write_time, 1)
    stats["total_time_sec"] = round(total_time, 1)
    stats["timestamp"] = datetime.now().isoformat()
    with open(stats_file, "w") as f:
        json.dump(stats, f, indent=2)
    logger.info(f"Stats saved to {stats_file}")

    return stats


if __name__ == "__main__":
    main()
