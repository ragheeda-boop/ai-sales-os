#!/usr/bin/env python3
"""
Engineering Offices Follow-up System — Constants
مكاتب هندسية - وزارة الاسكان
"""

# ═══════════════════════════════════════════════
# NOTION DATABASE
# ═══════════════════════════════════════════════
NOTION_DB_ID = "b85c24be6aa941a395dc33fd1c5f566a"
NOTION_DATA_SOURCE_ID = "5f35ec3f-8eb0-46d9-86a7-850bd2b1645b"
NOTION_DB_URL = "https://www.notion.so/b85c24be6aa941a395dc33fd1c5f566a"

# ═══════════════════════════════════════════════
# APOLLO SEQUENCE & LIST
# ═══════════════════════════════════════════════
APOLLO_SEQUENCE_ID = "69541c78db24f5001d40dfd7"
APOLLO_SEQUENCE_NAME = "مكاتب هندسية"
APOLLO_LIST_NAME = "مكاتب هندسية خار apollo"

# ═══════════════════════════════════════════════
# SOURCE FILES
# ═══════════════════════════════════════════════
SHEET1_PATH = r"C:\Users\PC\Downloads\مكاتب هندسية - Sheet1.csv"
SHEET2_PATH = r"C:\Users\PC\Downloads\مكاتب هندسية 2 - Sheet1.csv"

# ═══════════════════════════════════════════════
# NOTION FIELD NAMES (exact match with DB)
# ═══════════════════════════════════════════════
F_NAME            = "Company Name"
F_NORM            = "Normalized Name"
F_REGION          = "Region"
F_CITY            = "City"
F_CR              = "CR Number"
F_EMAIL           = "Main Email"
F_MOBILE          = "Mobile"
F_WA              = "WhatsApp"
F_SOURCE          = "Source Sheet"
F_COMPLETENESS    = "Data Completeness Score"
F_STATUS          = "Company Status"
F_TIER            = "Account Tier"
F_PRIORITY        = "Priority"
F_OWNER           = "Owner"
F_NOTES           = "Notes"
F_MANUAL_NOTE     = "Manual Note"

# Apollo fields
F_APOLLO_MATCHED  = "Apollo Matched"
F_MATCH_CONF      = "Match Confidence"
F_APOLLO_ACC_ID   = "Apollo Account ID"
F_APOLLO_CON_ID   = "Apollo Contact ID"
F_IN_LIST         = "In Apollo List"
F_IN_SEQ          = "In Sequence"
F_SEQ_STATUS      = "Sequence Status"
F_SEQ_STEP        = "Sequence Step"

# Engagement fields
F_EMAIL_SENT      = "Email Sent"
F_EMAIL_OPENED    = "Email Opened"
F_EMAIL_REPLIED   = "Email Replied"
F_EMAIL_BOUNCED   = "Email Bounced"
F_LAST_SENT_AT    = "Last Email Sent At"
F_LAST_OPENED_AT  = "Last Opened At"
F_LAST_REPLIED_AT = "Last Replied At"
F_LAST_ACT_DATE   = "Last Activity Date"
F_LAST_ACT_TYPE   = "Last Activity Type"
F_ACT_COUNT       = "Activity Count"
F_POS_SIGNAL      = "Positive Signal"
F_MTG_BOOKED      = "Meeting Booked"
F_MTG_DONE        = "Meeting Completed"
F_MTG_DATE        = "Meeting Date"
F_NEXT_ACTION     = "Next Action"
F_NEXT_DUE        = "Next Action Due"
F_FOLLOWUP_STAGE  = "Follow-up Stage"
F_STALE_FLAG      = "Stale Flag"
F_DAYS_SINCE      = "Days Since Contact"

# Quality fields
F_MISS_EMAIL      = "Missing Email"
F_MISS_MOBILE     = "Missing Mobile"
F_DUP_SUSPECTED   = "Duplicate Suspected"
F_MANUAL_REVIEW   = "Needs Manual Review"
F_READY           = "Ready for Outreach"

# ═══════════════════════════════════════════════
# REGION MAPPING (from raw sheet data)
# ═══════════════════════════════════════════════
REGION_MAP = {
    "الرياض": "الرياض",
    "جدة": "جدة",
    "مكة المكرمة": "مكة المكرمة",
    "الشرقية": "الشرقية",
    "الخبر": "الشرقية",
    "الدمام": "الشرقية",
    "الأحساء": "الشرقية",
    "الجبيل": "الشرقية",
    "المبرز": "الشرقية",
    "القطيف": "الشرقية",
    "المدينة المنورة": "المدينة المنورة",
    "حائل": "حائل",
    "القصيم": "القصيم",
    "بريده": "القصيم",
    "البدائع": "القصيم",
    "عسير": "عسير",
    "أبها": "عسير",
    "محايل": "عسير",
    "جازان": "جازان",
    "تبوك": "تبوك",
    "نجران": "نجران",
    "الباحة": "الباحة",
    "الجوف": "الجوف",
    "الحدود الشمالية": "الحدود الشمالية",
    "عرعر": "الحدود الشمالية",
    "رفحاء": "الحدود الشمالية",
    "الطائف": "مكة المكرمة",
    "رابغ": "مكة المكرمة",
    "الخرج": "الرياض",
    "الخارجة": "الرياض",
    "التويعية": "الرياض",
    "القويعية": "الرياض",
    "الأطاولة": "الباحة",
}

# ═══════════════════════════════════════════════
# FOLLOWUP RULES — stale threshold
# ═══════════════════════════════════════════════
STALE_DAYS = 14           # days since last activity = stale
OPENED_FOLLOWUP_DAYS = 3  # opened but no reply after 3 days = needs follow-up
