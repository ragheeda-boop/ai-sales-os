# TECHNICAL REFERENCE — PHASE 1 IMPLEMENTATION

**For:** Implementation Engineers & Developers  
**Purpose:** Complete technical specifications for building the Notion Sales OS  
**Audience:** Anyone implementing Phase 1 database creation and data import

---

## 1. NOTION DATABASE CREATION SPECIFICATIONS

### 1.1 Database 1: Companies

**Display Name:** Companies — Canonical  
**Description:** Single source of truth for all company accounts. Primary key: Apollo Account Id.  
**Icon:** 🏢 (Building)  

#### Properties (Exact Specification)

| # | Property Name | Type | Configuration | Notes |
|---|---|---|---|---|
| 1 | Company Name | Title | Default title property | Page title; required |
| 2 | Apollo Account Id | Text | Indexed, unique constraints | PRIMARY KEY; required |
| 3 | Domain | Text | Not indexed | Extracted from Website |
| 4 | Website | URL | No validation required | Standard URL format |
| 5 | Company Linkedin Url | URL | No validation required | LinkedIn company profile |
| 6 | Facebook Url | URL | No validation required | Optional |
| 7 | Twitter Url | URL | No validation required | Optional |
| 8 | Industry | Select | Create values from data | Multi-select recommended |
| 9 | Keywords | Text | Rich text: OFF | Comma-separated values |
| 10 | Technologies | Text | Rich text: OFF | Comma-separated values |
| 11 | # Employees | Number | Format: Number, no decimals | Source for Employee Size |
| 12 | Employee Size | Select | **See mapping below** | Auto-populated from # Employees |
| 13 | Annual Revenue | Number | Format: Currency (USD) | Source for Revenue Range |
| 14 | Revenue Range | Select | **See mapping below** | Auto-populated from Annual Revenue |
| 15 | Total Funding | Number | Format: Currency (USD) | Optional; sparse data |
| 16 | Latest Funding | Text | Rich text: OFF | Funding round type (e.g., Series B) |
| 17 | Latest Funding Amount | Number | Format: Currency (USD) | Optional |
| 18 | Last Raised At | Date | Date format: YYYY-MM-DD | Optional |
| 19 | Company Address | Text | Rich text: OFF | Full address |
| 20 | Company City | Text | Rich text: OFF | City |
| 21 | Company State | Text | Rich text: OFF | State/Province |
| 22 | Company Country | Text | Rich text: OFF | Country |
| 23 | Company Phone | Phone | Standard phone format | Main company number |
| 24 | Subsidiary of | Text | Rich text: OFF | Parent company name |
| 25 | Subsidiary of (Organization ID) | Text | Rich text: OFF | Parent Apollo Account Id |
| 26 | Account Owner | Text | Rich text: OFF | Apollo system field |
| 27 | Company Name for Emails | Text | Rich text: OFF | Alternative email name |
| 28 | Contacts | Relation | **Relations setup: see below** | Links to Contacts database |
| 29 | Intelligence Records | Relation | **Relations setup: see below** | Links to Sales Intelligence |
| 30 | Activities | Relation | **Relations setup: see below** | Links to Outreach/Activities |
| 31 | Apollo Source | Checkbox | Default unchecked | Check on import |
| 32 | Risk Flag | Checkbox | Default unchecked | Check if missing website/name |

#### Select Property: Employee Size

**Available Options:**
- 1–10
- 11–50
- 51–200
- 201–500
- 501–1,000
- 1,001–5,000
- 5,001+

