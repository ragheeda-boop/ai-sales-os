# FIELD MAPPING & TRANSFORMATION RULES — VERSION 3.2

## 1. MAPPING OVERVIEW

This document defines exactly how each Apollo field maps to Notion properties, including data type conversions, validation rules, and transformation logic. Updated for Phase 2/3 with Lead Scoring, Lead Tier classification, and Action Ready gating.

---

## 2. CONTACT FIELD MAPPINGS

### CONTACT IDENTITY
| Apollo Field | Notion Property | Type | Transform | Validation |
|---|---|---|---|---|
| Apollo Contact Id | Apollo Contact Id | Text (indexed) | As-is | Required, unique |
| First Name | First Name | Text | Trim whitespace | Required |
| Last Name | Last Name | Text | Trim whitespace | Required |
| *computed* | Full Name | Formula | `[First Name] + " " + [Last Name]` | Automatic |

### CONTACT EMAIL
| Apollo Field | Notion Property | Type | Transform | Validation |
|---|---|---|---|---|
| Email | Email | Email | Lowercase, trim | If blank, flag Risk Flag |
| Email Status | Email Status | Select | As-is | Values: Verified, Email No Longer Verified, New Data Available, Unavailable, Extrapolated |
| Primary Email Source | Primary Email Source | Text | As-is | Reference info |
| Primary Email Verification Source | Primary Email Verification Source | Text | As-is | Reference info |
| Primary Email Catch-all Status | Primary Email Catch-all Status | Text | As-is | Reference info |
| Primary Email Last Verified At | Primary Email Last Verified At | Date | Parse: "YYYY-MM-DD" | If unparseable, leave blank |
| Email Confidence | *skip* | N/A | N/A | Coverage too sparse (0.2%); skip on build |
| Secondary Email | Secondary Email | Email | Lowercase, trim | Optional |
| Secondary Email Source | Secondary Email Source | Text | As-is | Reference info |
| Secondary Email Status | Secondary Email Status | Text | As-is | Reference info |
| Secondary Email Verification Source | Secondary Email Verification Source | Text | As-is | Reference info |
| Tertiary Email | *skip* | N/A | N/A | No data in export |

### CONTACT PHONE
| Apollo Field | Notion Property | Type | Transform | Validation |
|---|---|---|---|---|
| Work Direct Phone | Work Direct Phone | Phone | Trim | Optional, sparse |
| Home Phone | Home Phone | Phone | Trim | Optional, sparse |
| Mobile Phone | Mobile Phone | Phone | Trim | Optional |
| Corporate Phone | Corporate Phone | Phone | Trim | Optional |
| Other Phone | Other Phone | Phone | Trim | Optional |

### CONTACT LOCATION
| Apollo Field | Notion Property | Type | Transform | Validation |
|---|---|---|---|---|
| City | City | Text | Trim | Person's location |
| State | State | Text | Trim | Person's location |
| Country | Country | Text | Trim | Person's location |

### CONTACT PROFESSIONAL
| Apollo Field | Notion Property | Type | Transform | Validation |
|---|---|---|---|---|
| Title | Title | Text | Trim | Required |
| Seniority | Seniority | Select | Normalize via SENIORITY_NORMALIZE map | Preserve Apollo values, unify variants |
| Departments | Departments | Text | Trim | Comma-separated |
| Sub Departments | Sub Departments | Text | Trim | Comma-separated |
| Person Linkedin Url | Person Linkedin Url | URL | Trim | Optional, validate URL format |

### CONTACT ENGAGEMENT SIGNALS (Phase 1/2)
| Apollo Field | Notion Property | Type | Transform | Validation |
|---|---|---|---|---|
| Email Sent | Email Sent | Checkbox | "True" → ✓, only if Apollo explicitly returns field | Email outreach flag; safe boolean write |
| Email Open | Email Opened | Checkbox | "True" → ✓, only if Apollo explicitly returns field | Email engagement flag; safe boolean write |
| Email Bounced | Email Bounced | Checkbox | "True" → ✓, only if Apollo explicitly returns field | Email quality flag; safe boolean write |
| Replied | Replied | Checkbox | "True" → ✓, only if Apollo explicitly returns field | Positive engagement; safe boolean write |
| Demoed | Demoed | Checkbox | "True" → ✓, only if Apollo explicitly returns field | Sales stage signal; safe boolean write |
| Meeting Booked | Meeting Booked | Checkbox | "True" → ✓, only if Apollo explicitly returns field | Sales signal; safe boolean write |
| Last Contacted | Last Contacted | Date | Parse: "YYYY-MM-DD" or "YYYY-MM-DD HH:MM:SS" | Track engagement timeline |

### CONTACT OUTREACH & STAGE
| Apollo Field | Notion Property | Type | Transform | Validation |
|---|---|---|---|---|
| Outreach Status | Outreach Status | Select | As-is from Apollo | Values: Do Not Contact, Bounced, Bad Data, etc. — blocks Action Ready |
| Stage | Stage | Select | As-is from Apollo | Values: Lead, Prospect, Customer, Churned, etc. |
| Do Not Call | Do Not Call | Checkbox | As-is from Apollo | Blocks Action Ready if TRUE |

### CONTACT INTENT & SCORING (Phase 2/3)
| Apollo Field | Notion Property | Type | Transform | Validation |
|---|---|---|---|---|
| Intent Topic | Intent Score | Number (0–10) | Fetch from Apollo API; normalized to 0-10 scale | Sparse field; part of Lead Score formula |
| *N/A* | Primary Intent Topic | Select | Fetch from Apollo API Phase 3 | Intent research topic; optional |
| *N/A* | Secondary Intent Topic | Select | Fetch from Apollo API Phase 3 | Intent research topic; optional |

