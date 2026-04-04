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

FIELD_AI_DECISION = "AI Decision"
FIELD_AI_QUALIFICATION_STATUS = "AI Qualification Status"
FIELD_AI_QUALIFICATION_DETAIL = "AI Qualification Detail"

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

# Engagement signals that count toward gate
ENGAGEMENT_SIGNALS = {"email_open", "replied", "meeting_booked", "demoed"}

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
# NOTION DATABASE IDS (loaded from env at runtime, these are just references)
# ═══════════════════════════════════════════════════════════════════════════════
# NOTION_DATABASE_ID_CONTACTS = env
# NOTION_DATABASE_ID_COMPANIES = env
# NOTION_DATABASE_ID_TASKS = env
# NOTION_DATABASE_ID_MEETINGS = env
# NOTION_DATABASE_ID_OPPORTUNITIES = env