**No "Unknown" option** (leave blank if # Employees missing)

#### Select Property: Revenue Range

**Available Options:**
- Unknown
- <$1M
- $1M–$10M
- $10M–$50M
- $50M–$100M
- $100M–$500M
- $500M+

#### Select Property: Industry

**Available Options:** Generate from unique values in data  
Expected: ~500-1000 unique industries  
Recommend: Create on first import, allow new values on subsequent imports

---

### 1.2 Database 2: Contacts

**Display Name:** Contacts — Canonical  
**Description:** Single source of truth for all contacts. Primary key: Apollo Contact Id. All contacts MUST link to a company.  
**Icon:** 👤 (Person)  

#### Properties (Exact Specification)

| # | Property Name | Type | Configuration | Notes |
|---|---|---|---|---|
| 1 | Full Name | Title | Default title property | Formula: [First Name] + " " + [Last Name] |
| 2 | Apollo Contact Id | Text | Indexed, unique constraints | PRIMARY KEY; required |
| 3 | First Name | Text | Rich text: OFF | Required |
| 4 | Last Name | Text | Rich text: OFF | Required |
| 5 | Email | Email | Standard email format | Required if available; 95.7% coverage |
| 6 | Email Status | Select | **See options below** | Verification status |
| 7 | Primary Email Source | Text | Rich text: OFF | Where email came from |
| 8 | Primary Email Verification Source | Text | Rich text: OFF | How email was verified |
| 9 | Primary Email Catch-all Status | Text | Rich text: OFF | Catch-all domain check |
| 10 | Primary Email Last Verified At | Date | Date format: YYYY-MM-DD | Parse from timestamp |
| 11 | Secondary Email | Email | Standard email format | Optional; 18% coverage |
| 12 | Secondary Email Source | Text | Rich text: OFF | Where secondary came from |
| 13 | Secondary Email Status | Text | Rich text: OFF | Verification status |
| 14 | Secondary Email Verification Source | Text | Rich text: OFF | How verified |
| 15 | Tertiary Email | Email | Standard email format | Optional; 0% coverage in data |
| 16 | Title | Text | Rich text: OFF | Job title; required |
| 17 | Seniority | Select | Create values from data | C-Level, VP, Director, Manager, etc. |
| 18 | Departments | Text | Rich text: OFF | Comma-separated |
| 19 | Sub Departments | Text | Rich text: OFF | Comma-separated |
| 20 | Work Direct Phone | Phone | Standard phone format | Sparse; 1.3% coverage |
| 21 | Home Phone | Phone | Standard phone format | Sparse; 0.1% coverage |
| 22 | Mobile Phone | Phone | Standard phone format | 45.4% coverage |
| 23 | Corporate Phone | Phone | Standard phone format | 55.5% coverage |
| 24 | Other Phone | Phone | Standard phone format | 20.6% coverage |
| 25 | City | Text | Rich text: OFF | Contact's city |
| 26 | State | Text | Rich text: OFF | Contact's state |
| 27 | Country | Text | Rich text: OFF | Contact's country |
| 28 | Person Linkedin Url | URL | No validation required | LinkedIn profile |
| 29 | Stage | Select | Create values from data | Lead, Prospect, Customer, etc. |
| 30 | Lists | Text | Rich text: OFF | Comma-separated list names |
| 31 | Last Contacted | Date | Date format: YYYY-MM-DD | Parse from timestamp |
| 32 | Email Sent | Checkbox | Default unchecked | "True" = checked |
| 33 | Email Open | Checkbox | Default unchecked | "True" = checked |
| 34 | Email Bounced | Checkbox | Default unchecked | "True" = checked |
| 35 | Replied | Checkbox | Default unchecked | "True" = checked |
| 36 | Demoed | Checkbox | Default unchecked | "True" = checked |
| 37 | Company | Relation | **Relations setup: see below** | REQUIRED relation to Companies |
| 38 | Intelligence Records | Relation | **Relations setup: see below** | Links to Sales Intelligence |
| 39 | Activities | Relation | **Relations setup: see below** | Links to Outreach/Activities |
| 40 | Contact Owner | Text | Rich text: OFF | Apollo system field |
| 41 | Apollo Account Id | Text | Rich text: OFF | Link key for company match |
| 42 | Conduct targeted research 6305 | Text | Rich text: ON | AI research guidance |
| 43 | Qualify Contact | Text | Rich text: ON | Qualification criteria |
| 44 | Generate natural call scripts 5398 | Text | Rich text: ON | AI script generation |
| 45 | Prime research focus and context 1558 | Text | Rich text: ON | Research context |
| 46 | Contact Analysis 7680 | Text | Rich text: ON | AI analysis summary |
| 47 | Primary Intent Topic | Select | **LEAVE BLANK FOR PHASE 1** | Phase 2: Fetch from API |
| 48 | Primary Intent Score | Number | **LEAVE BLANK FOR PHASE 1** | Phase 2: Fetch from API |
| 49 | Secondary Intent Topic | Select | **LEAVE BLANK FOR PHASE 1** | Phase 2: Fetch from API |
| 50 | Secondary Intent Score | Number | **LEAVE BLANK FOR PHASE 1** | Phase 2: Fetch from API |
| 51 | Risk Flag | Checkbox | Default unchecked | Check if email missing or status issues |

#### Select Property: Email Status

**Available Options:**
- Verified
- Email No Longer Verified
- New Data Available
- Unavailable
- Extrapolated

#### Select Property: Seniority

**Available Options:** Generate from unique values in data  
Expected: 15-20 unique levels  
Common: C-Level, VP, Director, Manager, Specialist, Individual Contributor, etc.

#### Select Property: Stage

**Available Options:** Generate from unique values in data  
Expected: 5-10 unique stages  
Common: Lead, Prospect, Customer, etc.

---

### 1.3 Database 3: Sales Intelligence

**Display Name:** Sales Intelligence  
**Description:** AI research guidance and buying signals. Links to Company and Contact.  
**Icon:** 🧠 (Brain)  

#### Properties (Exact Specification)

| # | Property Name | Type | Configuration | Notes |
|---|---|---|---|---|
| 1 | Record Name | Title | Default title property | Auto-generated from Contact or Company |
| 2 | Company | Relation | **Relations setup: see below** | Links to Companies database |
| 3 | Contact | Relation | **Relations setup: see below** | Links to Contacts database |
| 4 | Primary Intent Topic | Select | **LEAVE BLANK FOR PHASE 1** | Phase 2 enrichment |
| 5 | Primary Intent Score | Number | **LEAVE BLANK FOR PHASE 1** | Phase 2 enrichment (0-100) |
| 6 | Secondary Intent Topic | Select | **LEAVE BLANK FOR PHASE 1** | Phase 2 enrichment |
| 7 | Secondary Intent Score | Number | **LEAVE BLANK FOR PHASE 1** | Phase 2 enrichment (0-100) |
| 8 | Priority Tier | Select | High, Medium, Low | Based on intent signals |
| 9 | Qualify Contact | Checkbox | Default unchecked | Use for filtering qualified leads |
| 10 | AI Summary | Text | Rich text: ON | Summary of AI analysis |
| 11 | Outreach Angle | Text | Rich text: ON | Recommended outreach approach |
| 12 | Buying Signal Summary | Text | Rich text: ON | Summary of buying signals |
| 13 | Last AI Refresh | Date | Date format: YYYY-MM-DD | When data last updated |

**Phase 1 Strategy:**
- Create records for contacts with "Contact Analysis 7680" populated
- Link to Contact and Company
- Populate AI Summary from Contact Analysis field
- Leave intent signals blank (fill in Phase 2)

---

### 1.4 Database 4: Outreach / Activities

**Display Name:** Outreach / Activities  
**Description:** Email campaigns and engagement activities. Links to Contact and Company.  
**Icon:** ✉️ (Mail)  

#### Properties (Exact Specification)

| # | Property Name | Type | Configuration | Notes |
|---|---|---|---|---|
| 1 | Activity Name | Title | Default title property | Auto-generated from contact |
| 2 | Contact | Relation | **Relations setup: see below** | Links to Contacts database |
| 3 | Company | Relation | **Relations setup: see below** | Links to Companies database |
| 4 | Email Sent | Checkbox | Default unchecked | Flag if sent |
| 5 | Email Open | Checkbox | Default unchecked | Flag if opened |
| 6 | Email Bounced | Checkbox | Default unchecked | Flag if bounced |
| 7 | Replied | Checkbox | Default unchecked | Flag if replied |
| 8 | Demoed | Checkbox | Default unchecked | Flag if demoed |
| 9 | Last Contacted | Date | Date format: YYYY-MM-DD | Last contact date |
| 10 | Current Funnel Stage | Select | Create values from data | Pipeline stage |
| 11 | Next Action | Text | Rich text: ON | Next step in sequence |
| 12 | Next Action Date | Date | Date format: YYYY-MM-DD | When to execute next action |

**Phase 1 Strategy:**
- Create minimal activity records for contacts with "Email Sent = True"
- Populate engagement flags from contact data
- Leave Next Action fields blank (fill in Phase 2)

---

### 1.5 Database 5: Apollo Sync Logs

**Display Name:** Apollo Sync Logs  
**Description:** Audit trail for all imports and updates. Track timing, counts, and exceptions.  
**Icon:** 📋 (Log)  

#### Properties (Exact Specification)

| # | Property Name | Type | Configuration | Notes |
|---|---|---|---|---|
| 1 | Sync Name | Title | Default title property | e.g., "Phase 1 Initial Build" |
| 2 | Sync Type | Select | Full Load, Incremental, Append, Update | Type of sync operation |
| 3 | Source | Text | Rich text: OFF | e.g., "CSV File Part 1", "Apollo API" |
| 4 | Trigger | Select | Initial Build, On-Demand, Scheduled, Manual | What triggered the sync |
| 5 | Started At | Date | Date format: YYYY-MM-DD HH:MM:SS | Start timestamp |
| 6 | Finished At | Date | Date format: YYYY-MM-DD HH:MM:SS | End timestamp |
| 7 | Total Records Read | Number | Format: Number | Total records processed |
| 8 | Companies Created | Number | Format: Number | Count of companies |
| 9 | Contacts Created | Number | Format: Number | Count of contacts |
| 10 | Records Updated | Number | Format: Number | Count of updates (Phase 2) |
| 11 | Exceptions Count | Number | Format: Number | Count of errors/issues |
| 12 | Notes | Text | Rich text: ON | Detailed summary |

**Phase 1 Sync Log Entry Example:**
```
Sync Name: Phase 1A — Companies Import
Sync Type: Full Load
Source: CSV Files (Part 1 + Part 2 merged)
Trigger: Initial Build
Started At: 2024-03-23 10:00:00
Finished At: 2024-03-23 10:45:00
Total Records Read: 5,901
Companies Created: 3,606
Contacts Created: 0 (Phase 1B)
Records Updated: 0
Exceptions Count: 3
Notes: Imported all companies. 3 exceptions: missing Apollo Account Id. Ready for Phase 1B contact import.
```

---

### 1.6 Database 6: Exception Log

**Display Name:** Exception Log  
**Description:** Data quality issues, orphan contacts, conflicts. Manual action tracking.  
**Icon:** ⚠️ (Warning)  

#### Properties (Exact Specification)

| # | Property Name | Type | Configuration | Notes |
|---|---|---|---|---|
| 1 | Exception | Title | Default title property | e.g., "Missing Apollo Account Id" |
| 2 | Record Id | Text | Rich text: OFF | Apollo Contact Id or Account Id |
| 3 | Record Name | Text | Rich text: OFF | Company Name or Full Name |
| 4 | Exception Type | Select | **See types below** | Categorize the issue |
| 5 | Severity | Select | High, Medium, Low | Priority level |
| 6 | Source Field | Text | Rich text: OFF | Which field caused issue |
| 7 | Description | Text | Rich text: ON | Detailed explanation |
| 8 | Remediation Notes | Text | Rich text: ON | How to fix |
| 9 | Created At | Date | Date format: YYYY-MM-DD HH:MM:SS | When logged |
| 10 | Resolved At | Date | Date format: YYYY-MM-DD HH:MM:SS | When fixed |
| 11 | Resolved | Checkbox | Default unchecked | Mark as resolved |
| 12 | Requires Manual Action | Checkbox | Default unchecked | Needs human review |

#### Select Property: Exception Type

**Available Options:**
- Missing Primary Key
- Orphan Contact (Company not found)
- Invalid Email
- Invalid URL
- Duplicate Primary Key
- Type Conversion Failure
- Missing Required Field
- Inconsistent Data
- Other

**Phase 1 Expected Exceptions:**
- 3x "Missing Primary Key" (Apollo Account Id)
- 0-5x "Missing Email" (optional)
- 0-2x "Missing Website" (optional)

---

## 2. RELATION CONFIGURATION

### 2.1 Companies ↔ Contacts Relation

**Property on Companies:** Contacts  
**Property on Contacts:** Company  
**Link Type:** One-to-Many (bidirectional)

**Configuration:**
```
Companies.Contacts (Relation)
├─ Database: Contacts
├─ Related property: Company
├─ Allow multiple: Yes
├─ Show link count: Yes
└─ Related database options:
    ├─ Filter by: (none — show all contacts for company)
    ├─ Sort by: (recommend: Last Name)
    └─ Show: Full Name, Email, Title

Contacts.Company (Relation)
├─ Database: Companies
├─ Related property: Contacts
├─ Allow multiple: No (single company per contact)
├─ Show link count: Yes
├─ **REQUIRED: Is this property required?** YES
└─ Related database options:
    ├─ Filter by: (none)
    ├─ Sort by: (none)
    └─ Show: Company Name, Industry, Employee Size
```

**Cardinality Constraint:**
- Each Contact MUST have exactly ONE Company
- Each Company can have ZERO to MANY Contacts
- Cannot create contact without company link

---

### 2.2 Companies → Sales Intelligence Relation

**Property on Companies:** Intelligence Records  
**Property on Sales Intelligence:** Company  
**Link Type:** One-to-Many (bidirectional)

**Configuration:**
```
Companies.Intelligence Records (Relation)
├─ Database: Sales Intelligence
├─ Related property: Company
├─ Allow multiple: Yes
├─ Show link count: Yes

Sales Intelligence.Company (Relation)
├─ Database: Companies
├─ Related property: Intelligence Records
├─ Allow multiple: No
└─ Show link count: Yes
```

---

### 2.3 Contacts → Sales Intelligence Relation

**Property on Contacts:** Intelligence Records  
**Property on Sales Intelligence:** Contact  
**Link Type:** One-to-Many (bidirectional)

**Configuration:**
```
Contacts.Intelligence Records (Relation)
├─ Database: Sales Intelligence
├─ Related property: Contact
├─ Allow multiple: Yes
├─ Show link count: Yes

Sales Intelligence.Contact (Relation)
├─ Database: Contacts
├─ Related property: Intelligence Records
├─ Allow multiple: No
└─ Show link count: Yes
```

---

### 2.4 Companies → Activities Relation

**Property on Companies:** Activities  
**Property on Outreach/Activities:** Company  
**Link Type:** One-to-Many (bidirectional)

**Configuration:**
```
Companies.Activities (Relation)
├─ Database: Outreach / Activities
├─ Related property: Company
├─ Allow multiple: Yes
├─ Show link count: Yes

Outreach.Company (Relation)
├─ Database: Companies
├─ Related property: Activities
├─ Allow multiple: No
└─ Show link count: Yes
```

---

### 2.5 Contacts → Activities Relation

**Property on Contacts:** Activities  
**Property on Outreach/Activities:** Contact  
**Link Type:** One-to-Many (bidirectional)

**Configuration:**
```
Contacts.Activities (Relation)
├─ Database: Outreach / Activities
├─ Related property: Contact
├─ Allow multiple: Yes
├─ Show link count: Yes

Outreach.Contact (Relation)
├─ Database: Contacts
├─ Related property: Activities
├─ Allow multiple: No
└─ Show link count: Yes
```

---

## 3. DATABASE VIEWS & TEMPLATES

### 3.1 Recommended Views for Phase 1

**Companies Database:**
1. **All Companies** (Table view)
   - Show: Name, Apollo Account Id, Domain, Industry, Employee Size, Contacts
   - Sort: Company Name
   - Filter: Risk Flag = unchecked

2. **Companies at Risk** (Table view)
   - Show: Name, Domain, Website, Industry, Risk Flag reason
   - Filter: Risk Flag = checked
   - Sort: Industry

3. **By Revenue** (Table view)
   - Show: Name, Annual Revenue, Revenue Range, Industry
   - Sort: Annual Revenue (descending)
   - Filter: Revenue Range ≠ Unknown

4. **By Employee Size** (Table view)
   - Show: Name, # Employees, Employee Size, Industry
   - Group By: Employee Size

**Contacts Database:**
1. **All Contacts** (Table view)
   - Show: Full Name, Company, Email, Title, Seniority, Last Contacted
   - Sort: Company, Last Name
   - Filter: Risk Flag = unchecked

2. **Contacts at Risk** (Table view)
   - Show: Full Name, Company, Email, Email Status, Risk Flag reason
   - Filter: Risk Flag = checked

3. **By Title & Seniority** (Table view)
   - Show: Full Name, Company, Title, Seniority, Email
   - Group By: Seniority

4. **Email Verification** (Table view)
   - Show: Full Name, Company, Email, Email Status, Last Verified
   - Filter: Email Status ≠ Verified
   - Sort: Last Verified (oldest first)

5. **Recently Contacted** (Table view)
   - Show: Full Name, Company, Last Contacted, Email Sent, Email Open, Replied
   - Filter: Last Contacted ≠ empty
   - Sort: Last Contacted (newest first)

**Sales Intelligence Database:**
1. **All Intelligence** (Table view)
   - Show: Record Name, Company, Contact, AI Summary, Priority Tier
   - Sort: Created (newest first)

2. **High Priority** (Table view)
   - Show: Record Name, Company, Contact, Priority Tier, Outreach Angle
   - Filter: Priority Tier = High

**Outreach/Activities Database:**
1. **All Activities** (Table view)
   - Show: Activity Name, Contact, Company, Last Contacted, Current Stage
   - Sort: Last Contacted (newest first)

2. **Email Engagement** (Table view)
   - Show: Activity Name, Contact, Company, Email Sent, Email Open, Replied
   - Filter: Email Sent = checked
   - Sort: Last Contacted

---

## 4. DATA IMPORT SEQUENCE

### Step 1: Create All Databases (0.5 hours)
```
1. Create "Companies — Canonical" database
2. Create "Contacts — Canonical" database
3. Create "Sales Intelligence" database
4. Create "Outreach / Activities" database
5. Create "Apollo Sync Logs" database
6. Create "Exception Log" database
```

### Step 2: Create All Properties (1-2 hours)
```
1. Add all properties to Companies (32 properties)
2. Add all properties to Contacts (51 properties)
3. Add all properties to Sales Intelligence (13 properties)
4. Add all properties to Outreach/Activities (12 properties)
5. Add all properties to Apollo Sync Logs (12 properties)
6. Add all properties to Exception Log (12 properties)
```

### Step 3: Set Up Relations (30 mins)
```
1. Create Companies ↔ Contacts relation
2. Create Companies → Sales Intelligence relation
3. Create Contacts → Sales Intelligence relation
4. Create Companies → Activities relation
5. Create Contacts → Activities relation
6. Verify all bidirectional links work
```

### Step 4: Validation Batch (100 records) (1 hour)
```
1. Transform CSV to Notion format (100 rows)
2. Create 50 companies (from 100 contact records)
3. Create 100 contacts and link to companies
4. Verify no orphans (100% linked)
5. Verify primary keys unique
6. Sample check: domain extraction
7. Sample check: size/range mapping
8. Check Exception Log count (<1 expected)
9. PASS/FAIL decision
```

### Step 5: Full Import (2-3 hours)
```
1. Transform CSV to Notion format (5,901 rows)
2. Create 3,606 companies
3. Create 5,898 contacts and link to companies
4. Create intelligence records (stubs)
5. Create activity records (stubs)
6. Log all operations in Apollo Sync Logs
7. Log all exceptions in Exception Log
8. Verify final counts match expectations
```

### Step 6: Validation & QA (30 mins)
```
1. Verify company count = 3,606
2. Verify contact count = 5,898
3. Verify exception count = 3 (missing Account Id)
4. Verify orphan count = 0
5. Verify duplicate count = 0
6. Sample check: 10 domain extractions
7. Sample check: 10 size mappings
8. Sample check: 10 range mappings
9. Verify all relations bidirectional
10. Sign off Phase 1 complete
```

---

## 5. ERROR HANDLING & ROLLBACK

### Validation Errors During Import

**If validation batch FAILS:**
1. Stop import
2. Review error logs
3. Fix transformation logic
4. Run validation batch again
5. Only proceed to full import if batch passes

**If full import encounters errors:**
1. Log error with record details
2. Continue processing (non-blocking)
3. Add to Exception Log
4. Resume from checkpoint
5. Generate error report at end

### Rollback Procedure

**If full import must be rolled back:**
1. Delete all records from 6 databases
2. Verify databases are empty
3. Fix issue in transformation logic
4. Restart full import from beginning
5. Document what went wrong
6. Update Phase 1 report with lessons learned

---

## 6. PERFORMANCE CONSIDERATIONS

### Import Timing Estimates
- 100 record validation batch: 5-10 minutes
- 3,606 companies import: 15-20 minutes
- 5,898 contacts import: 30-45 minutes
- Relation building: 5-10 minutes
- Intelligence records (stubs): 10-15 minutes
- Activity records (stubs): 10-15 minutes
- **Total Phase 1 build time: 1.5-2 hours**

### Database Size After Phase 1
- Companies database: 3,606 pages
- Contacts database: 5,898 pages
- Sales Intelligence: 4,000-5,000 pages (stubs)
- Outreach/Activities: 2,000-3,000 pages (stubs)
- Apollo Sync Logs: 1 page (Phase 1A)
- Exception Log: 3-5 pages

### Query Performance (After Phase 1)
- Filter companies by revenue: <500ms
- Filter contacts by title: <500ms
- Load all contacts for company: <1000ms
- Relation lookups: <100ms

---

## 7. SECURITY & PERMISSIONS

### Access Control
- **Phase 1 Build:** Full read/write access to implementation engineer
- **Post-Phase 1:** Sales team gets read-only view
- **Phase 2 Enrichment:** Automated API access (MCP) for intent data

### Data Sensitivity
- ✅ Contact emails: Low sensitivity (commercial databases)
- ✅ Company financials: Low sensitivity (public sources)
- ✅ Personal data: Ensure GDPR compliance if EU contacts
- ✅ Intent signals: Internal use only

### Audit Trail
- All imports logged in Apollo Sync Logs
- Exception Log provides full transparency
- Timestamps on all operations
- User attribution on all changes (Phase 2)

---

## 8. TESTING CHECKLIST

**Before Validation Batch:**
- [ ] All 6 databases exist
- [ ] All properties created with correct types
- [ ] All relations configured bidirectionally
- [ ] All select lists populated
- [ ] Sample records viewable in Notion
- [ ] Domain extraction logic coded and tested
- [ ] Date parsing logic tested
- [ ] Size mapping logic tested
- [ ] Range mapping logic tested

**During Validation Batch (100 records):**
- [ ] 50 companies created
- [ ] 100 contacts created
- [ ] 100 company links verified
- [ ] 0 orphan contacts
- [ ] 0 duplicate keys
- [ ] 0 errors in exception handling
- [ ] All dates parsed correctly
- [ ] All URLs valid
- [ ] Sample domain extraction correct
- [ ] Sample size mapping correct
- [ ] Sample range mapping correct

**After Full Import (5,901 records):**
- [ ] 3,606 companies created
- [ ] 5,898 contacts created
- [ ] 3 exceptions logged (missing Account Id)
- [ ] 0 orphan contacts
- [ ] 0 duplicate keys
- [ ] All relations bidirectional
- [ ] Sample check: 20 domain extractions
- [ ] Sample check: 20 size mappings
- [ ] Sample check: 20 range mappings
- [ ] Exception Log complete
- [ ] Sync Log entry complete
- [ ] All required fields populated
- [ ] All optional fields handled
- [ ] Views accessible and functional

---

## 9. DOCUMENTATION & HANDOFF

**Deliverables on Completion:**
1. ✅ Phase 1 Audit & Schema document
2. ✅ Field Mapping Rules document
3. ✅ Validation Risk Report
4. ✅ Executive Summary & Next Steps
5. ✅ Technical Reference (this document)
6. ✅ Implementation logs & audit trails
7. ✅ Exception Log (data issues)
8. ✅ Apollo Sync Logs (import history)

**Handoff to Sales Team:**
1. Access to Companies database (read-only initially)
2. Access to Contacts database (read-only initially)
3. Training on database views and filters
4. Documentation of how to use Sales Intelligence
5. Outreach/Activities workflow guide

**Handoff to Phase 2:**
1. Fully populated Notion databases
2. Apollo API integration requirements
3. Intent signal enrichment plan
4. Direct sync mode specifications
5. Segment targeting use cases

---

**End of Technical Reference Document**

**Ready for Notion Implementation**
