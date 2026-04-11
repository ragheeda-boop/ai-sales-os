# 🚀 PHASE 1B LAUNCH CHECKLIST
## Import & Link Execution (7 Days)

**Project:** AI Sales OS
**Phase:** 1B (Import & Linking)
**Duration:** 5-7 working days
**Status:** ✅ READY TO LAUNCH
**Date Prepared:** March 24, 2026

---

## 📊 CRITICAL NUMBERS

| Metric | Target | Status |
|--------|--------|--------|
| Companies to Import | 3,606 | ✅ Ready |
| Contacts to Import | 5,898 | ✅ Ready |
| Target Link Success | 100% | 🎯 Critical |
| Target Data Quality | A+ | 🎯 Critical |
| Test Records (Sample) | 100 | ✅ Ready |
| Estimated Time | 9 hours total | ⏱️ 7 days |

---

## 🎯 PRE-LAUNCH VERIFICATION

### Environment Checklist
- [ ] Notion workspace access confirmed (all team members)
- [ ] Companies database created or accessible
- [ ] Contacts database created or accessible
- [ ] API credentials stored securely
- [ ] Team trained on import process
- [ ] Backup of existing Notion data taken
- [ ] Network connectivity verified
- [ ] All import files verified in 01_DATA_IMPORT/

### File Verification
```bash
✅ IMPORT_companies_FINAL.csv    (6.4M - 3,606 records)
✅ IMPORT_contacts_FINAL.csv     (4.2M - 5,898 records)
✅ sample_100_records.json       (878K - 100 test records)
✅ notion_companies.json         (7.9M - JSON format)
✅ notion_contacts.json          (41M - JSON format)
✅ link_companies_contacts.py    (automation script)
```

### Team Assignments
| Role | Person | Hours | Approval |
|------|--------|-------|----------|
| RevOps Lead (Import) | [NAME] | 4h | ☐ |
| Data Engineer (Linking) | [NAME] | 2h | ☐ |
| QA Lead (Validation) | [NAME] | 3h | ☐ |
| Project Lead (Oversight) | [NAME] | 2h | ☐ |

---

## 📅 EXECUTION TIMELINE

### **DAY 1: TEST IMPORT (2 hours)**

**Goal:** Verify import process works with 100 test records

**Owner:** RevOps Lead
**Estimated Time:** 2 hours
**Go/No-Go Decision Required:** YES

#### Step 1.1: Prepare Test Environment
```
☐ Open Notion workspace
☐ Navigate to Companies database
☐ Confirm database is empty or ready for test
☐ Locate "Import" button
☐ Select "JSON import" option
```

#### Step 1.2: Import Test Data
```
☐ File: 01_DATA_IMPORT/sample_100_records.json
☐ Click "Upload file"
☐ Review import preview (should show ~100 records)
☐ Confirm field mapping looks correct
☐ Click "Import"
☐ Wait for completion (typically <5 minutes)
☐ Check Notion notifications for completion message
```

#### Step 1.3: Validate Test Results
```
☐ Companies count: Verify 100 records added
☐ Contacts count: Verify ~180 contacts linked
☐ Required fields: Company Name, Domain, Apollo ID populated
☐ Email coverage: Check >90% have email
☐ Relationships: Sample check that contacts link to companies
☐ No errors: Check Notion activity log for errors
```

#### Step 1.4: Test Navigation & Filters
```
☐ Try searching for a company by name (should work)
☐ Try filtering by Industry (should work)
☐ Try sorting by Company Size (should work)
☐ Click on a contact → verify company shows
☐ Click on a company → verify contacts show
```

#### Step 1.5: Go/No-Go Decision
```
✅ GO: All 100 records imported + validated
❌ NO-GO: >1% error rate OR missing critical fields

Decision: ☐ GO | ☐ NO-GO (requires troubleshooting)
```

---

### **DAY 2-3: FULL DATA IMPORT (4 hours)**

**Goal:** Import all 3,606 companies + 5,898 contacts

**Owner:** RevOps Lead
**Estimated Time:** 4 hours total
**Parallel Imports:** YES (can run both simultaneously)

#### Step 2.1: Import Companies Data
```
Timeline: ~1 hour import + 30 min validation

☐ Open Notion → Companies database
☐ Click "Import" button
☐ Select "CSV import"
☐ Upload file: IMPORT_companies_FINAL.csv
☐ Review field mapping (should auto-detect):
  ├─ Company Name → Name
  ├─ Domain → Domain
  ├─ Apollo Account ID → Apollo_ID (PK)
  ├─ Industry → Industry
  ├─ Company Size → Company_Size
  └─ [verify all fields present]
☐ Click "Import" → confirm 3,606 records
☐ **IMPORTANT:** Do NOT close Notion until import completes
☐ Monitor Notion notifications for completion
```