### CONTACT LEAD SCORING (Phase 2/3 — CRITICAL)
| Computed Field | Notion Property | Type | Calculation | Notes |
|---|---|---|---|---|
| *formula* | Lead Score | Number (0–100) | `(Intent×10%) + (Engagement×10%) + (Size×45%) + (Seniority×35%)` | **v1.1 weights** — lead_score.py writes this |
| *formula* | Lead Tier | Select | HOT (≥80) / WARM-HIGH (60–79) / WARM (50–59) / COLD (<50) | Categorical classification; written by lead_score.py alongside score |

**Lead Score Formula Rationale:** 
- Intent (10%): Mostly empty for cold Apollo data with no outreach history
- Engagement (10%): Sparse — Email Sent/Replied/etc. only populated for contacted contacts
- Company Size (45%): Available for 98%+ of records; strong proxy for deal value
- Seniority (35%): Available for 95%+ of records; decision-maker indicator

**Future v2.0 Activation:** Do NOT switch to v2.0 weights (Intent 30%, Engagement 25%, Signals 25%, Size 10%, Seniority 10%) until Job Postings, Job Change Detection, and Intent Trend data are populated. Giving weight to empty fields weakens scores.

### CONTACT ACTION READINESS (Phase 2/3 — CRITICAL)
| Computed Field | Notion Property | Type | Rule | Notes |
|---|---|---|---|---|
| *5-condition gate* | Action Ready | Checkbox | TRUE if ALL conditions: (1) Lead Score ≥ 50, (2) Do Not Call = FALSE, (3) Outreach Status NOT in {Do Not Contact, Bounced, Bad Data}, (4) Stage NOT in {Customer, Churned}, (5) Has Email OR Phone | action_ready_updater.py evaluates; blocks task creation if FALSE |

### CONTACT ACTIVITY TRACKING (Phase 2/3)
| Apollo Field | Notion Property | Type | Transform | Validation |
|---|---|---|---|---|
| *N/A* | Contact Responded | Checkbox | Implied by Replied=TRUE or Meeting Booked=TRUE | Sales signal; updated by sync |
| *N/A* | First Contact Attempt | Date | Set on first Email Sent or Meeting Booked | Engagement timeline; updated by sync |
| *N/A* | Opportunity Created | Checkbox | Set when Stage transitions to "Opportunity" or higher | Sales stage signal; updated by sync |

### CONTACT ENGAGEMENT CLASSIFICATION
| Apollo Field | Notion Property | Type | Transform | Validation |
|---|---|---|---|---|
| Stage | Stage | Select | As-is | Preserve Apollo stage value |
| Lists | Lists | Text | Trim, preserve as comma-separated | Contact list membership |

### CONTACT SYSTEM
| Apollo Field | Notion Property | Type | Transform | Validation |
|---|---|---|---|---|
| Contact Owner | Contact Owner | Text | Trim | Apollo system field |

### CONTACT RESEARCH & INTELLIGENCE (AI Fields)
| Apollo Field | Notion Property | Type | Transform | Validation |
|---|---|---|---|---|
| Conduct targeted research 6305 | Conduct targeted research 6305 | Rich Text | Preserve formatting | AI research guidance |
| Qualify Contact | Qualify Contact | Rich Text | Preserve formatting | Qualification criteria |
| Generate natural call scripts 5398 | Generate natural call scripts 5398 | Rich Text | Preserve formatting | AI-generated outreach |
| Prime research focus and context 1558 | Prime research focus and context 1558 | Rich Text | Preserve formatting | Research context |
| Contact Analysis 7680 | Contact Analysis 7680 | Rich Text | Preserve formatting | AI analysis summary |

---

## 3. COMPANY FIELD MAPPINGS

### COMPANY IDENTITY
| Apollo Field | Notion Property | Type | Transform | Validation |
|---|---|---|---|---|
| Apollo Account Id | Apollo Account Id | Text (indexed) | As-is | Required, unique per company |
| Company Name | Company Name (Title) | Title | Trim | Required; use as Notion page title |
| Company Name for Emails | Company Name for Emails | Text | Trim | Reference name |
| *computed* | Domain | Text | Extract from Website (see rules) | Validation only; NOT primary key |

### COMPANY CONTACT
| Apollo Field | Notion Property | Type | Transform | Validation |
|---|---|---|---|---|
| Company Phone | Company Phone | Phone | Trim | Optional |
| Company Address | Company Address | Text | Trim | Full address |
| Company City | Company City | Text | Trim | City |
| Company State | Company State | Text | Trim | State/Province |
| Company Country | Company Country | Text | Trim | Country |

### COMPANY ONLINE
| Apollo Field | Notion Property | Type | Transform | Validation |
|---|---|---|---|---|
| Website | Website | URL | Trim whitespace, add http:// if missing | Optional but strongly recommended |
| Company Linkedin Url | Company Linkedin Url | URL | Trim | Optional |
| Facebook Url | Facebook Url | URL | Trim | Optional, sparse |
| Twitter Url | Twitter Url | URL | Trim | Optional, sparse |

### COMPANY PROFILE
| Apollo Field | Notion Property | Type | Transform | Validation |
|---|---|---|---|---|
| Industry | Industry | Select | As-is | Preserve Apollo industry |
| Keywords | Keywords | Text | Trim, preserve comma-separated | Business descriptors |
| Technologies | Technologies | Text | Trim, preserve comma-separated | Tech stack list |

### COMPANY SIZE
| Apollo Field | Notion Property | Type | Transform | Validation |
|---|---|---|---|---|
| # Employees | # Employees | Number | Parse as integer | Required for Employee Size mapping; affects Lead Score |
| *computed* | Employee Size | Select | Map from # Employees (see rules below) | Auto-generated; used in Lead Score formula |

