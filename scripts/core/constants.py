#!/usr/bin/env python3
"""
AI Sales OS — Constants & Field Names
Unified field names used across ALL scripts.
Change a name here → changes everywhere.
"""

# ═══════════════════════════════════════════════════════════════════════════════
# CONTACTS FIELDS (Notion property names)
# ═══════════════════════════════════════════════════════════════════════════════

FIELD_FULL_NAME = "Full Name"
FIELD_FIRST_NAME = "First Name"
FIELD_LAST_NAME = "Last Name"
FIELD_EMAIL = "Email"
FIELD_EMAIL_STATUS = "Email Status"
FIELD_TITLE = "Title"
FIELD_SENIORITY = "Seniority"
FIELD_DEPARTMENTS = "Departments"
FIELD_CITY = "City"
FIELD_STATE = "State"
FIELD_COUNTRY = "Country"
FIELD_LINKEDIN = "Person Linkedin Url"
FIELD_WORK_PHONE = "Work Direct Phone"
FIELD_MOBILE_PHONE = "Mobile Phone"
FIELD_HOME_PHONE = "Home Phone"
FIELD_CORPORATE_PHONE = "Corporate Phone"
FIELD_OTHER_PHONE = "Other Phone"

# Engagement booleans
FIELD_EMAIL_SENT = "Email Sent"
FIELD_EMAIL_OPENED = "Email Opened"
FIELD_EMAIL_BOUNCED = "Email Bounced"
FIELD_REPLIED = "Replied"
FIELD_MEETING_BOOKED = "Meeting Booked"
FIELD_DEMOED = "Demoed"

# Engagement counts (synced from Apollo Analytics)
FIELD_EMAIL_OPEN_COUNT = "Email Open Count"
FIELD_EMAILS_SENT_COUNT = "Emails Sent Count"
FIELD_EMAILS_REPLIED_COUNT = "Emails Replied Count"

# Stage & Status
FIELD_LAST_CONTACTED = "Last Contacted"
FIELD_OUTREACH_STATUS = "Outreach Status"
FIELD_STAGE = "Stage"
FIELD_DO_NOT_CALL = "Do Not Call"
FIELD_QUALIFICATION_STATUS = "Qualification Status"
FIELD_REPLY_STATUS = "Reply Status"

# Apollo IDs
FIELD_APOLLO_CONTACT_ID = "Apollo Contact Id"
FIELD_APOLLO_ACCOUNT_ID = "Apollo Account Id"

# Scoring
FIELD_LEAD_SCORE = "Lead Score"
FIELD_LEAD_TIER = "Lead Tier"
FIELD_ACTION_READY = "Action Ready"
FIELD_INTENT_SCORE_PRIMARY = "Primary Intent Score"
FIELD_INTENT_SCORE_SECONDARY = "Secondary Intent Score"

# Feedback / Outcome tracking
FIELD_CONTACT_RESPONDED = "Contact Responded"
FIELD_OPPORTUNITY_CREATED = "Opportunity Created"
FIELD_FIRST_CONTACT_ATTEMPT = "First Contact Attempt"

# Signals (synced from Apollo)
FIELD_INTENT_STRENGTH = "Intent Strength"
FIELD_JOB_CHANGE_EVENT = "Job Change Event"
FIELD_JOB_CHANGE_DATE = "Job Change Date"

# Apollo AI Fields (typed_custom_fields IDs)
APOLLO_AI_CONTACT_DECISION_ID = "6913a64c52c2780001146ce9"
APOLLO_AI_ICP_ANALYSIS_ID = "6913a64c52c2780001146cfd"
APOLLO_AI_RESEARCH_ID = "6913a64c52c2780001146d0e"
APOLLO_AI_QUALIFICATION_ID = "6913a64c52c2780001146d22"
# AI Sales Actions — Apollo account-level directive block (Segment/Fit/Priority/
# Urgency/Signal/Pain/Target Role/Action/Tone/Call Hook/Email...).
# Source: verified via apollo_mixed_companies_search on 2026-04-11 (KAFD, stc).
# Parsed by scripts/core/ai_sales_actions_parser.py.
APOLLO_AI_SALES_ACTIONS_ID = "69d979efebf741000dfbce23"

FIELD_AI_DECISION = "AI Decision"
FIELD_AI_QUALIFICATION_STATUS = "AI Qualification Status"
FIELD_AI_QUALIFICATION_DETAIL = "AI Qualification Detail"

# ═══════════════════════════════════════════════════════════════════════════════
# AI SALES ACTIONS (Apollo account-level directive field, parsed by
# scripts/core/ai_sales_actions_parser.py and applied by
# scripts/enrichment/ai_sales_actions_enricher.py)
# ═══════════════════════════════════════════════════════════════════════════════

# Raw Apollo field — the unstructured block we parse
FIELD_AI_SALES_ACTIONS_RAW = "AI Sales Actions"

# Companies DB — parsed sub-fields (rich_text / select)
FIELD_AI_PRIORITY = "AI Priority"              # select: P1 / P2 / P3
FIELD_AI_FIT = "AI Fit"                        # select: High / Medium / Low
FIELD_AI_URGENCY = "AI Urgency"                # select: High / Medium / Low
FIELD_AI_SEGMENT = "AI Segment"                # rich_text
FIELD_AI_SIGNAL = "AI Signal"                  # rich_text
FIELD_AI_PAIN_SUMMARY = "AI Pain Summary"      # rich_text
FIELD_AI_TARGET_ROLE = "AI Target Role"        # rich_text
FIELD_AI_ACTION_TYPE = "AI Action Type"        # select: Call / Email / Sequence / None
FIELD_AI_TONE = "AI Tone"                      # rich_text
FIELD_AI_SALES_ACTIONS_PARSED_AT = "AI Sales Actions Parsed At"  # date