#### Step 2.2: Import Contacts Data (can start immediately after companies)
```
Timeline: ~1 hour import + 30 min validation

☐ Open Notion → Contacts database (new tab)
☐ Click "Import" button
☐ Select "CSV import"
☐ Upload file: IMPORT_contacts_FINAL.csv
☐ Review field mapping (should auto-detect):
  ├─ Contact Name → Name
  ├─ Email → Email
  ├─ Title → Title
  ├─ Seniority → Seniority
  ├─ Apollo Contact ID → Apollo_ID (PK)
  ├─ Company Domain → Company_Domain
  └─ [verify all fields present]
☐ Click "Import" → confirm 5,898 records
☐ Monitor Notion notifications for completion
```

#### Step 2.3: Post-Import Validation (while imports run)
```
☐ Open 03_SETUP/linking_log.json (from previous test)
☐ Prepare SQL/Python script for linking (next step)
☐ Brief team on linking automation (coming Day 4)
☐ Check company names for obvious duplicates (spot check 10)
☐ Verify no email addresses have weird characters (spot check 10)
```

---

### **DAY 4: LINKING AUTOMATION (2 hours)**

**Goal:** Auto-link all 5,898 contacts to companies (100% success)

**Owner:** Data Engineer
**Estimated Time:** 2 hours
**Risk Level:** LOW (script tested)
**Validation Required:** YES

#### Step 3.1: Prepare for Linking
```
☐ Verify all companies imported (should see 3,606 in Notion)
☐ Verify all contacts imported (should see 5,898 in Notion)
☐ Open Terminal / PowerShell
☐ Navigate to: cd /path/to/03_SETUP/
☐ Verify Python 3.8+ installed: python --version
☐ Verify Notion API credentials ready (if script requires)
```

#### Step 3.2: Run Linking Script
```
Command: python link_companies_contacts.py

☐ Script starts → monitor console output
☐ Expected output format:
  ├─ "Linking companies and contacts..."
  ├─ "Processing batch 1/50..."
  ├─ "Success: 5,898 / 5,898 linked"
  └─ "Errors: 0"
☐ **CRITICAL:** If errors > 0, STOP and investigate
☐ Wait for completion message
☐ Check file: linking_log.json created/updated
```

#### Step 3.3: Validate Linking Results
```
Open linking_log.json in text editor:

☐ "total_contacts": 5,898
☐ "linked_count": 5,898
☐ "error_count": 0
☐ "success_rate": 100%
☐ Review error array (should be empty [])
☐ Sample check: Random 5 contacts verify company_id populated
```

#### Step 3.4: Verify Links in Notion
```
In Notion → Contacts database:

☐ Open random contact record
☐ Check "Company" field is populated
☐ Click company link → should open company record
☐ Click back → confirm relationship bidirectional
☐ Repeat check for 5 different contacts
☐ No orphaned contacts (all should have company)
```

---

### **DAY 5: QUALITY ASSURANCE VALIDATION (3 hours)**

**Goal:** Verify data quality meets A+ standard

**Owner:** QA Lead
**Estimated Time:** 3 hours
**Success Criteria:** Must achieve A+ grade before sign-off

#### Step 4.1: Data Completeness Check
```
Required Fields Audit:

COMPANIES (3,606 total):
☐ Apollo ID: 100% populated
☐ Company Name: 100% populated
☐ Domain: 100% populated
☐ Industry: ≥95% populated
☐ Company Size: ≥90% populated
☐ Contact relationships: 100% mapped

CONTACTS (5,898 total):
☐ Apollo ID: 100% populated
☐ First Name: 100% populated
☐ Email: ≥95.7% populated
☐ Title: ≥85% populated
☐ Seniority: ≥80% populated
☐ Company relationships: 100% linked
```

#### Step 4.2: Data Quality Checks
```
Random Sampling (check 50 records):

Email Format:
☐ All emails match format: user@domain.com
☐ No obvious typos or test emails
☐ No duplicate emails in sample

Company Relationships:
☐ Each contact has exactly 1 company
☐ No orphaned contacts
☐ No multi-company assignments

Domain Matching:
☐ Contact email domain matches company domain (95%+)
☐ Sample 10 mismatches are legitimate (name changes, etc)
```

