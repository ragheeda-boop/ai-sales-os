# 📋 PHASE 1B DATA VALIDATION RULES
## Field Mappings & Quality Checks

**Purpose:** Define exact field validation for import & QA
**Audience:** RevOps, Data Engineer, QA Lead
**Phase:** 1B (Import & Linking)

---

## 🏢 COMPANIES IMPORT VALIDATION

### Required Fields (100% Must Be Populated)

| Field | Source | Notion Field | Validation Rule | Accept Blank? |
|-------|--------|--------------|-----------------|---------------|
| **Company Name** | Apollo | Name | Non-empty string, <200 chars | ❌ NO |
| **Domain** | Apollo | Domain | Valid domain format (x.com) | ❌ NO |
| **Apollo Account ID** | Apollo | Apollo_ID | Unique UUID, primary key | ❌ NO |

### Expected Fields (≥90% Populated)

| Field | Source | Notion Field | Validation Rule | Min % |
|-------|--------|--------------|-----------------|-------|
| Industry | Apollo | Industry | Non-empty string | 95% |
| Company Size | Apollo | Company_Size | One of: 1-10, 11-50, 51-200, 201-500, 501-1K, 1K+ | 90% |
| Revenue Range | Apollo | Revenue_Range | Non-empty (if available) | 85% |
| Latest Funding | Apollo | Latest_Funding_Stage | One of: Seed, Series A-H, IPO, Acquired | 75% |

### Optional Fields (Can be blank, but populate if available)

| Field | Source | Notion Field | Usage |
|-------|--------|--------------|-------|
| Website | Apollo | Website_URL | Linked source |
| Employees | Apollo | Employee_Count | Intelligence |
| Founded Year | Apollo | Founded_Year | B2B intent |
| Tech Stack | Apollo | Technologies_Using | Account targeting |
| Phone | Apollo | Phone | Outreach |

### Sample Valid Company Record:
```json
{
  "Name": "Acme Corporation",
  "Domain": "acme.com",
  "Apollo_ID": "507f1f77bcf86cd799439011",
  "Industry": "SaaS",
  "Company_Size": "201-500",
  "Revenue_Range": "$10M-$50M",
  "Latest_Funding_Stage": "Series B",
  "Website_URL": "https://acme.com",
  "Employee_Count": 350,
  "Technologies_Using": "Salesforce, HubSpot, Stripe"
}
```

### Data Quality Checks for Companies:

```
REQUIRED CHECKS (FAIL = Data issue):
☐ Every company has unique Apollo_ID (0 duplicates)
☐ Every domain is unique (0 duplicate domains)
☐ Every name is non-empty
☐ Domain format valid (contains .)

EXPECTED CHECKS (WARN = Monitor):
☐ Industry populated ≥95% (OK if 5%+ missing)
☐ Company_Size populated ≥90% (OK if 10%+ missing)
☐ No obviously fake domains (no "test.com", "example.com")
☐ Phone numbers: If present, valid format

SPOT CHECKS (Random sample of 50):
☐ Company names readable (no garbage data)
☐ Domains look legitimate (no "aaaaaa.com")
☐ Industry matches domain (e.g., SaaS = tech domain)
☐ Size makes sense for industry
```

---

## 👤 CONTACTS IMPORT VALIDATION

### Critical Fields (100% Must Be Populated)

| Field | Source | Notion Field | Validation Rule | Accept Blank? |
|-------|--------|--------------|-----------------|---------------|
| **Contact Name** | Apollo | Name | Non-empty string, <200 chars | ❌ NO |
| **Apollo Contact ID** | Apollo | Apollo_ID | Unique UUID, primary key | ❌ NO |
| **Company Domain** | Apollo | Company_Domain | Valid domain for linking | ❌ NO |

### Email & Contact Info (≥95% Should Have)

| Field | Source | Notion Field | Validation Rule | Min % |
|-------|--------|--------------|-----------------|-------|
| Email | Apollo | Email | Valid email format (name@domain.com) | 95.7% |
| Title | Apollo | Title | Job title string | 85% |
| Seniority | Apollo | Seniority | One of: IC, Lead, Manager, Director, VP, C-Suite | 80% |
| Phone | Apollo | Phone | Valid phone format (if present) | 30% |

### Account Info (Should Match Companies)

| Field | Source | Notion Field | Validation Rule | Usage |
|-------|--------|--------------|-----------------|-------|
| Company Name | Apollo | Company_Name | Matches company name | Verification |
| Industry | Apollo | Industry | Pulled from company | Intelligence |
| Company Size | Apollo | Company_Size | Pulled from company | Segmentation |