# Contacts DB — propagated from Company + per-contact email copy
FIELD_AI_CALL_HOOK = "AI Call Hook"            # rich_text (bullets joined)
FIELD_AI_EMAIL_SUBJECT = "AI Email Subject"    # rich_text
FIELD_AI_EMAIL_OPENING = "AI Email Opening"    # rich_text
FIELD_AI_EMAIL_PAIN = "AI Email Pain"          # rich_text
FIELD_AI_EMAIL_VALUE = "AI Email Value"        # rich_text
FIELD_AI_EMAIL_CTA = "AI Email CTA"            # rich_text

# ─── Reply Intelligence Fields (Contacts DB) ─────────────────────────────────
FIELD_AI_REPLY_STATUS = "AI Reply Status"              # select: Interested / Soft Interest / Neutral / Soft Rejection / Hard Rejection
FIELD_AI_REPLY_REASON = "AI Reply Reason"              # select: 13 values (see below)
FIELD_AI_CLOSE_PROBABILITY = "AI Close Probability"    # number (0-100)
FIELD_AI_NEXT_ACTION = "AI Next Action"                # select: Call Now / Follow-up Email / Send Proposal / Re-engage Later / Change Stakeholder / No Action
FIELD_AI_REPLY_CONFIDENCE = "AI Reply Confidence"      # select: High / Medium / Low
FIELD_AI_REPLY_LAST_ANALYZED = "AI Reply Last Analyzed" # date (ISO 8601)

# Reply Status canonical values
AI_REPLY_STATUS_INTERESTED = "Interested"
AI_REPLY_STATUS_SOFT_INTEREST = "Soft Interest"
AI_REPLY_STATUS_NEUTRAL = "Neutral"
AI_REPLY_STATUS_SOFT_REJECTION = "Soft Rejection"
AI_REPLY_STATUS_HARD_REJECTION = "Hard Rejection"

# Reply Reason canonical values (13 values — positive, neutral, and negative reasons)
AI_REPLY_REASON_MEETING_REQUEST = "Meeting Request"
AI_REPLY_REASON_PRICING_ASK = "Pricing Ask"
AI_REPLY_REASON_INFO_REQUEST = "Info Request"
AI_REPLY_REASON_DELEGATION = "Delegation"
AI_REPLY_REASON_TIMING = "Timing"
AI_REPLY_REASON_BUDGET = "Budget"
AI_REPLY_REASON_NO_NEED = "No Need"
AI_REPLY_REASON_ALREADY_HAS_SOLUTION = "Already Has Solution"
AI_REPLY_REASON_TRUST_RISK = "Trust / Risk"
AI_REPLY_REASON_COMPLEXITY = "Complexity"
AI_REPLY_REASON_UNKNOWN = "Unknown"
AI_REPLY_REASON_GENERIC_REJECTION = "Generic Rejection"
AI_REPLY_REASON_EXPLICIT_REJECTION = "Explicit Rejection"

# Reply Next Action canonical values (NO Archive — this layer never archives)
AI_REPLY_NEXT_CALL_NOW = "Call Now"
AI_REPLY_NEXT_FOLLOW_UP_EMAIL = "Follow-up Email"
AI_REPLY_NEXT_SEND_PROPOSAL = "Send Proposal"
AI_REPLY_NEXT_RE_ENGAGE_LATER = "Re-engage Later"
AI_REPLY_NEXT_CHANGE_STAKEHOLDER = "Change Stakeholder"
AI_REPLY_NEXT_NO_ACTION = "No Action"

# Reply Confidence canonical values
AI_REPLY_CONFIDENCE_HIGH = "High"
AI_REPLY_CONFIDENCE_MEDIUM = "Medium"
AI_REPLY_CONFIDENCE_LOW = "Low"

# AI Action Type canonical values
AI_ACTION_CALL = "Call"
AI_ACTION_EMAIL = "Email"
AI_ACTION_SEQUENCE = "Sequence"
AI_ACTION_NONE = "None"

# AI Priority canonical values
AI_PRIORITY_P1 = "P1"
AI_PRIORITY_P2 = "P2"
AI_PRIORITY_P3 = "P3"

# Scoring boost values (Phase 5: conservative, additive, capped at 100)
AI_PRIORITY_BOOST = {
    "P1": 8.0,
    "P2": 4.0,
    "P3": 0.0,
}
AI_FIT_BOOST = {
    "High": 4.0,
    "Medium": 2.0,
    "Low": 0.0,
}
# Max total AI-driven boost (hard cap to keep scoring conservative)
AI_SCORE_BOOST_MAX = 12.0

# Ownership — Contact Level
FIELD_CONTACT_OWNER = "Contact Owner"

# Ownership — Company Level (v5.0 Company-Centric)
FIELD_COMPANY_OWNERS = "Company Owners"              # legacy: all owners comma-separated
FIELD_PRIMARY_COMPANY_OWNER = "Primary Company Owner" # select: single accountable owner
FIELD_SUPPORTING_OWNERS = "Supporting Owners"          # rich_text: other owners

# Company-Centric Lifecycle & Metrics (v5.0)
FIELD_COMPANY_STAGE = "Company Stage"                  # select: Prospect/Outreach/Engaged/Meeting/Opportunity/Customer/Churned/Archived
FIELD_ACTIVE_CONTACTS = "Active Contacts"              # number
FIELD_EMAILED_CONTACTS = "Emailed Contacts"            # number
FIELD_ENGAGED_CONTACTS = "Engaged Contacts"            # number
FIELD_LAST_ENGAGEMENT_DATE = "Last Engagement Date"    # date
FIELD_ACCOUNT_ENGAGEMENT_SCORE = "Account Engagement Score"  # number 0-100
FIELD_BUYING_COMMITTEE_STRENGTH = "Buying Committee Strength"  # select: Strong/Moderate/Weak
FIELD_COMPANY_HEALTH = "Company Health"                # select: Green/Yellow/Red
FIELD_SALES_OS_ACTIVE = "Sales OS Active"              # checkbox

