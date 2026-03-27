# PHASE 1 — AUDIT, SCHEMA DESIGN & FIELD MAPPING

## EXECUTIVE SUMMARY

**Merged Dataset:**
- **Total Contact Records:** 5,901
- **Total Columns:** 74 fields
- **Total Companies (Unique Apollo Account Id):** 3,606
- **Data Quality:** EXCELLENT (>99.8% completeness for critical fields)

**Status:** ✅ READY FOR BUILD

---

## 1. MERGED DATASET AUDIT FINDINGS

### 1.1 Dataset Composition

| Metric | Value |
|--------|-------|
| Part 1 rows (header + data) | 69,499 |
| Part 2 rows (header + data) | 138,780 |
| **Total merged rows** | **208,278** |
| **Data rows (excluding header)** | **208,277** |
| **After dedup by Apollo Contact Id** | **5,901** |
| **Unique companies** | **3,606** |

### 1.2 Primary Key Integrity

| Check | Result | Status |
|-------|--------|--------|
| Missing Apollo Contact Id | 0 | ✅ PERFECT |
| Missing Apollo Account Id | 3 | ⚠️ MINOR |
| Duplicate Apollo Contact Id | 0 | ✅ PERFECT |
| Duplicate Contact→Account mappings | 0 | ✅ PERFECT |

**Action:** The 3 records with missing Apollo Account Id will be logged to Exception Log.

### 1.3 Data Quality by Domain

#### Email/Contact Profile
- **Valid emails:** 5,647 / 5,901 (95.7%)
- **Unique emails:** 5,583
- **Email Status = "Verified":** 5,602 (94.9%)
- **First Names:** 5,901 / 5,901 (100%)
- **Last Names:** 5,892 / 5,901 (99.8%)
- **Titles:** 5,892 / 5,901 (99.8%)
- **Seniority:** 5,892 / 5,901 (99.8%)

#### Company Profile
- **Company Names:** 5,898 / 5,901 (99.9%)
- **Websites:** 5,813 / 5,901 (98.5%)
- **Industries:** 5,895 / 5,901 (99.9%)
- **# Employees:** 5,898 / 5,901 (99.9%)
- **Company Addresses:** 5,744 / 5,901 (97.3%)
- **Countries:** 5,742-5,883 / 5,901 (97-99%)

#### Financial & Funding Data
- **Annual Revenue:** 1,366 / 5,901 (23.1%) — *Sparse but expected*
- **Total Funding:** 399 / 5,901 (6.8%)
- **Latest Funding:** 514 / 5,901 (8.7%)

#### Outreach Signals
- **Email Sent:** 4,694 / 5,901 (79.5%)
- **Email Opened:** 1,091 / 5,901 (18.5%)
- **Email Bounced:** 0 False, all others blank/False
- **Replied:** 57 True, 5,844 False

#### Research & Intelligence Fields
- **Conduct targeted research 6305:** 4,145 / 5,901 (70.2%)
- **Qualify Contact:** 5,608 / 5,901 (95.0%)
- **Generate natural call scripts 5398:** 4,145 / 5,901 (70.2%)
- **Prime research focus and context 1558:** 4,174 / 5,901 (70.7%)
- **Contact Analysis 7680:** 5,891 / 5,901 (99.8%)

#### Intent Signals ⚠️ GAP
- **Primary Intent Topic:** 0 / 5,901 (0.0%)
- **Primary Intent Score:** 0 / 5,901 (0.0%)
- Secondary Intent fields: Also empty

**Note:** Intent fields exist but are unpopulated in CSV export. These will be enriched via direct Apollo API in Phase 2.

---

## 2. VALIDATION RISK REPORT

### 2.1 Risks Identified

| Risk | Severity | Count | Mitigation |
|------|----------|-------|-----------|
| Missing Apollo Account Id | LOW | 3 | Log to Exception Log; do not create orphan contacts |
| Missing Email | LOW | 254 | Create contact, flag for manual review |
| Missing Website | LOW | 88 | Company still valid; use Company Name + Address for validation |
| Missing Annual Revenue | MEDIUM | 4,535 | Expected; use "Unknown" in Revenue Range |
| Missing Secondary/Tertiary Email | LOW | 4,836 | Expected; primary email sufficient |
| Intent data empty in CSV | MEDIUM | 5,901 | Expected; will enrich from Apollo API in Phase 2 |

