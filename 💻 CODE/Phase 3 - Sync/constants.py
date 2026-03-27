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

# ═══════════════════════════════════════════════════════════════════════════════
# NOTION DATABASE IDS (loaded from env at runtime, these are just references)
# ═══════════════════════════════════════════════════════════════════════════════
# NOTION_DATABASE_ID_CONTACTS = env
# NOTION_DATABASE_ID_COMPANIES = env
# NOTION_DATABASE_ID_TASKS = env  (new — add to .env)