# Company Stage values
COMPANY_STAGE_PROSPECT = "Prospect"
COMPANY_STAGE_OUTREACH = "Outreach"
COMPANY_STAGE_ENGAGED = "Engaged"
COMPANY_STAGE_MEETING = "Meeting"
COMPANY_STAGE_OPPORTUNITY = "Opportunity"
COMPANY_STAGE_CUSTOMER = "Customer"
COMPANY_STAGE_CHURNED = "Churned"
COMPANY_STAGE_ARCHIVED = "Archived"

# ─── Stage Priority Lattice (2026-04-11) ────────────────────────────────────
# Defines the one-way direction Company Stage is allowed to move in.
# Higher number = higher priority. A writer MUST never decrease the stage
# unless the writer is the authoritative owner for that lower stage AND has
# explicit business reason (e.g. governance archival of customer-churned).
#
# This lattice is enforced by `is_stage_regression()` below and is used by:
#   • daily_sync.compute_company_stage   (writes Prospect/Outreach/Engaged)
#   • meeting_tracker.update_company_stage_to_meeting (writes Meeting)
#   • opportunity_manager.update_company_stage_to_opportunity (writes Opportunity)
#   • data_governor._archive_company     (writes Archived — terminal)
#
# Archived is terminal: nothing upgrades out of it except manual operator action.
STAGE_PRIORITY = {
    COMPANY_STAGE_PROSPECT: 1,
    COMPANY_STAGE_OUTREACH: 2,
    COMPANY_STAGE_ENGAGED: 3,
    COMPANY_STAGE_MEETING: 4,
    COMPANY_STAGE_OPPORTUNITY: 5,
    COMPANY_STAGE_CUSTOMER: 6,
    COMPANY_STAGE_CHURNED: 7,   # terminal but higher priority than Customer
    COMPANY_STAGE_ARCHIVED: 8,  # terminal — governance only
}

# Stages that must never be downgraded by automation.
# Manual Notion edits can still change them, but automation scripts read from
# Notion, see one of these, and refuse to write a lower-priority stage.
STAGE_TERMINAL = {COMPANY_STAGE_CUSTOMER, COMPANY_STAGE_CHURNED, COMPANY_STAGE_ARCHIVED}


def is_stage_regression(current_stage: str, new_stage: str) -> bool:
    """Return True if writing `new_stage` over `current_stage` would be a
    regression (a move to a lower-priority stage).

    Unknown stages are treated as priority 0 — they are always allowed to be
    overwritten. This is deliberate: we do not want a typo to lock a page.
    """
    if not current_stage:
        return False
    cur = STAGE_PRIORITY.get(current_stage, 0)
    nxt = STAGE_PRIORITY.get(new_stage, 0)
    return nxt < cur


# ─── Pipeline Freshness (2026-04-11) ────────────────────────────────────────
# Any decision that relies on "engagement data" (analytics_tracker output,
# outcome_tracker output, meeting_tracker output) must verify that the
# upstream writer has produced a recent stats file. If the stats file is
# older than FRESHNESS_MAX_AGE_HOURS the caller should skip archive /
# regression decisions and log a loud timing warning.
#
# 26h = daily run + 2h slack for weekend / retry drift.
FRESHNESS_MAX_AGE_HOURS = 26

# Stats files produced by the signal-enrichment phase. The freshness guard
# checks the mtime of whichever of these exist.
FRESHNESS_STATS_FILES = (
    "enrichment/last_analytics_stats.json",
    "automation/last_outcome_stats.json",
    "meetings/last_meeting_tracker_stats.json",
)


def check_pipeline_freshness(base_dir: str = None, max_age_hours: int = None) -> dict:
    """Check whether signal-enrichment stats files are recent.

    Returns a dict:
        {
            "fresh": bool,
            "checked": [ {file, age_hours, exists, fresh}, ... ],
            "max_age_hours": int,
            "oldest_age_hours": float | None,
        }

    `fresh` is True only if ALL existing stats files are within the window.
    Missing files are treated as NOT fresh (can't prove data landed).
    """
    import os as _os
    import time as _time

    if max_age_hours is None:
        max_age_hours = FRESHNESS_MAX_AGE_HOURS
    if base_dir is None:
        base_dir = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))

    now = _time.time()
    checks = []
    worst_age = None
    all_fresh = True

    for rel_path in FRESHNESS_STATS_FILES:
        full = _os.path.join(base_dir, rel_path)
        exists = _os.path.exists(full)
        if not exists:
            checks.append({
                "file": rel_path, "exists": False,
                "age_hours": None, "fresh": False,
            })
            all_fresh = False
            continue
        age_s = now - _os.path.getmtime(full)
        age_h = age_s / 3600.0
        is_fresh = age_h <= max_age_hours
        if not is_fresh:
            all_fresh = False
        if worst_age is None or age_h > worst_age:
            worst_age = age_h
        checks.append({
            "file": rel_path, "exists": True,
            "age_hours": round(age_h, 2), "fresh": is_fresh,
        })

    return {
        "fresh": all_fresh,
        "checked": checks,
        "max_age_hours": max_age_hours,
        "oldest_age_hours": round(worst_age, 2) if worst_age is not None else None,
    }

# Contacts — Company-Centric additions (v5.0)
FIELD_ROLE_IN_ACCOUNT = "Role in Account"              # select: Champion/Decision Maker/Influencer/Blocker/End User/Unknown
FIELD_STAKEHOLDER_PRIORITY = "Stakeholder Priority"    # select: Primary/Secondary/Tertiary
FIELD_ACTIVE_IN_SALES_OS = "Active in Sales OS"        # checkbox
FIELD_ARCHIVE_REASON = "Archive Reason"                # select: No Owner/No Email/Bounced/DNC/Manual

# Tasks — Company-Centric additions (v5.0)
FIELD_TASK_OWNER = "Task Owner"                        # select: Ibrahim/Ragheed/Soha
FIELD_OWNER_SOURCE = "Owner Source"                    # select: Company Primary/Contact Owner/Manual
FIELD_COMPANY_STAGE_AT_CREATION = "Company Stage at Creation"  # rich_text

