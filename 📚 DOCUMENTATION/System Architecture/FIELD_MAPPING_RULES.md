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
    
    Returns