### Optional Fields (Enrich if available)

| Field | Source | Notion Field | Usage |
|-------|--------|--------------|-------|
| LinkedIn URL | Apollo | LinkedIn_URL | Profile |
| Engagement Score | Apollo | Engagement_Score | Scoring |
| Intent Signals | Apollo | Intent_Signals | Lead quality |
| Last Activity | Apollo | Last_Activity_Date | Recency |

### Sample Valid Contact Record:
```json
{
  "Name": "John Smith",
  "Apollo_ID": "507f1f77bcf86cd799439012",
  "Email": "john.smith@acme.com",
  "Title": "VP Sales",
  "Seniority": "VP",
  "Company_Name": "Acme Corporation",
  "Company_Domain": "acme.com",
  "Phone": "+1 (555) 123-4567",
  "LinkedIn_URL": "https://linkedin.com/in/johnsmith",
  "Engagement_Score": 72,
  "Intent_Signals": ["Product Demo Viewed", "Pricing Page Visited"]
}
```

### Data Quality Checks for Contacts:

```
CRITICAL CHECKS (FAIL = Re-import):
☐ Every contact has unique Apollo_ID (0 duplicates)
☐ Every contact has Company_Domain (0 empty)
☐ Every name is non-empty
☐ Email format valid (if populated): user@domain.com

EMAIL CHECKS (IMPORTANT):
☐ Email coverage: ≥95.7% populated
☐ Email format validation: 99%+ clean (spot check)
☐ No test emails (test@, fake@, noemail@, etc)
☐ Domain matches company domain (95%+ valid match)

SENIORITY MAPPING (Check for odd values):
☐ Values fall within defined set
☐ "C-Suite" includes CEO, CFO, CTO, etc
☐ "VP" is distinct from "Director"
☐ "IC" is for individual contributors

SPOT CHECKS (Random sample of 50):
☐ Names readable (no garbage data)
☐ Emails realistic (no "xxxxxx@acme.com")
☐ Title matches seniority (VP = VP seniority)
☐ LinkedIn URLs valid (start with linkedin.com)
```

---

## 🔗 LINKING VALIDATION

### Linking Criteria:

```
Contact → Company Link Rules:

EXACT MATCH (100% success expected):
└─ Contact.Company_Domain = Company.Domain
   Example: john@acme.com → Company.Domain = "acme.com"

EMAIL DOMAIN EXTRACTION:
├─ Extract domain from contact email
├─ Normalize (remove www., convert to lowercase)
└─ Match to company domain

PRIORITY ORDER:
1. Company_Domain field (if provided)
2. Email domain (extracted from email address)
3. Company_Name field (fallback, not recommended)
```

### Linking Success Criteria:

```
MUST ACHIEVE:
☐ 5,898 / 5,898 contacts linked (100%)
☐ 0 orphaned contacts (no contact without company)
☐ 0 error_count in linking_log.json
☐ error_array.length = 0

SUCCESS RATE CALCULATION:
success_rate = (linked_count / total_count) × 100
Target: ≥99.98% (max 1 error per 5,000)

ACTUAL TARGETS:
99% success = 5,844 linked, 54 errors
99.98% success = 5,897 linked, 1 error
100% success = 5,898 linked, 0 errors
```

### Linking Output Validation:

```json
// linking_log.json should look like this:
{
  "timestamp": "2026-03-25T14:30:00Z",
  "total_contacts": 5898,
  "linked_count": 5898,
  "error_count": 0,
  "success_rate": 100.0,
  "errors": [],
  "summary": {
    "companies_found": 3606,
    "unique_domains": 3600,
    "contacts_processed": 5898,
    "avg_contacts_per_company": 1.64
  }
}
```

---

## ✅ QA VALIDATION CHECKLIST

### Phase 1: Completeness (30 min)

**Companies (N=3,606):**
```
☐ Count: SELECT COUNT(*) WHERE [Name] IS NOT NULL = 3,606
☐ Unique IDs: COUNT(DISTINCT [Apollo_ID]) = 3,606
☐ No blanks: COUNT(*) WHERE [Domain] IS NOT NULL = 3,606
☐ Email coverage: Will be checked in contacts
```