# Meetings — Company-Centric additions (v5.0)
FIELD_MEETING_OWNER = "Meeting Owner"                  # select: Ibrahim/Ragheed/Soha
FIELD_MEETING_PARTICIPANTS = "Participants"             # rich_text
FIELD_OUTCOME_IMPACT = "Outcome Impact"                # select: Stage Advance/No Change/Stage Regress
FIELD_NEXT_STEP_OWNER = "Next Step Owner"              # select: Ibrahim/Ragheed/Soha

# Opportunities — Company-Centric additions (v5.0)
FIELD_OPP_STAKEHOLDER_CONTACTS = "Stakeholder Contacts"  # relation (multi)
FIELD_OPP_COMPANY_OWNER_SNAPSHOT = "Company Owner Snapshot"  # rich_text
FIELD_OPP_BUYING_COMMITTEE_SIZE = "Buying Committee Size"    # number
FIELD_OPP_DECISION_MAKER_IDENTIFIED = "Decision Maker Identified"  # checkbox
FIELD_OPP_REVENUE_PRIORITY = "Revenue Priority"        # select: Tier 1/Tier 2/Tier 3

# Apollo User ID → Display Name mapping
# These are the team members who own contacts in Apollo.
APOLLO_OWNER_MAP = {
    "67cfce7e366f0d000dd6a10d": "Ibrahim",
    "68a5a043e0c973001d8c35b4": "Ragheed",
    "68d55ac428d3f4000d260a02": "Soha",
}

# Team members set (for quick membership checks)
TEAM_MEMBERS = set(APOLLO_OWNER_MAP.values())

# Campaign statuses that indicate email was NOT actually sent
CAMPAIGN_FAILED_STATUSES = {"failed"}

# Other
FIELD_RECORD_SOURCE = "Record Source"
FIELD_DATA_STATUS = "Data Status"
FIELD_COMPANY_NAME_FOR_EMAILS = "Company Name for Emails"

# ═══════════════════════════════════════════════════════════════════════════════
# JOB POSTINGS / INTENT PROXY FIELDS
# ═══════════════════════════════════════════════════════════════════════════════

FIELD_JOB_POSTINGS_INTENT = "Job Postings Intent"

# ═══════════════════════════════════════════════════════════════════════════════
# COMPANIES FIELDS
# ═══════════════════════════════════════════════════════════════════════════════

FIELD_COMPANY_NAME = "Company Name"
FIELD_DOMAIN = "Domain"
FIELD_WEBSITE = "Website"
FIELD_INDUSTRY = "Industry"
FIELD_EMPLOYEES = "Employees"
FIELD_EMPLOYEE_SIZE = "Employee Size"
FIELD_ANNUAL_REVENUE = "Annual Revenue"
FIELD_REVENUE_RANGE = "Revenue Range"
FIELD_TOTAL_FUNDING = "Total Funding"
FIELD_LATEST_FUNDING_AMOUNT = "Latest Funding Amount"
FIELD_LAST_RAISED_AT = "Last Raised At"
FIELD_COMPANY_CITY = "Company City"
FIELD_COMPANY_STATE = "Company State"
FIELD_COMPANY_COUNTRY = "Company Country"
FIELD_COMPANY_ADDRESS = "Company Address"
FIELD_COMPANY_PHONE = "Company Phone"
FIELD_COMPANY_LINKEDIN = "Company Linkedin Url"
FIELD_FACEBOOK = "Facebook Url"
FIELD_TWITTER = "Twitter Url"
FIELD_KEYWORDS = "Keywords"
FIELD_TECHNOLOGIES = "Technologies"
FIELD_SHORT_DESCRIPTION = "Short Description"
FIELD_ACCOUNT_STAGE = "Account Stage"
FIELD_HEADCOUNT_GROWTH_6M = "Headcount Growth 6M"
FIELD_HEADCOUNT_GROWTH_12M = "Headcount Growth 12M"
FIELD_HEADCOUNT_GROWTH_24M = "Headcount Growth 24M"

# ═══════════════════════════════════════════════════════════════════════════════
# TASKS FIELDS
# ═══════════════════════════════════════════════════════════════════════════════

FIELD_TASK_TITLE = "Task Title"
FIELD_TASK_PRIORITY = "Priority"
FIELD_TASK_STATUS = "Status"
FIELD_TASK_DUE_DATE = "Due Date"
FIELD_TASK_START_DATE = "Start Date"
FIELD_TASK_TYPE = "Task Type"
FIELD_TASK_TEAM = "Team"
FIELD_TASK_CONTACT = "Contact"
FIELD_TASK_COMPANY = "Company"
FIELD_TASK_OPPORTUNITY = "Opportunity"
FIELD_TASK_CONTEXT = "Context"
FIELD_TASK_DESCRIPTION = "Description"
FIELD_TASK_EXPECTED_OUTCOME = "Expected Outcome"
FIELD_TASK_AUTO_CREATED = "Auto Created"
FIELD_TASK_AUTOMATION_TYPE = "Automation Type"
FIELD_TASK_TRIGGER_RULE = "Trigger Rule"
FIELD_TASK_COMPLETED_AT = "Completed At"

# ═══════════════════════════════════════════════════════════════════════════════
# SCORE TIERS & THRESHOLDS
# ═══════════════════════════════════════════════════════════════════════════════

TIER_HOT = "HOT"
TIER_WARM = "WARM"
TIER_COLD = "COLD"

SCORE_HOT = 80
SCORE_WARM_HIGH = 60
SCORE_WARM = 50

# ═══════════════════════════════════════════════════════════════════════════════
# SLA (hours)
# ═══════════════════════════════════════════════════════════════════════════════

SLA_HOT_HOURS = 24
SLA_WARM_HIGH_HOURS = 48
SLA_WARM_HOURS = 168  # 7 days