### 2.2 Data Quality Assessment

**Overall Grade: A+**
- ✅ No primary key duplicates
- ✅ No primary key nulls (except 3 minor Account Id gaps)
- ✅ >99% completeness on core contact/company fields
- ✅ Excellent email coverage (95.7%)
- ✅ Excellent company data coverage (97-99%)
- ⚠️ Revenue data sparse but expected for B2B datasets
- ⚠️ Intent signals absent in CSV but retrievable from API

---

## 3. FIELD INVENTORY & MAPPING TABLE

### Complete Field List (74 fields)

| # | Apollo Field | Notion Property | Type | Coverage | Mapping Notes |
|---|---|---|---|---|---|
| **CONTACT CORE** | | | | | |
| 1 | First Name | First Name | Text | 100% | Direct |
| 2 | Last Name | Last Name | Text | 99.8% | Direct |
| 3 | Title | Title | Text | 99.8% | Direct |
| 4 | Seniority | Seniority | Select | 99.8% | Keep as-is |
| 5 | Departments | Departments | Text | 75.5% | Comma-separated |
| 6 | Sub Departments | Sub Departments | Text | 75.5% | Comma-separated |
| 7 | Apollo Contact Id | Apollo Contact Id | Text | 100% | **PRIMARY KEY** |
| | | Full Name | Formula | 100% | =First Name + " " + Last Name |
| **CONTACT EMAIL** | | | | | |
| 8 | Email | Email | Email | 95.7% | Primary email address |
| 9 | Email Status | Email Status | Select | 100% | Values: Verified, New Data Available, Email No Longer Verified, Unavailable, Extrapolated |
| 10 | Primary Email Source | Primary Email Source | Text | 96.3% | Direct |
| 11 | Primary Email Verification Source | Primary Email Verification Source | Text | 96.3% | Direct |
| 12 | Email Confidence | Email Confidence | Number | 0.2% | Sparse; skip on build |
| 13 | Primary Email Catch-all Status | Primary Email Catch-all Status | Text | 49.1% | Direct |
| 14 | Primary Email Last Verified At | Primary Email Last Verified At | Date | 94.9% | Parse date |
| 15 | Secondary Email | Secondary Email | Email | 18.0% | Optional secondary |
| 16 | Secondary Email Source | Secondary Email Source | Text | 18.0% | Direct |
| 17 | Secondary Email Status | Secondary Email Status | Text | 18.0% | Direct |
| 18 | Secondary Email Verification Source | Secondary Email Verification Source | Text | 18.0% | Direct |
| 19 | Tertiary Email | Tertiary Email | Email | 0.0% | **NOT IN DATA** |
| **CONTACT PHONE** | | | | | |
| 20 | Work Direct Phone | Work Direct Phone | Phone | 1.3% | Sparse |
| 21 | Home Phone | Home Phone | Phone | 0.1% | Sparse |
| 22 | Mobile Phone | Mobile Phone | Phone | 45.4% | Direct |
| 23 | Corporate Phone | Corporate Phone | Phone | 55.5% | Direct |
| 24 | Other Phone | Other Phone | Phone | 20.6% | Direct |
| **CONTACT LOCATION** | | | | | |
| 25 | City | City | Text | 64.9% | Person's city |
| 26 | State | State | Text | 68.5% | Person's state |
| 27 | Country | Country | Text | 99.7% | Person's country |
| **CONTACT SOCIAL** | | | | | |
| 28 | Person Linkedin Url | Person Linkedin Url | URL | 99.8% | Direct |
| **CONTACT ENGAGEMENT** | | | | | |
| 29 | Stage | Stage | Select | 100% | Keep value from Apollo |
| 30 | Last Contacted | Last Contacted | Date | 79.6% | Parse date |
| 31 | Email Sent | Email Sent | Checkbox | 79.5% | "True" = checked |
| 32 | Email Open | Email Open | Checkbox | 100% | "True" = checked |
| 33 | Email Bounced | Email Bounced | Checkbox | 100% | "True" = checked |
| 34 | Replied | Replied | Checkbox | 100% | "True" = checked |
| 35 | Demoed | Demoed | Checkbox | 100% | "True" = checked |
| **CONTACT RESEARCH** | | | | | |
| 36 | Conduct targeted research 6305 | Conduct targeted research 6305 | Text | 70.2% | AI research guidance |
| 37 | Qualify Contact | Qualify Contact | Text | 95.0% | Qualification notes |
| 38 | Generate natural call scripts 5398 | Generate natural call scripts 5398 | Text | 70.2% | AI-generated script |
| 39 | Prime research focus and context 1558 | Prime research focus and context 1558 | Text | 70.7% | Research context |
| 40 | Contact Analysis 7680 | Contact Analysis 7680 | Text | 99.8% | AI contact analysis |
| **CONTACT SYSTEM** | | | | | |
| 41 | Contact Owner | Contact Owner (ref) | Text | 100% | Apollo owner |
| 42 | Lists | Lists | Text | 100% | Comma-separated |
| **COMPANY CORE** | | | | | |
| 43 | Company Name | Company Name | Title | 99.9% | Canonical company name |
| 44 | Company Name for Emails | Company Name for Emails | Text | 99.9% | Alternative email name |
| 45 | Apollo Account Id | Apollo Account Id | Text | 99.9% | **PRIMARY KEY** |
| 46 | Website | Website | URL | 98.5% | Direct |
| | | Domain | Formula | 98.5% | Extract from Website |
| 47 | Industry | Industry | Select | 99.9% | Direct |
| 48 | Keywords | Keywords | Text | 94.9% | Comma-separated |
| 49 | Technologies | Technologies | Text | 95.6% | Comma-separated |
| **COMPANY LOCATION** | | | | | |
| 50 | Company Address | Company Address | Text | 97.3% | Full address |
| 51 | Company City | Company City | Text | 94.8% | City |
| 52 | Company State | Company State | Text | 96.0% | State/Province |
| 53 | Company Country | Company Country | Text | 97.3% | Country |
| 54 | Company Phone | Company Phone | Phone | 61.9% | Main phone |
| **COMPANY SOCIAL** | | | | | |
| 55 | Company Linkedin Url | Company Linkedin Url | URL | 99.9% | Direct |
| 56 | Facebook Url | Facebook Url | URL | 36.2% | Sparse |
| 57 | Twitter Url | Twitter Url | URL | 35.5% | Sparse |
| **COMPANY SIZE** | | | | | |
| 58 | # Employees | # Employees | Number | 99.9% | Employee count |
| | | Employee Size | Select | 99.9% | Mapped from # Employees |
| **COMPANY FINANCIAL** | | | | | |
| 59 | Annual Revenue | Annual Revenue | Currency | 23.1% | Annual revenue USD |
| | | Revenue Range | Select | 23.1% | Mapped from Annual Revenue |
| 60 | Total Funding | Total Funding | Currency | 6.8% | Total raised |
| 61 | Latest Funding | Latest Funding | Text | 8.7% | Funding round type |
| 62 | Latest Funding Amount | Latest Funding Amount | Currency | 8.2% | Latest round amount |
| 63 | Last Raised At | Last Raised At | Date | 8.7% | Last funding date |
| 64 | Subsidiary of | Subsidiary of | Text | 2.2% | Parent company |
| 65 | Subsidiary of (Organization ID) | Subsidiary of (Organization ID) | Text | 2.2% | Parent org ID |
| **COMPANY RETAIL** | | | | | |
| 66 | Number of Retail Locations | Number of Retail Locations | Number | 0.2% | Sparse; skip |
| **COMPANY SYSTEM** | | | | | |
| 67 | Account Owner | Account Owner (ref) | Text | 77.2% | Apollo owner |
| **INTENT & INTELLIGENCE** | | | | | |
| 68 | Primary Intent Topic | Primary Intent Topic | Select | **0.0%** | ❌ NOT IN CSV; fetch from API in Phase 2 |
| 69 | Primary Intent Score | Primary Intent Score | Number | **0.0%** | ❌ NOT IN CSV; fetch from API in Phase 2 |
| 70 | Secondary Intent Topic | Secondary Intent Topic | Select | **0.0%** | ❌ NOT IN CSV; fetch from API in Phase 2 |
| 71 | Secondary Intent Score | Secondary Intent Score | Number | **0.0%** | ❌ NOT IN CSV; fetch from API in Phase 2 |