**Contacts (N=5,898):**
```
☐ Count: SELECT COUNT(*) WHERE [Name] IS NOT NULL = 5,898
☐ Unique IDs: COUNT(DISTINCT [Apollo_ID]) = 5,898
☐ Email coverage: COUNT(*) WHERE [Email] IS NOT NULL ≥ 5,632 (95.7%)
☐ Company links: COUNT(*) WHERE [Company_Domain] IS NOT NULL = 5,898
```

### Phase 2: Validity (60 min)

**Email Validation (Random sample of 100):**
```
Regex: ^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$

☐ Format check: All emails match pattern ✓
☐ No test emails: 0 records with test@, fake@, noemail@
☐ Domain check: 95%+ contact domain matches company domain
☐ Duplicates: 0 duplicate emails in sample
```

**Seniority Validation (Check all):**
```
Allowed values:
  ["IC", "Lead", "Manager", "Director", "VP", "C-Suite", ""]

☐ Count of each value (should see distribution):
  - IC: ~20%
  - Lead: ~15%
  - Manager: ~20%
  - Director: ~15%
  - VP: ~10%
  - C-Suite: ~5%
  - Blank: ~15%
☐ No invalid values found
```

**Company Size Validation (Check all):**
```
Allowed values:
  ["1-10", "11-50", "51-200", "201-500", "501-1K", "1K+", ""]

☐ Distribution makes sense
☐ No obviously wrong mappings
☐ Spot check: 1-10 employee companies have low revenue
```

### Phase 3: Relationships (60 min)

**Bidirectional Links:**
```
☐ Open random company → View contacts → Count = N
☐ Open each contact record → Verify "Company" field filled
☐ Click company link → Confirms company record
☐ Return to contact → Confirms link persists

Sample size: 10 companies
```

**Orphan Check:**
```
Contact Orphans:
☐ COUNT(*) WHERE [Company] IS NULL = 0

Company Isolated:
☐ COUNT(*) WHERE [Related_Contacts] = 0
  (Some companies may have 0 contacts - OK)
```

### Phase 4: Integrity (30 min)

**No Duplicates:**
```
☐ Company domains: COUNT(DISTINCT domain) = COUNT(*)
☐ Contact Apollo IDs: COUNT(DISTINCT id) = COUNT(*)
☐ Contact emails: COUNT(DISTINCT email) < total (some people have same email)
```

**Search & Filter Tests:**
```
☐ Search "Acme" in companies → Returns results
☐ Filter by Industry "SaaS" → Returns results
☐ Filter by Company Size "201-500" → Returns results
☐ Search "john.smith@acme.com" → Finds contact
☐ Search "+1 (555) 123" → Finds contact (if phone present)
```

**Export Test:**
```
☐ Select all companies → Export to CSV
☐ File created without error
☐ Row count = 3,606
☐ All fields present in export
```

### QA Grading Rubric:

```
A+ (95-100%):
  ✅ All critical checks pass
  ✅ <5 issues found in completeness
  ✅ All validation tests green
  ✅ 0 duplicates
  ✅ 100% linked
  → APPROVED: Proceed to Phase 2

A (85-94%):
  ✅ All critical checks pass
  ✅ 5-10 issues found (minor)
  ✅ Some email coverage <95% (EXPECTED)
  ⚠️  Minor field gaps documented
  → APPROVED WITH NOTES: Proceed, track issues

B (75-84%):
  ⚠️  Critical checks have failures
  ⚠️  >10 issues found
  ⚠️  Email coverage <90%
  ❌ Some duplicates detected
  → CONDITIONAL: Fix issues, revalidate

C (<75%):
  ❌ Multiple critical checks fail
  ❌ >20 issues found
  ❌ Data quality compromised
  → REJECT: Stop, re-import from start
```

---

## 🎯 FINAL VALIDATION SIGN-OFF

```
By signing below, I confirm:

DATA ENGINEER:
Name: _________________ Date: _______ Signature: _______
I confirm:
☐ All 3,606 companies imported correctly
☐ All 5,898 contacts imported correctly
☐ Linking script executed with 100% success

QA LEAD:
Name: _________________ Date: _______ Signature: _______
I confirm:
☐ Data completeness: A+ grade
☐ Data validity: All tests pass
☐ Data relationships: 100% linked
☐ Ready for Phase 2

PROJECT LEAD:
Name: _________________ Date: _______ Signature: _______
I confirm:
☐ Phase 1B complete and validated
☐ All deliverables met
☐ Ready for Phase 2 kickoff: [DATE]
```

---

**Document Version:** 1.0
**Last Updated:** March 24, 2026
**Classification:** Internal - Technical Reference