# ═══════════════════════════════════════════════════════════════════════════════
# SENIORITY NORMALIZATION
# Apollo sends inconsistent values: "C-Suite", "c-suite", "C suite", etc.
# ═══════════════════════════════════════════════════════════════════════════════

SENIORITY_NORMALIZE = {
    "c-suite": "C-Suite",
    "c suite": "C-Suite",
    "c_suite": "C-Suite",
    "csuite": "C-Suite",
    "vp": "VP",
    "v.p.": "VP",
    "vice president": "VP",
    "director": "Director",
    "manager": "Manager",
    "senior": "Senior",
    "entry": "Entry",
    "intern": "Intern",
    "partner": "Partner",
    "owner": "Owner",
    "founder": "Founder",
}

# Outreach statuses that block action
OUTREACH_BLOCKED = {"Do Not Contact", "Bounced", "Bad Data"}

# Outreach Status values (select options)
OUTREACH_IN_SEQUENCE = "In Sequence"
OUTREACH_SENT = "Sent"
OUTREACH_OPENED = "Opened"
OUTREACH_REPLIED = "Replied"
OUTREACH_MEETING_BOOKED = "Meeting Booked"

# Task Status values (status type)
TASK_STATUS_NOT_STARTED = "Not Started"
TASK_STATUS_IN_PROGRESS = "In Progress"
TASK_STATUS_COMPLETED = "Completed"

# Contact-Company relation field
FIELD_COMPANY_RELATION = "Company"

# ═══════════════════════════════════════════════════════════════════════════════
# MEETINGS FIELDS
# ═══════════════════════════════════════════════════════════════════════════════

FIELD_MEETING_TITLE = "Meeting Title"
FIELD_MEETING_TYPE = "Meeting Type"
FIELD_MEETING_SCHEDULED_DATE = "Scheduled Date"
FIELD_MEETING_DURATION = "Duration (min)"
FIELD_MEETING_OUTCOME = "Outcome"
FIELD_MEETING_NOTES = "Meeting Notes"
FIELD_MEETING_KEY_TAKEAWAYS = "Key Takeaways"
FIELD_MEETING_DECISION = "Decision Made"
FIELD_MEETING_NEXT_STEPS = "Next Steps"
FIELD_MEETING_LINK = "Meeting Link"
FIELD_MEETING_NUM_ATTENDEES = "Number of Attendees"
FIELD_MEETING_ORGANIZER = "Meeting Organizer"
FIELD_MEETING_TIMEZONE = "Timezone"
FIELD_MEETING_CONTACT = "Primary Contact"
FIELD_MEETING_COMPANY = "Company"
FIELD_MEETING_OPPORTUNITY = "Opportunity"
FIELD_MEETING_AGENDA = "Agenda"

# Meeting Type values
MEETING_TYPE_DISCOVERY = "Discovery"
MEETING_TYPE_DEMO = "Demo"
MEETING_TYPE_PROPOSAL = "Proposal"
MEETING_TYPE_REVIEW = "Review"
MEETING_TYPE_FOLLOWUP = "Follow-up"
MEETING_TYPE_OTHER = "Other"

# Meeting Outcome values
MEETING_OUTCOME_POSITIVE = "Positive"
MEETING_OUTCOME_NEUTRAL = "Neutral"
MEETING_OUTCOME_NEGATIVE = "Negative"
MEETING_OUTCOME_NO_SHOW = "No Show"

# ═══════════════════════════════════════════════════════════════════════════════
# OPPORTUNITIES FIELDS
# ═══════════════════════════════════════════════════════════════════════════════

FIELD_OPP_NAME = "Opportunity Name"
FIELD_OPP_STAGE = "Stage"
FIELD_OPP_DEAL_VALUE = "Deal Value"
FIELD_OPP_ARR = "Annual Recurring Revenue"
FIELD_OPP_PROBABILITY = "Probability"
FIELD_OPP_EXPECTED_CLOSE = "Expected Close Date"
FIELD_OPP_ACTUAL_CLOSE = "Actual Close Date"
FIELD_OPP_DEAL_HEALTH = "Deal Health"
FIELD_OPP_RISK_LEVEL = "Risk Level"
FIELD_OPP_BLOCKERS = "Blockers"
FIELD_OPP_NEXT_ACTION = "Next Action"
FIELD_OPP_NOTES = "Notes"
FIELD_OPP_CONTACT = "Primary Contact"
FIELD_OPP_COMPANY = "Company"
FIELD_OPP_OWNER = "Opportunity Owner"
FIELD_OPP_TEAM = "Team"
FIELD_OPP_CURRENCY = "Currency"
FIELD_OPP_CONTRACT_TERM = "Contract Term"
FIELD_OPP_RECORD_SOURCE = "Record Source"
FIELD_OPP_ID = "Opportunity ID"

# Opportunity Stage values (status type — same as Tasks DB)
OPP_STAGE_DISCOVERY = "Discovery"
OPP_STAGE_PROPOSAL = "Proposal"
OPP_STAGE_NEGOTIATION = "Negotiation"
OPP_STAGE_CLOSED_WON = "Closed Won"
OPP_STAGE_CLOSED_LOST = "Closed Lost"

# Opportunity Deal Health values
OPP_HEALTH_GREEN = "\U0001f7e2 Green"
OPP_HEALTH_YELLOW = "\U0001f7e1 Yellow"
OPP_HEALTH_RED = "\U0001f534 Red"

# Stage advancement rules: Meeting Type → next Opportunity Stage
STAGE_ADVANCE_MAP = {
    MEETING_TYPE_DISCOVERY: OPP_STAGE_DISCOVERY,
    MEETING_TYPE_DEMO: OPP_STAGE_PROPOSAL,
    MEETING_TYPE_PROPOSAL: OPP_STAGE_NEGOTIATION,
}

