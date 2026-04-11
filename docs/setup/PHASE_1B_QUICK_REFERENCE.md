# ⚡ PHASE 1B QUICK REFERENCE
## One-Page Execution Guide

---

## 📅 THE 5-DAY CRITICAL PATH

```
┌──────────────────────────────────────────────────────────────┐
│ DAY 1: TEST IMPORT                                           │
│ ├─ Time: 2 hours                                             │
│ ├─ What: Import 100 test records                             │
│ ├─ File: sample_100_records.json                             │
│ ├─ Owner: RevOps Lead                                        │
│ └─ Decision: GO/NO-GO                                        │
├──────────────────────────────────────────────────────────────┤
│ DAY 2-3: FULL IMPORT                                         │
│ ├─ Time: 4 hours (can run parallel)                         │
│ ├─ What: Import 3,606 companies + 5,898 contacts           │
│ ├─ Files: IMPORT_companies_FINAL.csv + IMPORT_contacts... │
│ ├─ Owner: RevOps Lead                                        │
│ └─ Parallel: Both imports can run simultaneously             │
├──────────────────────────────────────────────────────────────┤
│ DAY 4: LINKING                                               │
│ ├─ Time: 2 hours                                             │
│ ├─ What: Auto-link all 5,898 contacts to companies          │
│ ├─ Tool: python link_companies_contacts.py                  │
│ ├─ Owner: Data Engineer                                      │
│ └─ Target: 100% success (5,898/5,898 linked)               │
├──────────────────────────────────────────────────────────────┤
│ DAY 5: QA & VALIDATION                                       │
│ ├─ Time: 3 hours                                             │
│ ├─ What: Verify data quality A+                              │
│ ├─ Check: All required fields, duplicates, relationships     │
│ ├─ Owner: QA Lead                                            │
│ └─ Grade: A+ (≥95% pass)                                     │
└──────────────────────────────────────────────────────────────┘
```

---

## 🎯 CRITICAL NUMBERS

| What | Target | How to Verify |
|------|--------|---------------|
| Companies | 3,606 | "View all" in Notion |
| Contacts | 5,898 | "View all" in Notion |
| Linked (%) | 100% | Check linking_log.json |
| Data Quality | A+ | QA validation checklist |
| Time to Complete | 9 hours | Total across 5 days |

---

## 📍 FILE LOCATIONS

```
01_DATA_IMPORT/
├── sample_100_records.json              ← DAY 1 (test)
├── IMPORT_companies_FINAL.csv           ← DAY 2 (3,606)
└── IMPORT_contacts_FINAL.csv            ← DAY 3 (5,898)

03_SETUP/
└── link_companies_contacts.py           ← DAY 4 (auto-link)

02_DOCUMENTATION/
├── PHASE_1B_LAUNCH_CHECKLIST.md         ← Detailed guide
└── FIELD_MAPPING_RULES.md               ← Reference
```

---

## 🚦 GO/NO-GO GATES

### Gate 1 (End of Day 1):
```
✅ GO if: 100 records imported, 0 errors
❌ NO-GO if: >1% error rate OR missing fields
```

### Gate 2 (End of Day 3):
```
✅ GO if: 3,606 + 5,898 records in Notion
❌ NO-GO if: Import error or incomplete
```

### Gate 3 (End of Day 4):
```
✅ GO if: linking_log.json shows 100% success
❌ NO-GO if: error_count > 0
```

### Gate 4 (End of Day 5):
```
✅ GO if: Data quality A+ (≥95% pass)
❌ NO-GO if: Grade < A+ (requires review)
```

---

## ⚠️ RED FLAGS & QUICK FIXES

| Problem | Check | Fix |
|---------|-------|-----|
| Import slow (>30 min) | Notion status page | Retry after 5 min |
| 0 records imported | File encoding | Re-save CSV as UTF-8 |
| Linking 0 records | Companies in Notion? | Verify import completed |
| >5% missing emails | Check data quality | This is OK (known Apollo limit) |
| Duplicate companies | Count distinct IDs | This is NOT OK - investigate |

---

## 👥 WHO DOES WHAT

```
DAY 1: RevOps Lead
├─ Open Notion
├─ Import sample_100_records.json
└─ Validate 100 records

DAY 2-3: RevOps Lead
├─ Import IMPORT_companies_FINAL.csv
└─ Import IMPORT_contacts_FINAL.csv (parallel)

DAY 4: Data Engineer
├─ Run: python link_companies_contacts.py
└─ Verify: linking_log.json success

DAY 5: QA Lead
├─ Run validation checklist
├─ Grade data quality
└─ Obtain sign-offs
```

---

## 🔧 THE LINKING SCRIPT

```bash
# What to do:
cd 03_SETUP/
python link_companies_contacts.py

# What you'll see:
"Linking companies and contacts..."
"Processing batch 1/50..."
"Success: 5,898 / 5,898 linked"
"Errors: 0"

# What to check:
cat linking_log.json
# Should show: "linked_count": 5,898, "error_count": 0
```

---

## ✅ SUCCESS CHECKLIST (Copy & Post)

```
PHASE 1B SUCCESS = All of These:

□ 3,606 companies in Notion
□ 5,898 contacts in Notion
□ 100% linked (5,898/5,898)
□ 0 errors in logs
□ Data quality: A+
□ Email coverage: ≥95.7%
□ QA approved
□ All sign-offs done

= PHASE 1B COMPLETE ✅
```

---

## 📞 STUCK? ASK THESE PEOPLE

| When | Who |
|------|-----|
| "Import won't work" | Data Engineer |
| "Script error" | Data Engineer |
| "Data looks wrong" | QA Lead |
| "Notion won't respond" | IT Support |
| "Behind schedule" | Project Lead |

---

## ⏰ TIME TRACKER

| Task | Est. | Actual | Owner |
|------|------|--------|-------|
| Day 1 (Test) | 2h | ___ | RevOps |
| Day 2-3 (Import) | 4h | ___ | RevOps |
| Day 4 (Link) | 2h | ___ | Engineer |
| Day 5 (QA) | 3h | ___ | QA |
| **TOTAL** | **9h** | **___** | - |

---

## 🚀 WHAT'S NEXT?

After Phase 1B complete (March 31):
- **Phase 2:** Apollo Integration (April 1-14)
- **Phase 3:** Automation rules (April 15-25)
- **Phase 4:** Odoo sync (April 26 - May 5)

**Current Status:** 🟢 GO FOR LAUNCH

---

*Keep this page open. Update times as you go. Share in Slack once complete.*