---

## 4. DOMAIN EXTRACTION LOGIC

For each company's Website field, extract Domain as follows:

```
1. Remove "https://" or "http://"
2. Remove "www." if present
3. Take substring before first "/" (if any)
4. Convert to lowercase
5. Save as Domain

Examples:
  https://www.google.com        → google.com
  https://www.microsoft.com/en  → microsoft.com
  www.amazon.com                → amazon.com
  linkedin.com/company/foo      → linkedin.com
  (blank)                        → (blank)
```

**Use Domain for:**
- Validation during import
- Risk flagging (e.g., free email domains)
- Deduplication checks

**Do NOT use Domain as:**
- Primary key (use Apollo Account Id instead)
- Company identifier in relations

---

## 5. EMPLOYEE SIZE & REVENUE RANGE MAPPINGS

### Employee Size Mapping (from # Employees)

| Range | Values |
|-------|--------|
| 1–10 | 1 to 10 |
| 11–50 | 11 to 50 |
| 51–200 | 51 to 200 |
| 201–500 | 201 to 500 |
| 501–1,000 | 501 to 1000 |
| 1,001–5,000 | 1001 to 5000 |
| 5,001+ | 5001+ |

### Revenue Range Mapping (from Annual Revenue in USD)

| Range | Values |
|-------|--------|
| Unknown | blank or 0 |
| <$1M | 0 to 999,999 |
| $1M–$10M | 1,000,000 to 9,999,999 |
| $10M–$50M | 10,000,000 to 49,999,999 |
| $50M–$100M | 50,000,000 to 99,999,999 |
| $100M–$500M | 100,000,000 to 499,999,999 |
| $500M+ | 500,000,000+ |