# Default probability by stage
STAGE_PROBABILITY = {
    OPP_STAGE_DISCOVERY: "25%",
    OPP_STAGE_PROPOSAL: "50%",
    OPP_STAGE_NEGOTIATION: "75%",
    OPP_STAGE_CLOSED_WON: "100%",
    OPP_STAGE_CLOSED_LOST: "10%",
}

# Stale deal threshold (days without update)
STALE_DEAL_DAYS = 14

# ═══════════════════════════════════════════════════════════════════════════════
# DATA GOVERNANCE — Ingestion Gate Rules (v6.0)
# ═══════════════════════════════════════════════════════════════════════════════

# Company Entry Gate: must pass at least MIN_COMPANY_GATE_SCORE of these checks
COMPANY_GATE_MIN_SCORE = 2  # Must satisfy at least 2 of the 5 criteria

# ICP criteria — target industries and countries
ICP_INDUSTRIES = {
    "insurance", "financial services", "banking", "fintech",
    "investment management", "accounting", "real estate",
    "oil & energy", "construction", "government administration",
    "information technology", "computer software", "telecommunications",
    "health care", "hospital & health care", "medical devices",
    "automotive", "logistics & supply chain", "defense & space",
}

ICP_COUNTRIES = {
    "Saudi Arabia", "United Arab Emirates", "Bahrain", "Kuwait",
    "Oman", "Qatar", "Jordan", "Egypt", "Lebanon",
}

ICP_MIN_EMPLOYEES = 50  # Minimum company size for ICP match

# Senior contact seniorities that count toward gate
SENIOR_SENIORITIES = {"C-Suite", "VP", "Director", "Owner", "Founder", "Partner"}

# Senior title keywords (case-insensitive)
SENIOR_TITLE_KEYWORDS = {
    "ceo", "cfo", "coo", "cto", "cio", "ciso", "cmo", "cro",
    "chief", "president", "vice president", "vp", "director",
    "head of", "general manager", "managing director", "partner",
    "svp", "evp", "avp",
}

# Contact Role Classification
ROLE_DECISION_MAKER_KEYWORDS = {
    "ceo", "cfo", "coo", "cto", "cio", "ciso", "chief", "president",
    "owner", "founder", "managing director", "general manager", "partner",
}
ROLE_INFLUENCER_KEYWORDS = {
    "director", "head of", "vp", "vice president", "svp", "evp",
    "senior manager", "principal", "lead",
}

# Engagement signals that count toward gate (legacy narrow set — single opens only)
ENGAGEMENT_SIGNALS = {"email_open", "replied", "meeting_booked", "demoed"}

# ─── Real Intent Signal (2026-04-11) ────────────────────────────────────────
# Broader definition used by ingestion_gate, data_governor, and daily_sync's
# compute_company_stage. A single email open is noise; we only count intent
# when there is a strong or repeated commercial signal.
#
# Business logic:
#   • Replied = unambiguous intent
#   • Meeting booked = unambiguous intent
#   • Email Open Count >= 2 = not a one-off open; account is paying attention
#   • Internal forwarding / multiple unique openers = strong buying signal
#     (multi-stakeholder engagement inside the target company)
#
# Apollo limitation: Apollo's contact API does NOT expose a reliable
# "forwarded" flag or unique-opener count at the contact level. We therefore
# treat `email_open_count >= EMAIL_OPEN_COUNT_INTENT_THRESHOLD` as the
# primary proxy for repeated engagement and only set internal_forward_detected
# when a consumer explicitly provides it (analytics_tracker / manual).

EMAIL_OPEN_COUNT_INTENT_THRESHOLD = 2       # opens/contact before it counts as real intent
UNIQUE_OPENERS_INTENT_THRESHOLD = 2          # distinct openers at an account
REPEATED_ENGAGEMENT_DAYS_WINDOW = 30         # window used by analytics_tracker if needed

# Optional Notion fields. NOT required to exist — consumers must use getattr-
# style access. Adding them to the Companies / Contacts DB is recommended but
# not mandatory for the logic to work (the helpers degrade gracefully).
FIELD_INTERNAL_FORWARD_DETECTED = "Internal Forward Detected"      # checkbox (optional)
FIELD_REPEATED_ENGAGEMENT_DETECTED = "Repeated Engagement Detected"  # checkbox (optional)
FIELD_HAS_INTENT_SIGNAL = "Has Intent Signal"                       # checkbox (optional)

# Reason codes for logging / audit trail
INTENT_REASON_REPLIED = "replied"
INTENT_REASON_MEETING = "meeting_booked"
INTENT_REASON_REPEATED_OPENS = "repeated_opens"
INTENT_REASON_INTERNAL_FORWARD = "internal_forward"
INTENT_REASON_REPEATED_ENGAGEMENT = "repeated_engagement"


def _coerce_bool(value) -> bool:
    """Best-effort bool coercion. Treats None / empty as False."""
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value.strip().lower() in {"true", "t", "yes", "y", "1", "checked"}
    return bool(value)


def _coerce_int(value) -> int:
    """Best-effort int coercion. Returns 0 for None / bad data."""
    if value is None:
        return 0
    try:
        return int(value)
    except (TypeError, ValueError):
        try:
            return int(float(value))
        except (TypeError, ValueError):
            return 0