#### Step 4.3: Deduplication Verification
```
Uniqueness Check:

☐ Count distinct Apollo IDs in companies: should = 3,606
☐ Count distinct Apollo IDs in contacts: should = 5,898
☐ Count duplicate email addresses: should = 0
☐ Count duplicate company domains: should = 0 (or explain)
```

#### Step 4.4: Data Integrity Checks
```
System Relationships:

☐ All companies have ≥1 associated contact
☐ No company with >500 contacts (data sanity check)
☐ Filter by industry → results look reasonable
☐ Filter by company size → results look reasonable
☐ Search function works for all fields
☐ Export test: Can export 100 records to CSV
```

#### Step 4.5: Quality Grade Assignment
```
Scoring Rubric:

A+ (95-100%): All checks pass, <5 issues found
A  (85-94%):  1-2 fields <90%, fixable issues
B  (75-84%):  Multiple fields <85%, needs review
C  (<75%):    STOP - requires re-import

Current Status: ☐ A+ | ☐ A | ☐ B | ☐ C

Sign-off:
Quality Approved By: _________________ Date: _______
```

---

### **DAY 6-7: DOCUMENTATION & SIGN-OFF (2 hours)**

**Goal:** Complete final sign-offs and prepare for Phase 2

**Owner:** Project Lead
**Estimated Time:** 2 hours

#### Step 5.1: Generate Final Reports
```
☐ Export linking_log.json for records
☐ Export QA validation checklist (completed)
☐ Capture Notion screenshots of:
  ├─ Companies database (first 10 records)
  ├─ Contacts database (first 10 records)
  └─ Sample linked relationship
☐ Create summary statistics:
  ├─ Total companies imported: 3,606
  ├─ Total contacts imported: 5,898
  ├─ Link success rate: 100%
  ├─ Data quality grade: A+
  └─ Time spent: [hours]
```

#### Step 5.2: Team Sign-Off
```
Complete and collect approvals:

REVOPS LEAD (Import):
Name: _________________ Date: _______ Signature: _______
Confirms: All data imported per plan

DATA ENGINEER (Linking):
Name: _________________ Date: _______ Signature: _______
Confirms: All 5,898 contacts linked (100%)

QA LEAD (Validation):
Name: _________________ Date: _______ Signature: _______
Confirms: Data quality grade: A+

PROJECT LEAD (Overall):
Name: _________________ Date: _______ Signature: _______
Confirms: Phase 1B COMPLETE - Ready for Phase 2
```

#### Step 5.3: Archive & Document
```
☐ Save all validation logs to: 02_DOCUMENTATION/
☐ Update this checklist with actual completion dates
☐ Move linking_log.json to: 03_SETUP/archive/
☐ Create Phase 1B completion summary
☐ Schedule kickoff for Phase 2 (Apollo Integration)
```

---

## ⚠️ RISK MITIGATION & TROUBLESHOOTING

### Import Failures

**Issue:** CSV import shows <100% completion
```
Actions:
☐ Check file encoding (should be UTF-8)
☐ Verify file not corrupted (redownload if needed)
☐ Check for special characters in required fields
☐ Retry import after 5 minutes
☐ If persists: Contact Notion support with error message
```

**Issue:** Field mapping incorrect
```
Actions:
☐ Cancel import (don't proceed)
☐ Verify CSV headers match expected fields
☐ Manually map fields in Notion import preview
☐ Check 02_DOCUMENTATION/FIELD_MAPPING_RULES.md
☐ Retry with manual mapping
```

### Linking Failures

**Issue:** Script returns "error_count > 0"
```
Actions:
☐ Open linking_log.json
☐ Review error array for details
☐ Check if all companies were imported first
☐ Verify company domains populated in Notion
☐ Run script again (may be temporary issue)
☐ If persists: Check script logs for Python errors
```

**Issue:** Linking runs but produces 0 linked records
```
Actions:
☐ Verify all 3,606 companies in Notion
☐ Verify all 5,898 contacts in Notion
☐ Check if Notion API credentials correct
☐ Test on 10-record subset manually first
☐ Review 03_SETUP/link_companies_contacts.py logic
```

### Data Quality Issues

**Issue:** >5% of contacts missing email
```
Actions:
☐ This is ACCEPTABLE (Apollo data limitation)
☐ Document email coverage rate
☐ Do NOT re-import
☐ Plan for email enrichment in Phase 2
```

**Issue:** High duplicate email count (>10)
```
Actions:
☐ Sample check: Are they real duplicates or false positives?
☐ If real: May need to deduplicate before Phase 2
☐ If false positives (different people, same email): Mark as exception
☐ Document issue for Phase 2 handling
```

---