**Employee Size Mapping Logic:**
```
if # Employees is blank:
  Employee Size = (blank)
else if # Employees <= 10:
  Employee Size = "1–10"
else if # Employees <= 50:
  Employee Size = "11–50"
else if # Employees <= 200:
  Employee Size = "51–200"
else if # Employees <= 500:
  Employee Size = "201–500"
else if # Employees <= 1000:
  Employee Size = "501–1,000"
else if # Employees <= 5000:
  Employee Size = "1,001–5,000"
else:
  Employee Size = "5,001+"
```

**Lead Score Impact:** Company Size weighted 45% in v1.1 Lead Score formula. Larger companies (e.g., "5,001+") receive higher scores, all else equal.

### COMPANY FINANCIAL
| Apollo Field | Notion Property | Type | Transform | Validation |
|---|---|---|---|---|
| Annual Revenue | Annual Revenue | Currency (or Number) | Parse as integer (USD) | Optional; sparse (23.1%) |
| *computed* | Revenue Range | Select | Map from Annual Revenue (see rules below) | Auto-generated |
| Total Funding | Total Funding | Currency (or Number) | Parse as integer (USD) | Optional, sparse |
| Latest Funding | Latest Funding | Text | Trim (funding round type, e.g., "Series B") | Reference info |
| Latest Funding Amount | Latest Funding Amount | Currency (or Number) | Parse as integer (USD) | Optional, sparse |
| Last Raised At | Last Raised At | Date | Parse: "YYYY-MM-DD" | Optional, sparse |

**Revenue Range Mapping Logic:**
```
if Annual Revenue is blank or 0:
  Revenue Range = "Unknown"
else if Annual Revenue < 1,000,000:
  Revenue Range = "<$1M"
else if Annual Revenue < 10,000,000:
  Revenue Range = "$1M–$10M"
else if Annual Revenue < 50,000,000:
  Revenue Range = "$10M–$50M"
else if Annual Revenue < 100,000,000:
  Revenue Range = "$50M–$100M"
else if Annual Revenue < 500,000,000:
  Revenue Range = "$100M–$500M"
else:
  Revenue Range = "$500M+"
```

### COMPANY RELATIONSHIPS
| Apollo Field | Notion Property | Type | Transform | Validation |
|---|---|---|---|---|
| Subsidiary of | Subsidiary of | Text | Trim | Parent company name |
| Subsidiary of (Organization ID) | Subsidiary of (Organization ID) | Text | Trim | Parent Apollo Account Id (optional lookup) |

### COMPANY SYSTEM
| Apollo Field | Notion Property | Type | Transform | Validation |
|---|---|---|---|---|
| Account Owner | Account Owner | Text | Trim | Apollo system field |
| *not in CSV* | Apollo Source | Checkbox | Auto-check = TRUE | Mark as imported from Apollo |

### COMPANY FLAGS
| Apollo Field | Notion Property | Type | Transform | Validation |
|---|---|---|---|---|
| *computed* | Risk Flag | Checkbox | Check if: no Website, no Company Name, invalid Domain | Data quality flag |

---

## 4. DOMAIN EXTRACTION RULES

**Source Field:** Website

**Algorithm:**
```
input: website (e.g., "https://www.google.com/en")

1. if website is blank:
     output: blank
   
2. remove leading/trailing whitespace
   
3. remove "https://" or "http://" prefix if present
   
4. remove "www." if present at start
   
5. take substring up to first "/" (if any)
   
6. convert to lowercase
   
7. output: domain
```

**Examples:**

| Website | Domain |
|---|---|
| `https://www.google.com` | `google.com` |
| `https://www.microsoft.com/en` | `microsoft.com` |
| `www.amazon.com` | `amazon.com` |
| `linkedin.com/company/foo` | `linkedin.com` |
| `(blank)` | `(blank)` |
| `http://site.co.uk` | `site.co.uk` |

---

## 5. RELATION MAPPINGS

### Companies → Contacts (One-to-Many)
**Property Name:** Contacts (on Companies database)
**Related Database:** Contacts
**Link Field:** Company (on Contacts database)
**Cardinality:** 1:N (one company can have many contacts)
**Link Type:** Bidirectional

**Logic:**
```
For each Contact record:
  - Find matching Company by matching Apollo Account Id
  - Set Contact.Company = Company record
  - Companies.Contacts will auto-backlink
```

### Contacts → Company (Many-to-One)
**Property Name:** Company (on Contacts database)
**Related Database:** Companies
**Link Field:** Contacts (on Companies database)
**Cardinality:** N:1 (many contacts belong to one company)
**Link Type:** Bidirectional
**Constraint:** REQUIRED — no contact can exist without a company link

**Validation Rule:**
```
if Contact.Apollo Account Id is blank or not found in Companies database:
  → Log to Exception Log
  → Do NOT create contact
  → Report as orphan
```

### Companies → Intelligence Records (One-to-Many)
**Property Name:** Intelligence Records (on Companies database)
**Related Database:** Sales Intelligence
**Link Field:** Company (on Sales Intelligence database)
**Cardinality:** 1:N
**Link Type:** Bidirectional

**Logic:**
```
For each Company with contacts having research/analysis data:
  - Create Sales Intelligence record if not exists
  - Set Intelligence.Company = Company record
  - Populate from contact-level intelligence
```

### Contacts → Intelligence Records (One-to-Many)
**Property Name:** Intelligence Records (on Contacts database)
**Related Database:** Sales Intelligence
**Link Field:** Contact (on Sales Intelligence database)
**Cardinality:** 1:N
**Link Type:** Bidirectional

