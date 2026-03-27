# 🚀 PHASE 2: DATA IMPORT - QUICK START GUIDE

**Status:** Ready to Begin (March 25, 2026)
**Duration:** 1-2 Days
**Objective:** Import 9,504 records into Notion

---

## 📋 CHECKLIST: BEFORE YOU START

- ✅ All 5 Notion databases created
- ✅ All relationships configured
- ✅ All views tested
- ⏳ CSV files prepared
- ⏳ Data mapping verified
- ⏳ Import process defined

---

## 🎯 PHASE 2 OBJECTIVES

### Objective 1: Prepare CSV Files
```
├─ Companies.csv (3,606 records)
├─ Contacts.csv (5,898 records)
└─ Data quality check
```

### Objective 2: Map Fields to Notion
```
Apollo Fields → Notion Fields
├─ Company Name → Name
├─ Account ID → Apollo Account ID
├─ Domain → Domain
└─ ... (full mapping)
```

### Objective 3: Import Data to Notion
```
1. Upload Companies CSV
2. Upload Contacts CSV
3. Verify record counts
4. Check relationships
5. Run QA tests
```

---

## 📊 DATA PREPARATION TASKS

### Task 1: Export from Apollo

**Export Companies:**
```
Format: CSV
Fields:
  - Company Name
  - Apollo Account ID
  - Domain
  - Industry
  - Company Size
  - Employee Count
  - Revenue Range
  - HQ Location
  - Website
  - Phone
  - Funding Stage
  - Funding Amount
  - Funding Date
  - Created Date
```

**Export Contacts:**
```
Format: CSV
Fields:
  - Full Name
  - First Name
  - Last Name
  - Apollo Contact ID
  - Email
  - Direct Phone
  - Mobile Phone
  - Title
  - Seniority
  - Department
  - Company Name
  - Company Domain
  - Company Apollo ID
  - Created Date
```

### Task 2: Clean Data

```python
Validation Checks:
☐ No duplicate Apollo IDs
☐ All required fields present
☐ Valid email formats
☐ No empty company names
☐ Consistent phone formats
☐ Date formats YYYY-MM-DD
☐ Domain names valid
☐ CSV encoding UTF-8
```

### Task 3: Import to Notion

**Companies First:**
```
1. Go to Companies database
2. Click: ... → Import
3. Select: Companies.csv
4. Map fields:
   - Name → Name
   - Apollo Account ID → Apollo Account ID
   - Domain → Domain
   - etc...
5. Review preview
6. Click: Import
7. Wait for completion
8. Verify: 3,606 records imported
```

**Then Contacts:**
```
1. Go to Contacts database
2. Click: ... → Import
3. Select: Contacts.csv
4. Map fields:
   - Full Name → Full Name
   - Apollo Contact ID → Apollo Contact ID
   - Email → Email
   - Company Name → (need to link by domain)
   - etc...
5. Review preview
6. Click: Import
7. Wait for completion
8. Verify: 5,898 records imported
```

---

## 🔗 LINKING CONTACTS TO COMPANIES

**After Import Complete:**

### Option 1: Automatic by Domain (Recommended)

```javascript
// Use Notion's relation API
For each Contact:
  1. Get company_domain from CSV
  2. Find Companies.domain = company_domain
  3. Set Contacts.Company = Companies record
  4. Done!
```

**Formula to verify links:**
```
In Contacts: IF(Company="", "❌ Missing Link", "✅ Linked")
Filter: Missing Link = Unlinked contacts
```

### Option 2: Manual Linking (if automatic fails)

```
1. Go to: Contacts database
2. Filter: Company is empty
3. For each contact:
   a. Click: Company field
   b. Search: Company name
   c. Click: Select
4. Done!
```

---

## ✅ VERIFICATION STEPS

### After Companies Import

```
☐ 3,606 records in Companies database
☐ All company names present
☐ All domains present
☐ No duplicate Apollo IDs
☐ All views load correctly
☐ "All Companies" view shows 3,606
☐ "High Intent" view works
☐ "By Industry" view groups correctly
```

### After Contacts Import

```
☐ 5,898 records in Contacts database
☐ All names present
☐ All emails present
☐ No duplicate Apollo Contact IDs
☐ All views load correctly
☐ "All Contacts" view shows 5,898
☐ "HOT LEADS" view (should be empty initially)
☐ "By Company" view groups correctly
```

### After Linking Companies

```
☐ All contacts linked to companies
  Count: Contacts with Company field filled = 5,898
☐ No orphaned contacts
  Count: Contacts with Company = empty = 0
☐ One-to-many relationships work
  Test: Click Contact → Company → Opens company record
☐ Reverse relationships work
  Test: Go to Company → View Contacts in relation view
```

---

## 🚨 TROUBLESHOOTING

### Problem: Contacts Not Linking to Companies

**Solution 1:**
```
1. Check domain spelling consistency
2. Export: Companies domain list
3. Compare: Contacts company_domain
4. Fix mismatches (case sensitivity, spaces)
5. Re-import with corrected domains
```

**Solution 2:**
```
1. Use Notion API to create relations
2. Filter by domain match
3. Run linking script
4. Verify all linked
```

### Problem: Duplicate Records

**Solution:**
```
1. In view: Filter by Apollo ID
2. Find duplicates: Apollo ID appears 2+ times
3. Delete duplicates (keep newest)
4. Re-import from source
```

### Problem: Missing Fields

**Solution:**
```
1. Check CSV has all columns
2. Verify mapping during import
3. Add missing data to CSV
4. Re-import with complete data
```

---

## 📈 EXPECTED RESULTS

**After Complete Phase 2:**

```
System State:
├─ Companies: 3,606 ✅
├─ Contacts: 5,898 ✅
├─ All Relations: Active ✅
├─ All Views: Working ✅
└─ Data Integrity: 100% ✅

Sample Metrics:
├─ Contacts per Company: Avg 1.6
├─ Companies with 10+ Contacts: 200+
├─ Contacts with Email: 5,898 (100%)
├─ Companies with Domain: 3,606 (100%)
└─ Data Completeness: 95%+
```

---

## 🎯 SUCCESS CRITERIA

### Phase 2 Complete When:

- ✅ All 3,606 companies imported to Notion
- ✅ All 5,898 contacts imported to Notion
- ✅ All contacts linked to companies (100%)
- ✅ No duplicate records
- ✅ All views working
- ✅ All relationships functional
- ✅ Data passed QA checks
- ✅ User can navigate: Contact → Company → back

---

## 📅 TIMELINE

```
Day 1 (4 hours):
├─ Export data from Apollo (30 min)
├─ Clean & validate data (1 hour)
├─ Create CSV files (30 min)
├─ Import Companies to Notion (1 hour)
└─ Verify imports (1 hour)

Day 2 (3 hours):
├─ Import Contacts to Notion (1 hour)
├─ Link Contacts to Companies (1 hour)
└─ Run QA & verification (1 hour)
```

---

## 🔧 TOOLS NEEDED

- Notion account
- Apollo account (for export)
- CSV editor (Excel, Google Sheets)
- Python (optional, for linking script)

---

## 📞 SUPPORT

- **Questions?** Check NOTION_SETUP_MANUAL_GUIDE.md
- **Need help?** Use NOTION_SETUP_TRACKER.xlsx
- **Validation?** Run notion_setup_validator.py

---

**Next Phase:** Phase 3: Apollo Webhook Integration
**Estimated Start:** March 26, 2026

**Ready to begin? Start with Task 1: Export from Apollo!** 🚀