## 🎯 GO/NO-GO DECISION GATES

### After Test Import (Day 1)
```
GATE 1: Can we proceed to full import?

Must Have:
☐ 100 test records imported successfully
☐ 0 errors in test data
☐ Sample relationships verified

Decision:
☐ GO (proceed to full import) → continue to Day 2
☐ NO-GO (troubleshoot) → contact support, retry

If NO-GO, estimated delay: 4-8 hours
```

### After Full Import (Day 3)
```
GATE 2: Can we proceed to linking?

Must Have:
☐ 3,606 companies in Notion
☐ 5,898 contacts in Notion
☐ No import errors reported

Decision:
☐ GO (proceed to linking) → proceed to Day 4
☐ NO-GO (investigate) → re-run import

If NO-GO, estimated delay: 2-4 hours
```

### After Linking (Day 4)
```
GATE 3: Can we proceed to QA validation?

Must Have:
☐ linking_log.json shows 100% success
☐ 0 errors in linking script
☐ Random spot check of 5 links verified

Decision:
☐ GO (proceed to QA) → proceed to Day 5
☐ NO-GO (re-link) → investigate and retry

If NO-GO, estimated delay: 2-4 hours
```

### After QA Validation (Day 5)
```
GATE 4: Can we sign off Phase 1B complete?

Must Have:
☐ Data quality grade: A+ (≥95% pass rate)
☐ Email coverage: ≥95.7%
☐ Link coverage: 100%
☐ All team sign-offs complete

Decision:
☐ GO (Phase 1B COMPLETE) → move to Phase 2
☐ CONDITIONAL GO (minor issues) → document and track

If CONDITIONAL, list issues:
_________________________________
_________________________________
```

---

## 📞 ESCALATION CONTACTS

| Issue Type | Contact | Response Time |
|-----------|---------|----------------|
| Import technical error | Data Engineer | <2 hours |
| Script/linking failure | Data Engineer | <2 hours |
| Data quality concern | QA Lead | <4 hours |
| Notion connectivity | IT/Support | <1 hour |
| Schedule delay | Project Lead | <4 hours |
| Major blocker | RevOps Lead | <24 hours |

---

## 📊 SUCCESS METRICS

### Phase 1B Complete = All of These:

```
Data Imported:
✅ 3,606 companies in Notion
✅ 5,898 contacts in Notion
✅ 100% email coverage for companies (0 blanks allowed)

Data Linked:
✅ 5,898 / 5,898 contacts linked to companies (100%)
✅ 0 orphaned contacts
✅ Bidirectional relationships working

Data Quality:
✅ Critical fields 100% populated
✅ Email format validation: >99% clean
✅ Overall grade: A+ (≥95% pass)

Validation Complete:
✅ QA sign-off obtained
✅ All logs documented
✅ Team trained & ready
```

---

## 🚀 NEXT PHASE PREPARATION

Once Phase 1B complete, immediately start **Phase 2: Apollo Integration**

### Quick Summary:
- **Timeline:** Weeks 3-4 (starts immediately after sign-off)
- **Goal:** Real-time lead scoring + intent signals
- **Key Deliverable:** 200+ high-score leads identified
- **Team:** Same core team

### Prep Work (Can start during Day 5-6):
- [ ] Review 02_DOCUMENTATION/apollo_integration_guide.md
- [ ] Verify Apollo API credentials
- [ ] Set up intent signal categories
- [ ] Define lead scoring thresholds
- [ ] Brief sales team on scoring criteria

---

## 📋 COMPLETION CHECKLIST

### Pre-Launch (Before Day 1)
- [ ] All files verified in 01_DATA_IMPORT/
- [ ] Team trained & assigned
- [ ] Notion environment ready
- [ ] Backup created
- [ ] Network/VPN tested

### During Execution (Days 1-5)
- [ ] Test import completed successfully
- [ ] Full import completed successfully
- [ ] Linking automation 100% successful
- [ ] QA validation passed (A+ grade)
- [ ] All logs collected

### Post-Launch (Before Phase 2)
- [ ] All sign-offs obtained
- [ ] Documentation complete
- [ ] Phase 2 prep work started
- [ ] Team debriefing completed
- [ ] Issues logged for Phase 2

---

**STATUS: ✅ PHASE 1B READY TO LAUNCH**

**Estimated Start:** March 25, 2026
**Estimated Completion:** March 31, 2026
**Next Phase Kickoff:** April 1, 2026

---

**Document Version:** 1.0
**Last Updated:** March 24, 2026
**Prepared By:** RevOps Architect
**Classification:** Internal - Execution Document