---

## 6. PROPOSED NOTION DATABASE SCHEMA

### Database 1: Companies — Canonical

**Purpose:** Single source of truth for all companies.
**Primary Key:** Apollo Account Id (unique, never null for valid records)

**Properties:**

```
Title Property:
  - Company Name (from Company Name)

Text Properties:
  - Apollo Account Id (PRIMARY KEY, indexed)
  - Domain (extracted from Website)
  - Company Name for Emails
  - Industry
  - Keywords
  - Technologies
  - Company Address
  - Company City
  - Company State
  - Company Country
  - Company Phone
  - Subsidiary of
  - Subsidiary of (Organization ID)
  - Contact Owner

URL Properties:
  - Website
  - Company Linkedin Url
  - Facebook Url
  - Twitter Url

Number Properties:
  - # Employees
  - Annual Revenue
  - Total Funding
  - Latest Funding Amount

Currency Properties (if supported, else Number):
  - Annual Revenue
  - Total Funding
  - Latest Funding Amount

Select Properties:
  - Employee Size (1–10, 11–50, 51–200, 201–500, 501–1000, 1001–5000, 5001+)
  - Revenue Range (Unknown, <$1M, $1M–$10M, $10M–$50M, $50M–$100M, $100M–$500M, $500M+)
  - Industry (values from data)

Date Properties:
  - Last Raised At

Rich Text / Long Text:
  - Latest Funding (funding round type)

Relations:
  - Contacts (← Contacts database)
  - Intelligence Records (← Sales Intelligence database)
  - Activities (← Outreach/Activities database)

Checkbox Properties:
  - Apollo Source (auto-check on import)
  - Risk Flag (check if no website, domain issues, etc.)
```

---

### Database 2: Contacts — Canonical

**Purpose:** Single source of truth for all contacts.
**Primary Key:** Apollo Contact Id (unique, never null)
**Constraint:** Every contact MUST link to a valid company in Companies database.

**Properties:**

