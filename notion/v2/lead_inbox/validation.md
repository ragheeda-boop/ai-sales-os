# 📥 Lead Inbox — Validation Checklist

Run these 12 tests immediately after the Notion build is complete.
All 12 must pass before marking Day 2 done.

---

## Schema Tests

- [ ] **T1 — Field count:** The DB has exactly **12 fields**
- [ ] **T2 — Status type:** The `Status` field is of type **`Status`** (not `Select`) — verify by clicking the field name and checking the type label
- [ ] **T3 — Status groups:** Status has 6 values distributed across 3 groups:
  - Not started: `New`
  - In progress: `Review`
  - Complete: `Qualified`, `Rejected`, `Duplicate`, `Moved`
- [ ] **T4 — Source values:** Source dropdown has exactly **6 values** in this order: `Manual`, `Referral`, `Import`, `Muqawil`, `Other`, `Apollo`
- [ ] **T5 — Intake Owner values:** Intake Owner dropdown has exactly **3 values**: `Ibrahim`, `Ragheed`, `Soha`
- [ ] **T6 — Rejection Reason values:** Rejection Reason dropdown has exactly **5 values**: `Not ICP`, `No Contact Info`, `Duplicate`, `Low Quality`, `Other`

---

## Template Tests

- [ ] **T7 — ➕ Manual template:** Click `New ▼` → `➕ Manual` → verify Source=Manual, Status=New, Intake Owner=Ragheed are auto-filled
- [ ] **T8 — 🤝 Referral template:** Click `New ▼` → `🤝 Referral` → verify Source=Referral, Status=New, Intake Owner=Ragheed + body contains "من أحاله"
- [ ] **T9 — 💳 Business Card template:** Click `New ▼` → `💳 Business Card` → verify Source=Manual, Status=New, Notes starts with "من معرض/حدث:"

---

## View Tests

- [ ] **T10 — State transition test:**
  1. Create a test record: Name="اختبار التحقق", Email="check@test.com", Company Name="Test"
  2. Confirm it appears in `جديد` view
  3. Change Status → `Review` → confirm it moves to `قيد المراجعة` view
  4. Change Status → `Qualified` → confirm it moves to `جاهز للنقل` view
  5. Change Status → `Moved` → confirm it moves to `مؤرشف` view
  6. Delete the record

- [ ] **T11 — Rejection path test:**
  1. Create a test record via `➕ Manual`
  2. Change Status → `Rejected`
  3. Fill Rejection Reason = `Not ICP`
  4. Confirm it appears in `مؤرشف` view
  5. Delete the record

- [ ] **T12 — Sidebar position test:** `📥 Lead Inbox` appears in sidebar directly below `⭐ اليوم` with nothing between them

---

## If any test fails

1. Do NOT proceed to Day 3
2. Open `notion/v2/lead_inbox/issues.md` (create if missing)
3. Log: test number, what went wrong, screenshot if possible
4. Fix the issue in Notion
5. Re-run the failed test
6. Only after all 12 pass → proceed to Day 3

---

## Sign-off

- Built by: _______________
- Date built: _______________
- All 12 tests passed: ☐
- Ready for Day 3 (Today page): ☐