def has_real_intent(record: dict) -> tuple:
    """Determine whether a contact OR a company exhibits real commercial intent.

    Works on two shapes:
      • Apollo contact dicts (raw snake_case keys: replied, meeting_booked,
        email_open_count, emails_opened, num_emails_opened, internal_forward_detected,
        repeated_engagement_detected, unique_openers_count, forward_count)
      • Notion page property dicts — callers should flatten to primitives first.

    Returns:
        (is_intent: bool, reasons: list[str]) — reasons is a list of
        INTENT_REASON_* strings describing why intent was detected.
        Empty list when is_intent is False.
    """
    if not record:
        return False, []

    reasons: list = []

    replied = _coerce_bool(
        record.get("replied")
        or record.get("Replied")
    )
    if replied:
        reasons.append(INTENT_REASON_REPLIED)

    meeting_booked = _coerce_bool(
        record.get("meeting_booked")
        or record.get("Meeting Booked")
    )
    if meeting_booked:
        reasons.append(INTENT_REASON_MEETING)

    # Email open count — check several possible keys because Apollo, analytics
    # tracker, and Notion flatteners all name it differently.
    open_count = max(
        _coerce_int(record.get("email_open_count")),
        _coerce_int(record.get("Email Open Count")),
        _coerce_int(record.get("num_emails_opened")),
        _coerce_int(record.get("emails_opened")),
        _coerce_int(record.get("opens")),
    )
    if open_count >= EMAIL_OPEN_COUNT_INTENT_THRESHOLD:
        reasons.append(f"{INTENT_REASON_REPEATED_OPENS}(count={open_count})")

    # Explicit internal-forward flag (rare — only if upstream set it)
    internal_forward = _coerce_bool(
        record.get("internal_forward_detected")
        or record.get(FIELD_INTERNAL_FORWARD_DETECTED)
    )
    # Implicit detection: multiple unique openers at the account
    unique_openers = _coerce_int(
        record.get("unique_openers_count")
        or record.get("unique_openers")
    )
    forward_count = _coerce_int(
        record.get("forward_count")
        or record.get("forwards")
    )
    if internal_forward or forward_count > 0 or unique_openers >= UNIQUE_OPENERS_INTENT_THRESHOLD:
        reasons.append(INTENT_REASON_INTERNAL_FORWARD)

    # Explicit repeated-engagement flag (set by analytics_tracker when a
    # contact has multiple distinct engagement dates inside the window)
    repeated_engagement = _coerce_bool(
        record.get("repeated_engagement_detected")
        or record.get(FIELD_REPEATED_ENGAGEMENT_DETECTED)
    )
    if repeated_engagement:
        reasons.append(INTENT_REASON_REPEATED_ENGAGEMENT)

    return (len(reasons) > 0), reasons


def company_has_real_intent(contacts: list) -> tuple:
    """Aggregate has_real_intent over a list of contacts at a single company.

    Returns:
        (is_intent: bool, reasons: list[str])
    """
    all_reasons: list = []
    for c in contacts or []:
        hit, reasons = has_real_intent(c)
        if hit:
            all_reasons.extend(reasons)
    # De-duplicate while preserving order
    seen = set()
    unique = [r for r in all_reasons if not (r in seen or seen.add(r))]
    return (len(unique) > 0), unique

# Trigger events that count toward gate
TRIGGER_HEADCOUNT_GROWTH_THRESHOLD = 0.10  # 10% growth = trigger
TRIGGER_FUNDING_RECENCY_DAYS = 365  # Funding within last year = trigger

# Contact entry requirements
CONTACT_REQUIRED_FIELDS = {"email", "owner_id"}  # Must have both

# Archive reasons
ARCHIVE_REASON_NO_OWNER = "No Owner"
ARCHIVE_REASON_NO_EMAIL = "No Email"
ARCHIVE_REASON_BOUNCED = "Bounced"
ARCHIVE_REASON_DNC = "DNC"
ARCHIVE_REASON_NO_OUTREACH = "No Outreach"
ARCHIVE_REASON_GATE_FAIL = "Gate Fail"
ARCHIVE_REASON_NO_COMPANY = "No Company"
ARCHIVE_REASON_MANUAL = "Manual"

# Governance enforcement modes
GOVERNANCE_MODE_STRICT = "strict"    # Reject all non-qualifying
GOVERNANCE_MODE_REVIEW = "review"    # Flag for review but allow
GOVERNANCE_MODE_AUDIT = "audit"      # Log only, don't block

# Anti-noise thresholds
MIN_DATA_COMPLETENESS = 0.4  # Company must have >= 40% of key fields populated
COMPANY_KEY_FIELDS = [
    "domain", "industry", "num_employees", "country",
    "website_url", "phone",
]

# Data protection — soft delete cooldown
SOFT_DELETE_DAYS = 30  # Days before soft-deleted records can be hard-deleted

# ═══════════════════════════════════════════════════════════════════════════════
# ICP INDUSTRY FIT SCORING (v1.5)
# Scores reflect MUHIDE's B2B trade governance & FinTech value proposition.
# Applied as 15% weight in Lead Score formula.
# ═══════════════════════════════════════════════════════════════════════════════

FIELD_SORT_SCORE = "Sort Score"       # number — (Lead Score * 100) + Recency Bonus (0-100)
FIELD_MUHIDE_FIT_SCORE = "MUHIDE Fit Score"  # number 1-100 — AI-computed by muhide_strategic_analysis.py
                                              # Used as industry_fit override in lead_score.py when available

# Industry string → Fit Score (0-100). Keys are lowercase for case-insensitive match.
# Core ICP: Financial services, legal, government infrastructure in GCC/MENA.
ICP_INDUSTRY_SCORES = {
    # Tier 1: Core ICP — Maximum fit (MUHIDE's primary market)
    "financial services": 100,
    "banking": 100,
    "fintech": 100,
    "investment banking": 100,
    "insurance": 95,
    "investment management": 90,
    "accounting": 85,
    "venture capital & private equity": 85,
    "capital markets": 90,

    # Tier 2: Strong secondary — High fit
    "government administration": 80,
    "legal services": 80,
    "law practice": 80,
    "oil & energy": 75,
    "defense & space": 75,
    "real estate": 70,
    "construction": 65,
    "import and export": 70,
    "wholesale": 65,
    "management consulting": 70,

    # Tier 3: Adjacent — Moderate fit
    "information technology and services": 60,
    "information technology": 60,
    "computer software": 55,
    "telecommunications": 55,
    "logistics & supply chain": 55,
    "transportation/trucking/railroad": 50,
    "aviation & aerospace": 55,
    "health care": 50,
    "hospital & health care": 50,
    "medical devices": 45,
    "pharmaceuticals": 45,
    "automotive": 45,
    "utilities": 50,
    "mining & metals": 50,
    "chemicals": 45,

    # Tier 4: Weak fit — Low ICP alignment
    "retail": 20,
    "consumer goods": 15,
    "food & beverages": 15,
    "entertainment": 15,
    "media production": 15,
    "broadcast media": 15,
    "education management": 20,
    "higher education": 20,
    "primary/secondary education": 10,
    "nonprofit organization management": 20,
    "restaurants": 5,
    "arts and crafts": 5,
    "apparel & fashion": 10,
    "sports": 10,
    "music": 5,
    "gambling & casinos": 10,
}