**Logic:**
```
For each Contact with research/analysis data:
  - Create or link Sales Intelligence record
  - Set Intelligence.Contact = Contact record
  - Populate from contact-level intelligence fields
```

### Companies → Activities (One-to-Many)
**Property Name:** Activities (on Companies database)
**Related Database:** Outreach/Activities
**Link Field:** Company (on Outreach/Activities database)
**Cardinality:** 1:N
**Link Type:** Bidirectional

### Contacts → Activities (One-to-Many)
**Property Name:** Activities (on Contacts database)
**Related Database:** Outreach/Activities
**Link Field:** Contact (on Outreach/Activities database)
**Cardinality:** 1:N
**Link Type:** Bidirectional

**Logic:**
```
For each Contact with Email Sent = True:
  - Create Activity record
  - Set Activity.Contact = Contact record
  - Set Activity.Company = Contact.Company
  - Populate engagement flags from contact data
```

### Contacts → Tasks (One-to-Many — Phase 2/3)
**Property Name:** Tasks (on Contacts database)
**Related Database:** Tasks
**Link Field:** Contact (on Tasks database)
**Cardinality:** 1:N
**Link Type:** Bidirectional

**Logic:**
```
For each Contact where Action Ready = TRUE:
  - auto_tasks.py creates Task record
  - Set Task.Contact = Contact record
  - Set Task.Company = Contact.Company
  - Set Task.Priority based on Lead Tier (HOT=Critical, WARM=High)
  - Set Task.Due Date based on SLA (HOT=24h, WARM=48h)
  - Set Task.Status = "Not Started"
  - Set Task.Auto Created = TRUE
  - Set Task.Automation Type = "Lead Score Action"
```

---

## 6. DATE PARSING RULES

Apollo exports dates in multiple formats. Parse as follows:

### Accepted Formats
- `YYYY-MM-DD` (e.g., `2024-03-15`)
- `YYYY-MM-DD HH:MM:SS` (e.g., `2024-03-15 14:30:00`)
- `YYYY-MM-DDTHH:MM:SSZ` (ISO 8601, e.g., `2024-03-15T14:30:00Z`)

### Parsing Logic
```
1. Trim whitespace
2. If blank, output blank
3. Try to parse as YYYY-MM-DD first
4. If contains time component, strip to YYYY-MM-DD
5. If fails to parse, log to Exception Log with field name
6. Output: YYYY-MM-DD (Notion format)
```

### Affected Fields
- Primary Email Last Verified At
- Last Contacted
- Last Raised At
- First Contact Attempt (Phase 2/3)

---

## 7. URL VALIDATION RULES

For any URL field (Website, LinkedIn, Facebook, Twitter, Person LinkedIn):

### Validation Logic
```
1. Trim whitespace
2. If blank, output blank
3. If not starting with http:// or https://:
     a. Add "https://" prefix
4. Validate basic URL pattern (presence of domain)
5. If invalid format, log to Exception Log
6. Output: trimmed URL with protocol
```

### Examples
| Input | Output |
|---|---|
| `google.com` | `https://google.com` |
| `https://google.com` | `https://google.com` |
| `http://google.com` | `http://google.com` |
| `(blank)` | `(blank)` |
| `not a url` | (log to Exception Log) |

---

## 8. BOOLEAN/CHECKBOX CONVERSION

Apollo exports boolean values as text: "True" / "False" / blank

### Conversion Logic (Safe Boolean Write — Phase 2/3)
```
if field in engagement_booleans (Email Sent, Replied, etc.):
  # Safe write: only write if Apollo explicitly returns the field
  if value in Apollo response AND value == "True":
    Notion checkbox = ✓ (checked)
  elif field NOT in Apollo response:
    # Don't write anything — preserve manual edits in Notion
    skip field
  else:
    Notion checkbox = (unchecked/blank)
else:
  # Non-engagement booleans (Do Not Call, Auto Created)
  if value == "True":
    Notion checkbox = ✓ (checked)
  else:
    Notion checkbox = (unchecked/blank)
```

### Rationale
Safe Boolean Write prevents overwriting manually-set TRUE values with False from Apollo if a contact hasn't been synced recently. This preserves manual CRM edits.

### Affected Fields
- Email Sent (engagement — safe write)
- Email Opened (engagement — safe write)
- Email Bounced (engagement — safe write)
- Replied (engagement — safe write)
- Demoed (engagement — safe write)
- Meeting Booked (engagement — safe write)
- Do Not Call (non-engagement — normal write)
- Contact Responded (Phase 2/3 — computed from Replied or Meeting Booked)
- Opportunity Created (Phase 2/3 — computed from Stage transitions)
- Auto Created (Phase 2/3, Tasks DB — set by auto_tasks.py)
- Action Ready (Phase 2/3 — computed by action_ready_updater.py)

---

## 9. SELECT/ENUMERATION VALUES

### Email Status (from Email Status field)
**Allowed Values:**
- Verified
- Email No Longer Verified
- New Data Available
- Unavailable
- Extrapolated

**Default:** Blank if missing

### Seniority (from Seniority field with Normalization — Phase 2/3)
**Source:** Apollo Seniority field
**Normalization:** Use SENIORITY_NORMALIZE map from constants.py to unify variants

**Expected Values (post-normalization):**
- C-Suite
- VP
- Director
- Manager
- Specialist
- Individual Contributor
- etc.

**Notes:** Apollo may export "C-Suite", "C suite", "c-suite" variants. Normalize to canonical form.

### Outreach Status (from Outreach Status field — Phase 2/3)
**Allowed Values (block Action Ready if present):**
- Do Not Contact
- Bounced
- Bad Data
- Opted Out
- *Other Apollo values preserved*

