---
name: notion-schema-manager
description: "Manage Notion database schema, properties, relations, and views for AI Sales OS. Use this skill when the user asks about Notion database structure, wants to add/modify/remove properties, fix field types, check what fields exist, understand database relations, create views, or troubleshoot schema issues. Also trigger when someone asks about field names, property types, or 'what fields does the contacts/companies/tasks database have?'"
---

# Notion Schema Manager — AI Sales OS

You manage the Notion database structure for AI Sales OS. The schema is the foundation — every script, every automation, and every view depends on correct property names and types.

## Database Overview

AI Sales OS uses 7 Notion databases. The three core operational ones are:

### Contacts Database
The main working database. 44,875+ records.

**Title field:** `Full Name`

**Key properties (confirmed by API):**

| Property | Type | Notes |
|----------|------|-------|
| Full Name | title | |
| First Name, Last Name | rich_text | |
| Email | email | |
| Email Status | select | Valid/Invalid/etc. |
| Title | rich_text | Job title |
| Seniority | select | C-Suite, VP, Director, Manager, etc. — NOTE: both "C-Suite" and "C suite" exist |
| Departments | rich_text | Comma-separated from Apollo list |
| City, State, Country | rich_text | |
| Person Linkedin Url | url | |
| Work Direct Phone, Mobile Phone, Home Phone, Corporate Phone, Other Phone | phone_number | |
| Lead Score | number | 0-100, written by lead_score.py |
| Lead Tier | select | HOT / WARM / COLD |
| Action Ready | checkbox | Computed by action_ready_updater.py |
| Primary Intent Score, Secondary Intent Score | number | Currently empty (Apollo plan) |
| Stage | select | Lead/Prospect/Engaged/Customer/Churned — largely empty |
| Outreach Status | select | Sent/Opened/Replied/Meeting Booked/Do Not Contact/Bounced |
| Qualification Status | select | Qualified/In Progress/etc. |
| Reply Status | select | Positive/Neutral/Negative |
| Do Not Call | checkbox | |
| Email Sent, Email Opened, Email Bounced, Replied, Meeting Booked, Demoed | checkbox | Safe-written only when Apollo returns value |
| Last Contacted | date | |
| Contact Responded | checkbox | Feedback loop tracking |
| Opportunity Created | checkbox | Revenue tracking |
| First Contact Attempt | date | Lifecycle tracking |
| Apollo Contact Id, Apollo Account Id | rich_text | Primary key and company link |
| Company | relation | Links to Companies DB |
| Company Name for Emails | rich_text | From Apollo organization_name |
| Record Source | select | Apollo |
| Data Status | select | Raw |

### Companies Database
15,407+ records.

**Title field:** `Company Name`

**Key properties:**

| Property | Type |
|----------|------|
| Company Name | title |
| Domain | rich_text |
| Website | url |
| Industry | rich_text |
| Employees | number |
| Employee Size | rich_text |
| Annual Revenue | number |
| Revenue Range | rich_text |
| Total Funding, Latest Funding Amount | number |
| Last Raised At | date |
| Company City, State, Country, Address | rich_text |
| Company Phone | phone_number |
| Company Linkedin Url, Facebook Url, Twitter Url | url |
| Keywords, Technologies | rich_text |
| Short Description | rich_text |
| Account Stage | select |
| Apollo Account Id | rich_text |

### Tasks Database
Purpose: Action Engine output. Auto-created tasks for sales follow-up.

**Title field:** `Task Title`

**IMPORTANT:** Status field is `status` type, NOT `select`. Use `{"status": {"name": "Not Started"}}`.

| Property | Type | Notes |
|----------|------|-------|
| Task Title | title | |
| Priority | select | Critical / High / Medium / Low |
| Status | **status** | Not Started / In Progress / Completed |
| Due Date, Start Date | date | |
| Task Type | select | Follow-up / Demo / Proposal / Review / Other |
| Team | select | |
| Contact | relation | Links to Contacts |
| Company | relation | Links to Companies |
| Opportunity | relation | Links to Opportunities |
| Context | rich_text | Why this task was created |
| Description | rich_text | |
| Expected Outcome | rich_text | |
| Auto Created | checkbox | True for automation-generated tasks |
| Automation Type | select | Lead Scoring |
| Trigger Rule | rich_text | e.g., "Score >= 80 AND Action Ready = True" |
| Completed At | date | |

## Property Naming Convention

All property names are defined in `constants.py`. When adding new properties:
1. Add the constant to `constants.py` first
2. Use the exact Notion property name as the string value
3. Import from constants in any script that uses it

Example: `FIELD_LEAD_SCORE = "Lead Score"` — every script imports this instead of hardcoding the string.

## Relations Map

```
Contacts ←→ Companies (via Company / Contacts relation)
Contacts ←→ Tasks (via Contact relation)
Companies ←→ Tasks (via Company relation)
Tasks ←→ Opportunities (via Opportunity relation)
```

## Views That Exist

- `🔴 HOT LEADS (80+)` — Contacts filtered by Lead Score >= 80
- `🟡 WARM LEADS (50-79)` — Contacts filtered by Lead Score 50-79
- `🟢 COLD LEADS (<50)` — Contacts filtered by Lead Score < 50

## When Modifying Schema

1. Check if the property already exists before adding (duplicates cause silent bugs)
2. Verify the property type matches what the code expects
3. Update `constants.py` with any new field name
4. Test with a single record before bulk operations
5. Document the change

Always follow the shared rules in `shared-sales-os-rules`.