```
Title Property:
  - Full Name (formula: First Name + " " + Last Name, or use full_name if provided)

Text Properties:
  - Apollo Contact Id (PRIMARY KEY, indexed)
  - Apollo Account Id (for reference; links to Company)
  - First Name
  - Last Name
  - Title
  - Seniority
  - Departments
  - Sub Departments
  - Work Direct Phone
  - Home Phone
  - Mobile Phone
  - Corporate Phone
  - Other Phone
  - City (person's location)
  - State (person's location)
  - Country (person's location)
  - Primary Email Source
  - Primary Email Verification Source
  - Primary Email Catch-all Status
  - Secondary Email Source
  - Secondary Email Status
  - Secondary Email Verification Source
  - Contact Owner
  - Stage
  - Lists

Email Properties:
  - Email (primary email)
  - Secondary Email
  - Tertiary Email

URL Properties:
  - Person Linkedin Url

Date Properties:
  - Last Contacted
  - Primary Email Last Verified At

Select Properties:
  - Email Status (Verified, Email No Longer Verified, New Data Available, Unavailable, Extrapolated)

Checkbox Properties:
  - Email Sent
  - Email Open
  - Email Bounced
  - Replied
  - Demoed
  - Risk Flag (check if no email, email status issues, etc.)

Rich Text / Long Text Properties:
  - Conduct targeted research 6305
  - Qualify Contact
  - Generate natural call scripts 5398
  - Prime research focus and context 1558
  - Contact Analysis 7680

Relations:
  - Company (→ Companies database, required, many-to-one)
  - Intelligence Records (← Sales Intelligence database)
  - Activities (← Outreach/Activities database)
```

---

### Database 3: Sales Intelligence

**Purpose:** Intent signals, scoring, and AI-generated research guidance.
**Primary Key:** Auto-generated by Notion

**Properties:**

```
Title Property:
  - Record Name

Relations:
  - Company (→ Companies database)
  - Contact (→ Contacts database)

Select Properties:
  - Primary Intent Topic (values TBD from Apollo API Phase 2)
  - Secondary Intent Topic (values TBD from Apollo API Phase 2)
  - Priority Tier (High, Medium, Low)

Number Properties:
  - Primary Intent Score (0-100)
  - Secondary Intent Score (0-100)

Checkbox Properties:
  - Qualify Contact

Rich Text / Long Text Properties:
  - AI Summary
  - Outreach Angle
  - Buying Signal Summary
  - Contact Analysis (from Contact Analysis 7680)

Date Properties:
  - Last AI Refresh
```

---

### Database 4: Outreach / Activities

**Purpose:** Track email campaigns, engagement, and outreach activities.
**Primary Key:** Auto-generated by Notion

**Properties:**

```
Title Property:
  - Activity Name

Relations:
  - Contact (→ Contacts database)
  - Company (→ Companies database)

Checkbox Properties:
  - Email Sent
  - Email Open
  - Email Bounced
  - Replied
  - Demoed

Date Properties:
  - Last Contacted
  - Next Action Date

Select Properties:
  - Current Funnel Stage

Rich Text / Long Text Properties:
  - Next Action

Note: Can also be modeled as calculated rollups/rollbacks from Contact if preferred.
```

---

### Database 5: Apollo Sync Logs

**Purpose:** Audit trail for all data imports and updates.
**Primary Key:** Auto-generated by Notion

**Properties:**

```
Title Property:
  - Sync Name (e.g., "Phase 1 Initial Build", "Apollo Pull #1 - Q1 2024")

Text Properties:
  - Source (e.g., "CSV File Part 1", "Apollo API")
  - Trigger (e.g., "Initial Build", "On-Demand Request", "Scheduled")
  - Sync Type (e.g., "Full Load", "Incremental", "Append", "Update")

Date Properties:
  - Started At
  - Finished At

Number Properties:
  - Total Records Read
  - Companies Created
  - Contacts Created
  - Records Updated
  - Exceptions Count

Rich Text / Long Text Properties:
  - Notes (detailed summary)
```

---

### Database 6: Exception Log (Optional but Preferred)

**Purpose:** Track data issues, orphans, and manual action items.
**Primary Key:** Auto-generated by Notion

**Properties:**

```
Title Property:
  - Exception (e.g., "Missing Apollo Account Id", "Orphan Contact", "Invalid Email")

Text Properties:
  - Record Id (Apollo Contact Id or Apollo Account Id)
  - Record Name (Company Name or Full Name)
  - Exception Type
  - Severity (High, Medium, Low)
  - Source Field

Rich Text / Long Text Properties:
  - Description
  - Remediation Notes

Date Properties:
  - Created At
  - Resolved At

Checkbox Properties:
  - Resolved
  - Requires Manual Action
```