**Impact:** Contact with Outreach Status in {Do Not Contact, Bounced, Bad Data} cannot be Action Ready, and no task will be created.

### Stage (from Stage field — Phase 2/3)
**Allowed Values (block Action Ready if certain stages):**
- Lead
- Prospect
- Opportunity
- Customer (blocks Action Ready)
- Churned (blocks Action Ready)
- *Other Apollo values preserved*

**Impact:** Contact with Stage in {Customer, Churned} cannot be Action Ready, and no task will be created.

### Lead Tier (Computed by lead_score.py — Phase 2/3)
**Allowed Values:**
- HOT (Lead Score ≥ 80) — requires immediate call action
- WARM-HIGH (Lead Score 60–79) — high priority follow-up
- WARM (Lead Score 50–59) — nurture sequence
- COLD (Lead Score < 50) — monitor only

**Expected Distribution (calibration targets):**
- HOT: 0.5–2% of total contacts
- WARM-HIGH: 5–15%
- WARM: 10–20%
- COLD: 80%+ (normal for cold Apollo data; not a problem)

**Note:** 80% COLD is expected with cold Apollo outbound data. These are prospects without prior engagement.

### Task Priority (Computed by auto_tasks.py — Phase 2/3)
**Allowed Values:**
- Critical (Lead Tier = HOT)
- High (Lead Tier = WARM-HIGH or WARM)
- Medium (fallback; shouldn't occur)
- Low (fallback; shouldn't occur)

### Task Status (Phase 2/3 Tasks DB)
**Type:** Status (NOT select)
**Allowed Values:**
- Not Started
- In Progress
- Completed

**Write Format:** `{"status": {"name": "Not Started"}}` (NOT select syntax)

### Task Automation Type (Phase 2/3 Tasks DB)
**Type:** Select
**Allowed Values:**
- Lead Score Action (created by auto_tasks.py from Action Ready gate)
- Manual (created by sales team)
- Workflow (future)
- Other

---

## 10. SAFE BOOLEAN WRITE ALGORITHM (Phase 2/3)

**Critical for preserving manual CRM edits:**

```python
def write_engagement_boolean(field_name, apollo_value, notion_current):
    """
    Safely write engagement booleans without overwriting manual edits.
    
    Args:
        field_name: e.g., "Email Sent"
        apollo_value: "True", "False", or None (if field not in Apollo response)
        notion_current: current Notion checkbox state (True/False)
    
    Returns:
        new_value (True/False/None to skip)
    """
    
    # If Apollo didn't return the field, don't write anything
    if apollo_value is None:
        return None  # SKIP — preserve Notion value
    
    # If Apollo returned the field, write it
    if apollo_value == "True":
        return True
    else:
        return False
```

**Use Case:** Contact was manually marked Email Sent = True in Notion. On next sync, Apollo doesn't return Email Sent field for this contact (empty from Apollo). Safe write preserves the manual True in Notion instead of overwriting with False.

---

## 11. SENIORITY NORMALIZATION (Phase 2/3)

**Goal:** Unify Apollo seniority variants into canonical values for consistent scoring and segmentation.

**Map (from constants.py SENIORITY_NORMALIZE):**

```python
SENIORITY_NORMALIZE = {
    # C-Suite variants
    "C-Suite": "C-Suite",
    "C suite": "C-Suite",
    "c-suite": "C-Suite",
    "CEO": "C-Suite",
    "CFO": "C-Suite",
    "CTO": "C-Suite",
    "COO": "C-Suite",
    "President": "C-Suite",
    
    # VP variants
    "VP": "VP",
    "V.P.": "VP",
    "Vice President": "VP",
    
    # Director variants
    "Director": "Director",
    "Director of": "Director",
    
    # Manager variants
    "Manager": "Manager",
    "Senior Manager": "Manager",
    "Group Manager": "Manager",
    
    # Individual Contributor
    "Specialist": "Specialist",
    "Analyst": "Specialist",
    "Engineer": "Specialist",
    "Developer": "Specialist",
    
    # Other
    "Owner": "Owner",
    "Founder": "Founder",
}
```

**Algorithm (in daily_sync.py):**

```python
def _normalize_seniority(raw_seniority):
    """Normalize seniority variant to canonical form"""
    if not raw_seniority:
        return None
    
    cleaned = raw_seniority.strip()
    
    # Direct lookup
    if cleaned in SENIORITY_NORMALIZE:
        return SENIORITY_NORMALIZE[cleaned]
    
    # Prefix match (e.g., "Director of Engineering" → "Director")
    for pattern, canonical in SENIORITY_NORMALIZE.items():
        if cleaned.startswith(pattern):
            return canonical
    
    # No match — return as-is
    return cleaned
```

**Impact on Lead Score:** Seniority weighted 35% in v1.1 Lead Score formula. Normalized values ensure consistent scoring.

---

## 12. EXCEPTION HANDLING

### Exception Log Entry Structure
When any transformation fails, create Exception Log entry:

```
{
  "exception_type": "string",
  "record_id": "Apollo Contact Id or Apollo Account Id",
  "record_name": "Company Name or Full Name",
  "source_field": "field name that failed",
  "source_value": "raw value that failed to parse",
  "expected_format": "description of expected format",
  "error_message": "human-readable error",
  "severity": "High | Medium | Low",
  "created_at": "timestamp",
  "remediation": "suggested fix or notes"
}
```

### Common Exception Types
1. **Missing Primary Key**
   - Apollo Contact Id missing
   - Apollo Account Id missing
2. **Orphan Contact**
   - Contact's Apollo Account Id not found in companies
3. **Invalid Email**
   - Email format doesn't match standard pattern
4. **Invalid URL**
   - Website/LinkedIn URL fails format validation
5. **Duplicate Primary Key**
   - Apollo Contact Id or Apollo Account Id appears twice
6. **Type Conversion Failure**
   - Date field cannot be parsed
   - Number field contains non-numeric value
7. **Missing Required Field**
   - Company Name blank
   - First Name blank
   - Last Name blank
8. **Safe Boolean Conflict** (Phase 2/3)
   - Apollo and Notion disagree on engagement boolean; manual value preserved

---

## 13. DEDUPLICATION RULES

### Company Deduplication
**Key:** Apollo Account Id (primary deduplication key)

```
For each unique Apollo Account Id:
  - Create ONE company record
  - Use first occurrence of each field
  - If subsequent records have different values for same field:
    a. Log to Exception Log as "Inconsistent Company Data"
    b. Use most recent (by Last Contacted or date field) value
```

### Contact Deduplication
**Key:** Apollo Contact Id (primary deduplication key); secondary backup = Email

```
For each unique Apollo Contact Id:
  - Create ONE contact record
  - Do NOT allow duplicates
  - If found, log to Exception Log as "Duplicate Contact"
  - Triple dedup in daily_sync.py: Apollo ID → Email → seen_ids set
```

---

## 14. RICH TEXT FIELD HANDLING

Fields with AI-generated content (Contact Analysis 7680, Conduct targeted research, etc.) should be stored as:

**Notion Property Type:** Text (Rich Text)

**Handling:**
- Preserve original formatting if present
- Do not strip HTML or markdown
- Allow line breaks
- Allow bullet points

---

## 15. COMMA-SEPARATED LIST HANDLING

Fields like Departments, Keywords, Technologies are stored as comma-separated values.

**Storage Strategy:**
- **Option A (Recommended):** Store as single Text field with comma-separated values
  - Easier to import
  - Searchable via text contains
  - Can be split on Notion side if needed

- **Option B (Advanced):** Split into Notion multi-select (requires pre-processing)
  - Requires generating unique select values first
  - More effort upfront
  - Better for filtering/grouping

**Phase 1–3 Strategy:** Use Option A (store as comma-separated text)

---

## 16. LEAD SCORE FORMULA & CALIBRATION (Phase 2/3)

### v1.1 Formula (Current — in use until signals data exists)

```
Score = (Intent × 10%) + (Engagement × 10%) + (Company Size × 45%) + (Seniority × 35%)
```

### Component Scoring

| Component | Max Points | Calculation | Coverage | Rationale |
|-----------|-----------|---|---|---|
| **Intent** | 10 | Intent Score (0–10, from Apollo API) | ~15% of contacts | Sparse; only available when tracked |
| **Engagement** | 10 | Sum of: Email Sent (2), Email Opened (2), Replied (3), Meeting Booked (2), Demoed (1) | ~20% of contacts | Only for previously contacted prospects |
| **Company Size** | 45 | Map Employee Count: 1–10=5, 11–50=10, 51–200=20, 201–500=30, 501–1K=35, 1K–5K=40, 5K+=45 | ~98% of contacts | High coverage, strong proxy for deal value |
| **Seniority** | 35 | Map Seniority: C-Suite=35, VP=30, Director=25, Manager=20, Specialist=10, Other=5 | ~95% of contacts | High coverage, decision-maker proxy |

### Expected Score Distribution (v1.1)

```
HOT (≥80):       0.5–2%    (rare; requires high size + seniority)
WARM-HIGH (60–79): 5–15%    (size + seniority + some engagement)
WARM (50–59):     10–20%    (mid-tier companies, decent seniority)
COLD (<50):       80%+      (small companies or low seniority; normal for cold data)
```

**Important:** 80% COLD is expected for cold Apollo outbound data with no engagement history. This is NOT a bug — it's the baseline for unqualified outbound prospects.

### v2.0 Formula (Future — activate ONLY when signals exist)

```
Score = (Intent × 30%) + (Engagement × 25%) + (Signals × 25%) + (Company Size × 10%) + (Seniority × 10%)
```

**Do NOT activate v2.0 until ALL of these are populated:**
- Job Postings (hiring signals)
- Job Change Detection (recent moves)
- Intent Trend (multi-sync score comparison)

**Why not yet?** Signals are currently empty across the entire database. Weighting empty fields → all contacts score artificially low → system is broken.

### Lead Score Write Strategy

```python
def write_lead_score(contact_id, score_value, lead_tier):
    """
    Write Lead Score (0–100) and Lead Tier (HOT/WARM/COLD) to Notion.
    Both written in single update; both from lead_score.py calculation.
    """
    # Write both fields together
    notion.update_contact({
        'id': contact_id,
        'Lead Score': score_value,  # 0–100
        'Lead Tier': lead_tier       # "HOT" | "WARM-HIGH" | "WARM" | "COLD"
    })
```

---

## 17. ACTION READY GATING (Phase 2/3)

### Five Conditions (ALL must be TRUE)

```
Action Ready = TRUE if:
  (1) Lead Score >= 50
  AND
  (2) Do Not Call = FALSE
  AND
  (3) Outreach Status NOT in {"Do Not Contact", "Bounced", "Bad Data"}
  AND
  (4) Stage NOT in {"Customer", "Churned"}
  AND
  (5) Has at least one contact method (Email is not blank OR Work Direct Phone is not blank)
```

### Blocks for Task Creation

If ANY condition fails, no task is created. Examples:

| Condition | Blocks | Example |
|-----------|--------|---------|
| Score < 50 | COLD tier | Lead Score = 45 → Action Ready = FALSE |
| Do Not Call = TRUE | Marked uncontactable | User manually checked; no outreach |
| Outreach Status = "Bounced" | Bad contact data | Email undeliverable; skip |
| Stage = "Customer" | Already won | Opportunity closed; no need for new tasks |
| No Email + No Phone | Cannot reach | Incomplete contact; mark as risk |

### Write Strategy

```python
def compute_action_ready(contact):
    """
    Evaluate 5 conditions; write Action Ready checkbox.
    Runs AFTER lead_score.py; before auto_tasks.py.
    """
    score = contact.get('Lead Score')
    do_not_call = contact.get('Do Not Call', False)
    outreach_status = contact.get('Outreach Status')
    stage = contact.get('Stage')
    email = contact.get('Email')
    phone = contact.get('Work Direct Phone')
    
    action_ready = (
        score >= 50
        and not do_not_call
        and outreach_status not in ['Do Not Contact', 'Bounced', 'Bad Data']
        and stage not in ['Customer', 'Churned']
        and (email or phone)
    )
    
    return action_ready
```

---

## 18. TASK CREATION FROM ACTION READY (Phase 2/3)

### SLA-Based Task Creation (auto_tasks.py)

```python
def create_task_for_action_ready_contact(contact):
    """
    For each contact where Action Ready = TRUE:
    Create a task with SLA-based due date and priority.
    """
    
    lead_tier = contact['Lead Tier']  # HOT, WARM-HIGH, WARM, COLD
    lead_score = contact['Lead Score']
    
    # Determine priority and SLA
    if lead_tier == 'HOT':
        priority = 'Critical'
        sla_hours = 24
        action_text = 'CALL'
        channel = 'Phone'
    elif lead_tier in ['WARM-HIGH', 'WARM']:
        priority = 'High'
        sla_hours = 48
        action_text = 'FOLLOW-UP'
        channel = 'Email'
    else:
        # COLD — no task created
        return None
    
    # Calculate due date
    due_date = now + timedelta(hours=sla_hours)
    
    # Create task in Notion
    task = {
        'Title': f"{action_text}: {contact['Full Name']} ({contact['Company']})",
        'Contact': contact['Apollo Contact Id'],
        'Company': contact['Company'],
        'Priority': priority,
        'Status': 'Not Started',
        'Due Date': due_date,
        'Channel': channel,
        'Auto Created': True,
        'Automation Type': 'Lead Score Action',
        'Trigger Rule': 'Action Ready = TRUE + Lead Tier >= WARM'
    }
    
    return notion.create_task(task)
```

### Duplicate Prevention

```python
def check_task_exists(contact_id):
    """
    Before creating task, check if contact already has open task.
    Skip if task exists with Status != 'Completed'.
    """
    existing_tasks = notion.query_tasks({
        'filter': {
            'property': 'Contact',
            'relation': {'contains': contact_id}
        }
    })
    
    for task in existing_tasks:
        if task['Status'] != 'Completed':
            return True  # Task exists, skip creation
    
    return False  # No open task, safe to create
```

---

## 19. TRANSFORMATION ALGORITHM PSEUDOCODE

```python
def transform_contact_record(apollo_contact_row, companies_dict):
    """Transform Apollo contact row to Notion contact record"""
    
    contact = {}
    exceptions = []
    
    # Identity
    contact['Apollo Contact Id'] = apollo_contact_row['Apollo Contact Id']
    contact['First Name'] = apollo_contact_row['First Name'].strip()
    contact['Last Name'] = apollo_contact_row['Last Name'].strip()
    contact['Full Name'] = f"{contact['First Name']} {contact['Last Name']}"
    
    # Email
    contact['Email'] = apollo_contact_row.get('Email', '').lower().strip()
    if not contact['Email']:
        contact['Risk Flag'] = True
    
    # Seniority (with normalization)
    raw_seniority = apollo_contact_row.get('Seniority', '')
    contact['Seniority'] = _normalize_seniority(raw_seniority)
    
    # Link to company
    account_id = apollo_contact_row['Apollo Account Id']
    if account_id not in companies_dict:
        exceptions.append({
            'type': 'Orphan Contact',
            'contact_id': contact['Apollo Contact Id'],
            'account_id': account_id
        })
        return None, exceptions  # DO NOT CREATE
    
    contact['Company'] = companies_dict[account_id]
    
    # Engagement booleans (safe write — only if Apollo returns field)
    for field in ['Email Sent', 'Email Opened', 'Replied', 'Demoed', 'Meeting Booked']:
        if field in apollo_contact_row:
            contact[field] = apollo_contact_row[field] == 'True'
        # else: don't write anything (preserve Notion manual edits)
    
    # Dates
    contact['Last Contacted'] = parse_date(apollo_contact_row.get('Last Contacted', ''))
    
    # Outreach status & Stage
    contact['Outreach Status'] = apollo_contact_row.get('Outreach Status', '')
    contact['Stage'] = apollo_contact_row.get('Stage', '')
    contact['Do Not Call'] = apollo_contact_row.get('Do Not Call', '') == 'True'
    
    return contact, exceptions

def transform_company_record(apollo_company_row):
    """Transform Apollo company row to Notion company record"""
    
    company = {}
    
    # Identity
    company['Apollo Account Id'] = apollo_company_row['Apollo Account Id']
    company['Company Name'] = apollo_company_row['Company Name'].strip()
    
    # Website & Domain
    company['Website'] = apollo_company_row['Website'].strip()
    company['Domain'] = extract_domain(company['Website'])
    
    # Size mapping
    emp_count = int(apollo_company_row['# Employees']) if apollo_company_row['# Employees'] else None
    company['# Employees'] = emp_count
    company['Employee Size'] = map_employee_size(emp_count)
    
    # Revenue mapping
    revenue = int(apollo_company_row['Annual Revenue']) if apollo_company_row['Annual Revenue'] else None
    company['Annual Revenue'] = revenue
    company['Revenue Range'] = map_revenue_range(revenue)
    
    # Risk flag
    company['Risk Flag'] = not company['Website'] or not company['Company Name']
    
    return company

def extract_domain(website):
    """Extract domain from website URL"""
    if not website:
        return None
    
    url = website.strip()
    url = url.replace('https://', '').replace('http://', '').replace('www.', '')
    domain = url.split('/')[0].lower()
    return domain if domain else None

def parse_date(date_str):
    """Parse date in multiple formats"""
    if not date_str or not date_str.strip():
        return None
    
    for fmt in ['%Y-%m-%d', '%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%SZ']:
        try:
            parsed = datetime.strptime(date_str.strip(), fmt)
            return parsed.strftime('%Y-%m-%d')
        except ValueError:
            continue
    
    return None

def _normalize_seniority(raw_seniority):
    """Normalize seniority variant to canonical form"""
    if not raw_seniority:
        return None
    
    cleaned = raw_seniority.strip()
    
    if cleaned in SENIORITY_NORMALIZE:
        return SENIORITY_NORMALIZE[cleaned]
    
    for pattern, canonical in SENIORITY_NORMALIZE.items():
        if cleaned.startswith(pattern):
            return canonical
    
    return cleaned
```

---

## 20. FIELD NAME REFERENCE (from constants.py)

All scripts import from constants.py. Field names are defined once as constants:

```python
# Contacts Database Fields
FIELD_APOLLO_CONTACT_ID = "Apollo Contact Id"
FIELD_FIRST_NAME = "First Name"
FIELD_LAST_NAME = "Last Name"
FIELD_EMAIL = "Email"
FIELD_SENIORITY = "Seniority"
FIELD_TITLE = "Title"
FIELD_DEPARTMENTS = "Departments"
FIELD_LEAD_SCORE = "Lead Score"  # Phase 2/3
FIELD_LEAD_TIER = "Lead Tier"  # Phase 2/3
FIELD_ACTION_READY = "Action Ready"  # Phase 2/3
FIELD_INTENT_SCORE = "Intent Score"
FIELD_EMAIL_SENT = "Email Sent"
FIELD_EMAIL_OPENED = "Email Opened"
FIELD_EMAIL_BOUNCED = "Email Bounced"
FIELD_REPLIED = "Replied"
FIELD_DEMOED = "Demoed"
FIELD_MEETING_BOOKED = "Meeting Booked"
FIELD_LAST_CONTACTED = "Last Contacted"
FIELD_DO_NOT_CALL = "Do Not Call"
FIELD_OUTREACH_STATUS = "Outreach Status"
FIELD_STAGE = "Stage"
FIELD_CONTACT_RESPONDED = "Contact Responded"  # Phase 2/3
FIELD_FIRST_CONTACT_ATTEMPT = "First Contact Attempt"  # Phase 2/3
FIELD_OPPORTUNITY_CREATED = "Opportunity Created"  # Phase 2/3

# Companies Database Fields
FIELD_APOLLO_ACCOUNT_ID = "Apollo Account Id"
FIELD_COMPANY_NAME = "Company Name"
FIELD_DOMAIN = "Domain"
FIELD_INDUSTRY = "Industry"
FIELD_EMPLOYEE_COUNT = "# Employees"
FIELD_EMPLOYEE_SIZE = "Employee Size"
FIELD_ANNUAL_REVENUE = "Annual Revenue"
FIELD_REVENUE_RANGE = "Revenue Range"

# Tasks Database Fields (Phase 2/3)
FIELD_TASK_TITLE = "Task Title"
FIELD_TASK_PRIORITY = "Priority"
FIELD_TASK_STATUS = "Status"  # Status type, not select
FIELD_TASK_DUE_DATE = "Due Date"
FIELD_TASK_CONTACT = "Contact"  # Relation
FIELD_TASK_COMPANY = "Company"  # Relation
FIELD_TASK_AUTO_CREATED = "Auto Created"  # Checkbox
FIELD_TASK_AUTOMATION_TYPE = "Automation Type"  # Select
FIELD_TASK_TRIGGER_RULE = "Trigger Rule"  # Text
```

**Golden Rule:** Never hardcode field names. Always import from constants.py.

---

## 21. VALIDATION CHECKLIST FOR EACH BATCH

Before importing each batch, verify:

- [ ] All required fields present (First Name, Last Name, Apollo Contact Id, Company Name, Apollo Account Id)
- [ ] No duplicate Apollo Contact Ids in batch
- [ ] No duplicate Apollo Account Ids per company
- [ ] All dates parse correctly
- [ ] All URLs have proper format
- [ ] All employee counts are numeric
- [ ] All revenue amounts are numeric
- [ ] All Email Status values match allowed list
- [ ] All Stage values are non-empty
- [ ] All email addresses (if present) match email format
- [ ] All company links resolve to valid companies
- [ ] Domain extraction logic works (sample check)
- [ ] Employee Size mapping logic works (sample check)
- [ ] Revenue Range mapping logic works (sample check)
- [ ] Seniority normalization works (sample check) — Phase 2/3
- [ ] Lead Score calculation correct (v1.1 weights) — Phase 2/3
- [ ] Action Ready gating correct (5 conditions) — Phase 2/3
- [ ] Safe boolean writes working (only write if Apollo returns) — Phase 2/3
- [ ] Exception count is reasonable (<1% of batch)

---

**End of Field Mapping Document — Version 3.2**

**Updated for:** Phase 2/3 (Lead Scoring, Lead Tier, Action Ready, Auto Tasks, Safe Boolean Writes, Seniority Normalization)

**Checked:** March 27, 2026