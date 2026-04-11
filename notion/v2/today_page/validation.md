# ⭐ اليوم — Validation Checklist

Run these tests after building the page. All must pass before Day 4.

---

## Structural Tests

- [ ] **T1 — Sidebar position:** `⭐ اليوم` is the first item in Favorites, above `📥 Lead Inbox`
- [ ] **T2 — Section count:** The page has exactly 6 sections (Header, Call Today, Follow-up Today, Deals, Inbox Summary, Notes toggle)
- [ ] **T3 — No extra blocks:** No dashboards, no charts, no KPIs, no Morning Brief embeds

---

## Linked View Tests

- [ ] **T4 — Call Today source:** Section 2 linked view is connected to the **Tasks** database (not a different DB)
- [ ] **T5 — Call Today filter:** Filter shows only Urgent Call tasks that are not Completed and due today or earlier
- [ ] **T6 — Follow-up Today filter:** Filter shows only Follow-up tasks that are not Completed and due today or earlier
- [ ] **T7 — Deals filter:** Filter shows only Opportunities where Stage is NOT Closed Won AND NOT Closed Lost
- [ ] **T8 — Inbox Summary filter:** Filter shows only Lead Inbox records where Status = New

---

## Sort Tests

- [ ] **T9 — Call Today sort:** Priority descending, then Due Date ascending
- [ ] **T10 — Follow-up sort:** Due Date ascending (oldest first)
- [ ] **T11 — Deals sort:** Expected Close Date ascending

---

## End-to-End Tests

- [ ] **T12 — Inbox flow test:**
  1. Create a test record in Lead Inbox: Name="T12 Test", Source=Manual, Status=New
  2. Open ⭐ اليوم
  3. Verify the record appears in Section 5 (Inbox Summary)
  4. Go to Lead Inbox and change Status → Review
  5. Refresh ⭐ اليوم → record should disappear from Section 5
  6. Delete the test record

- [ ] **T13 — Notes toggle test:**
  1. Click on the `📝 ملاحظات اليوم` toggle
  2. Write "Test note — delete me"
  3. Collapse the toggle
  4. Reopen → text should persist
  5. Delete the test text

- [ ] **T14 — Daily routine walkthrough:** Pretend it's 9 AM. Open ⭐ اليوم. Within 30 seconds, you should know:
  - How many calls to make today (count rows in Section 2)
  - How many follow-ups (count rows in Section 3)
  - Which deals need attention (look at Section 4 Deal Health column)
  - How many new leads waiting (row count in Section 5)

---

## Success Criterion

**The single test that matters:** Can the operator open Notion at 9 AM and know what to do within 30 seconds, using only this page and nothing else?

If yes → Day 3 complete. Proceed to Day 4.
If no → log specific friction points in `notion/v2/today_page/issues.md` and iterate.

---

## Sign-off

- Built by: _______________
- Date built: _______________
- All 14 tests passed: ☐
- Ready for Day 4 (import_list.py build): ☐