---

## 7. EXTRACTION PLAN

### Phase 1A: Companies Extraction
1. Group all contacts by Apollo Account Id
2. Create one row per unique Apollo Account Id
3. Use first occurrence of each company field
4. Extract Domain from Website
5. Generate Employee Size from # Employees
6. Generate Revenue Range from Annual Revenue
7. Check for blank required fields → send to Exception Log
8. Total expected: 3,606 companies

### Phase 1B: Contacts Extraction
1. For each contact record:
   - Verify Apollo Contact Id exists (required)
   - Verify Apollo Account Id exists (required unless sent to Exception Log)
   - Link to company via Apollo Account Id
   - If no matching company exists in Companies database, send to Exception Log
   - If company exists, create contact and set Company relation
2. Total expected: 5,898 contacts (3 orphaned due to missing Account Id)

### Phase 1C: Build Relations
1. For each contact, set Company relation to matching company
2. For each company, backlink should auto-populate from Contacts relation
3. Validate no orphan contacts exist

### Phase 1D: Sales Intelligence (Minimal Phase 1)
1. For contacts with "Contact Analysis 7680" populated, create stub Intelligence record
2. Link to Contact and Company
3. In Phase 2, enrich with intent data from Apollo API

### Phase 1E: Outreach/Activities (Minimal Phase 1)
1. For each contact with Email Sent = True, create Activity record
2. Populate Email Sent, Email Open, Replied, etc. from contact data
3. Link to Contact and Company

---

## 8. VALIDATION BATCH PLAN

Before full build, run validation batch on **first 100 records**:

**Validation Checklist:**
- [ ] 100 companies created with correct primary keys
- [ ] 100 contacts created with correct primary keys
- [ ] All contacts linked to valid companies (0 orphans)
- [ ] Domain extracted correctly (sample check)
- [ ] Employee Size mapped correctly (sample check)
- [ ] Revenue Range mapped correctly (sample check)
- [ ] Email Status values correct
- [ ] Seniority values preserved
- [ ] All relations bidirectional
- [ ] No duplicate records
- [ ] Exception Log has 0 entries for valid batch

**Pass Criteria:**
- ✅ 100% primary key integrity
- ✅ 100% company link integrity
- ✅ 0 orphan contacts
- ✅ Correct field types
- ✅ Correct value mappings

Once validation batch passes, proceed to full build.

---

## 9. FULL BUILD EXECUTION PLAN

**Step 1:** Create all 6 Notion databases with final schema
**Step 2:** Run validation batch (100 records)
**Step 3:** Upon validation pass, import all 5,901 contacts + 3,606 companies
**Step 4:** Create relations and backlinks
**Step 5:** Create minimal Intelligence records (Phase 2 enrichment)
**Step 6:** Create minimal Activity records
**Step 7:** Log all operations in Apollo Sync Logs
**Step 8:** Log all exceptions in Exception Log

**Expected Outcome:**
- 3,606 companies created
- 5,898 contacts created
- 3 exceptions (missing Apollo Account Id)
- 0 orphan contacts
- All relations validated

---

## 10. PHASE 2 READINESS

**After Phase 1 completion:**

1. **Intent Data:** Fetch Primary Intent Topic + Score from Apollo API
2. **Contact Enrichment:** Pull updated contact fields for specific segments
3. **Account Targeting:** Build filters in Notion for account selection (revenue, employees, industry, etc.)
4. **Direct Apollo Pulls:** Switch to on-demand mode for specific segments

**Phase 2 will use MCP/Apollo connection to:**
- Query accounts by filters
- Query contacts by title/seniority/geography
- Pull saved Apollo lists
- Enrich existing Notion records with latest Apollo data
- Never sync back into old databases

---

## NEXT STEP

**Ready to proceed with:**
1. ✅ Notion database creation (using schema above)
2. ✅ Validation batch (first 100 records)
3. ✅ Full import (all 5,901 records)
4. ✅ Relation setup and validation
5. ✅ Phase 1 completion report

**Awaiting confirmation to begin Notion database build.**