# Default score for industries not in the map
ICP_INDUSTRY_DEFAULT_SCORE = 30

# ═══════════════════════════════════════════════════════════════════════════════
# COMPANY PRIORITY SCORE (CPS) — Decision Layer v7.0 (2026-04-14)
# Single unified company-level score that drives all sales execution.
# Computed by scripts/scoring/company_priority_scorer.py
# ═══════════════════════════════════════════════════════════════════════════════

# Notion field names (Companies DB)
FIELD_COMPANY_PRIORITY_SCORE = "Company Priority Score"  # number 0-100
FIELD_PRIORITY_TIER = "Priority Tier"                    # select: P1/P2/P3
FIELD_BEST_CONTACT = "Best Contact"                      # rich_text (contact name + page ID)
FIELD_NEXT_ACTION = "Next Action"                        # select: Call/Email/Sequence/Wait/Review
FIELD_PRIORITY_REASON = "Priority Reason"                # rich_text (auto-generated top 3 reasons)
FIELD_ACTION_OWNER = "Action Owner"                      # select: Ibrahim/Ragheed/Soha
FIELD_ACTION_SLA = "Action SLA"                          # select: 24h/48h/7d/None
FIELD_AI_RISK_FLAG = "AI Risk Flag"                      # checkbox

# CPS Component Weights
CPS_WEIGHT_BEST_CONTACT = 0.25    # Best Contact Score
CPS_WEIGHT_ENGAGEMENT = 0.25      # Engagement Index
CPS_WEIGHT_FIRMOGRAPHIC = 0.20    # Industry Fit + Size
CPS_WEIGHT_AI_SIGNAL = 0.15       # AI Priority + AI Qualification + MUHIDE Fit
CPS_WEIGHT_MOMENTUM = 0.15        # Stage movement + Freshness

# Priority Tier thresholds
CPS_TIER_P1 = 75        # P1: Act Now — Urgent Call or Strategic Email
CPS_TIER_P2 = 50        # P2: Pursue — Follow-up Email or Sequence
# P3: < 50 — Monitor only, auto-sequence if eligible

# Priority Tier labels
PRIORITY_P1 = "P1"
PRIORITY_P2 = "P2"
PRIORITY_P3 = "P3"

# Next Action values
ACTION_CALL = "Call"
ACTION_EMAIL = "Email"
ACTION_SEQUENCE = "Sequence"
ACTION_WAIT = "Wait"
ACTION_REVIEW = "Review"

# SLA values
SLA_24H = "24h"
SLA_48H = "48h"
SLA_7D = "7d"
SLA_NONE = "None"

# Firmographic sub-weights within the FIT component
CPS_FIT_INDUSTRY_WEIGHT = 0.60   # Industry Fit score
CPS_FIT_SIZE_WEIGHT = 0.40       # Employee size score

# AI Signal sub-weights
CPS_AI_PRIORITY_WEIGHT = 0.40    # AI Priority (P1=100, P2=70, P3=40)
CPS_AI_QUAL_WEIGHT = 0.30        # AI Qualification (Qualified=100, Possible=60, Disqualified=0)
CPS_AI_MUHIDE_WEIGHT = 0.30      # MUHIDE Fit Score (direct 0-100)

# AI Priority → numeric score mapping
AI_PRIORITY_SCORE = {"P1": 100, "P2": 70, "P3": 40}

# AI Qualification → numeric score mapping
AI_QUAL_SCORE = {"Qualified": 100, "Possible Fit": 60, "Disqualified": 0}

# Momentum scoring constants
MOMENTUM_STAGE_ADVANCED_7D = 40     # Stage moved up in last 7 days
MOMENTUM_ACTIVITY_3D = 30           # Activity within 3 days
MOMENTUM_ACTIVITY_7D = 20           # Activity within 7 days
MOMENTUM_ACTIVITY_14D = 10          # Activity within 14 days
MOMENTUM_MULTI_ENGAGED = 20         # Multiple contacts engaged
MOMENTUM_NEW_CONTACT_7D = 10        # New contact added in last 7 days

# CPS caps and guards
CPS_AI_DISQUALIFIED_CAP = 74        # If AI Qual = Disqualified, cap CPS at P2 max
CPS_MIN_COMPONENTS = 2              # Min populated components to receive a CPS score

# ─── Contact Stage Auto-Inference (T8) ──────────────────────────────────────
# Maps Outreach Status → Contact Stage when Apollo returns empty Stage.
# Applied ONLY when Stage is empty — never overwrites manual or Apollo-set values.
# Priority: highest signal wins (meeting booked > replied > opened > sent).
STAGE_INFER_FROM_OUTREACH = {
    "meeting booked": "Engaged",
    "replied": "Prospect",
    "opened": "Lead",
    "in sequence": "Lead",
    "sent": "Lead",
    "bounced": "Archived",
    "do not contact": "Archived",
    "bad data": "Archived",
}

# Fallback when email_sent=True but Outreach Status is unknown/empty
STAGE_INFER_DEFAULT = "Lead"

# ═══════════════════════════════════════════════════════════════════════════════
# NOTION DATABASE IDS (loaded from env at runtime, these are just references)
# ═══════════════════════════