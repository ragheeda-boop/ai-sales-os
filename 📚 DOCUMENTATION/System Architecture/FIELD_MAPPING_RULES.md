# FIELD MAPPING & TRANSFORMATION RULES — PHASE 1

## 1. MAPPING OVERVIEW

This document defines exactly how each Apollo CSV field maps to Notion properties, including data type conversions, validation rules, and transformation logic.

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
| Seniority | Seniority | Select | As-is | Preserve Apollo values |
| Departments | Departments | Text | Trim | Comma-separated |
| Sub Departments | Sub Departments | Text | Trim | Comma-separated |
| Person Linkedin Url | Person Linkedin Url | URL | Trim | Optional, validate URL format |

### CONTACT ENGAGEMENT SIGNALS
| Apollo Field | Notion Property | Type | Transform | Validation |
|---|---|---|---|---|
| Email Sent | Email Sent | Checkbox | "True" → ✓, else empty | Email outreach flag |
| Email Open | Email Open | Checkbox | "True" → ✓, else empty | Email engagement flag |
| Email Bounced | Email Bounced | Checkbox | "True" → ✓, else empty | Email quality flag |
| Replied | Replied | Checkbox | "True" → ✓, else empty | Positive engagement |
| Demoed | Demoed | Checkbox | "True" → ✓, else empty | Sales stage signal |
| Last Contacted | Last Contacted | Date | Parse: "YYYY-MM-DD" or "YYYY-MM-DD HH:MM:SS" | Track engagement timeline |

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

### CONTACT INTENT (PHASE 2 — NOT IN CSV)
| Apollo Field | Notion Property | Type | Transform | Validation |
|---|---|---|---|---|
| *N/A — not in CSV* | Primary Intent Topic | Select | Fetch from Apollo API Phase 2 | **Leave blank in Phase 1** |
| *N/A — not in CSV* | Primary Intent Score | Number | Fetch from Apollo API Phase 2 | **Leave blank in Phase 1** |
| *N/A — not in CSV* | Secondary Intent Topic | Select | Fetch from Apollo API Phase 2 | **Leave blank in Phase 1** |
| *N/A — not in CSV* | Secondary Intent Score | Number | Fetch from Apollo API Phase 2 | **Leave blank in Phase 1** |

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
| # Employees | # Employees | Number | Parse as integer | Required for Employee Size mapping |
| *computed* | Employee Size | Select | Map from # Employees (see rules below) | Auto-generated |

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

### Conversion Logic
```
if value == "True":
  Notion checkbox = ✓ (checked)
else:
  Notion checkbox = (unchecked/blank)
```

### Affected Fields
- Email Sent
- Email Open
- Email Bounced
- Replied
- Demoed

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

### Seniority (from Seniority field)
**Preserve as-is from Apollo export**
Expected values: C-level, VP, Director, Manager, Specialist, etc.

### Stage (from Stage field)
**Preserve as-is from Apollo export**
Expected values: Lead, Prospect, Customer, etc.

### Industry (from Industry field)
**Preserve as-is from Apollo export**
Expected values: Technology, Healthcare, Finance, etc.

### Employee Size (Computed)
**Allowed Values:**
- 1–10
- 11–50
- 51–200
- 201–500
- 501–1,000
- 1,001–5,000
- 5,001+

### Revenue Range (Computed)
**Allowed Values:**
- Unknown
- <$1M
- $1M–$10M
- $10M–$50M
- $50M–$100M
- $100M–$500M
- $500M+

---

## 10. EXCEPTION HANDLING

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

---

## 11. DEDUPLICATION RULES

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
**Key:** Apollo Contact Id (primary deduplication key)

```
For each unique Apollo Contact Id:
  - Create ONE contact record
  - Do NOT allow duplicates
  - If found, log to Exception Log as "Duplicate Contact"
```

---

## 12. RICH TEXT FIELD HANDLING

Fields with AI-generated content (Contact Analysis 7680, Conduct targeted research, etc.) should be stored as:

**Notion Property Type:** Text (Rich Text)

**Handling:**
- Preserve original formatting if present
- Do not strip HTML or markdown
- Allow line breaks
- Allow bullet points

---

## 13. COMMA-SEPARATED LIST HANDLING

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

**Phase 1 Strategy:** Use Option A (store as comma-separated text)

---

## 14. TRANSFORMATION ALGORITHM PSEUDOCODE

```python
def transform_contact_record(apollo_contact_row, companies_dict):
    """Transform Apollo CSV contact row to Notion contact record"""
    
    contact = {}
    exceptions = []
    
    # Identity
    contact['Apollo Contact Id'] = apollo_contact_row['Apollo Contact Id']
    contact['First Name'] = apollo_contact_row['First Name'].strip()
    contact['Last Name'] = apollo_contact_row['Last Name'].strip()
    contact['Full Name'] = f"{contact['First Name']} {contact['Last Name']}"
    
    # Email
    contact['Email'] = apollo_contact_row['Email'].lower().strip()
    if not contact['Email']:
        contact['Risk Flag'] = True
    
    contact['Email Status'] = apollo_contact_row['Email Status']
    contact['Primary Email Source'] = apollo_contact_row['Primary Email Source']
    # ... etc for all email fields
    
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
    
    # Boolean fields
    contact['Email Sent'] = apollo_contact_row['Email Sent'] == 'True'
    contact['Email Open'] = apollo_contact_row['Email Open'] == 'True'
    # ... etc
    
    # Dates
    contact['Last Contacted'] = parse_date(apollo_contact_row['Last Contacted'])
    
    return contact, exceptions

def transform_company_record(apollo_company_row):
    """Transform Apollo CSV company row to Notion company record"""
    
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
    
    # Try parsing different formats
    for fmt in ['%Y-%m-%d', '%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%SZ']:
        try:
            parsed = datetime.strptime(date_str.strip(), fmt)
            return parsed.strftime('%Y-%m-%d')
        except ValueError:
            continue
    
    return None  # Failed to parse
```

---

## 15. VALIDATION CHECKLIST FOR EACH BATCH

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
- [ ] Exception count is reasonable (<1% of batch)

---

**End of Field Mapping Document**

**Ready for Phase 1 Validation Batch Execution**
