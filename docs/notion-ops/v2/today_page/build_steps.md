# ⭐ اليوم (Today) — Notion Build Steps

**Estimated time:** 30 minutes | **Prerequisites:** Lead Inbox built (Day 2 complete), Background folder contains Tasks/Opportunities/Lead Inbox DBs

---

## STEP 1 — Create the Page (2 min)

1. In sidebar, at the very top, click `+ Add a page`
2. Page title: `⭐ اليوم`
3. Icon: ⭐ (already in title)
4. Cover: none (keep it minimal)
5. Layout: empty page (NOT template)
6. Drag to position #1 in the sidebar, above Lead Inbox

---

## STEP 2 — Section 1: Header / System Status (2 min)

1. Type `/callout` and press Enter
2. Icon: 🟢
3. Text:
   ```
   النظام يعمل | آخر sync: 2026-04-10 | HOT: 0 | WARM: 0 | Overdue: 0
   ```
4. Color: Green background
5. This line is manually updated each morning for now

---

## STEP 3 — Section 2: 📞 اتصل اليوم (6 min)

1. Add heading: `/heading 2` → type `📞 اتصل اليوم`
2. Below the heading: type `/linked view of database`
3. Select: **Tasks**
4. Create a new view in this page (do NOT use an existing Tasks view)
5. Configure view:
   - **Name:** `Call Today`
   - **Type:** Table
   - **Filter:**
     - Task Type → is → `Urgent Call`
     - Status → is not → `Completed`
     - Due Date → on or before → Today
   - **Sort:**
     - Priority → descending
     - Due Date → ascending
   - **Properties visible:** Task Title, Company, Contact, Priority, Due Date, Task Owner, Context
   - **Properties hidden:** everything else
6. Optional: set "Open pages in" → Side peek (faster than full page)

---

## STEP 4 — Section 3: ✉️ تابع اليوم (5 min)

1. Add heading: `/heading 2` → type `✉️ تابع اليوم`
2. Below the heading: type `/linked view of database` → select Tasks
3. Create a new view:
   - **Name:** `Follow-up Today`
   - **Type:** Table
   - **Filter:**
     - Task Type → is → `Follow-up`
     - Status → is not → `Completed`
     - Due Date → on or before → Today
   - **Sort:**
     - Due Date → ascending
   - **Properties visible:** Task Title, Company, Contact, Due Date, Task Owner, Context

---

## STEP 5 — Section 4: 💼 الصفقات (5 min)

1. Add heading: `/heading 2` → type `💼 الصفقات`
2. Below the heading: type `/linked view of database` → select **Opportunities**
3. Create a new view:
   - **Name:** `Open Deals`
   - **Type:** Table
   - **Filter:**
     - Stage → is not → `Closed Won`
     - AND Stage → is not → `Closed Lost`
   - **Sort:**
     - Expected Close Date → ascending
   - **Properties visible:** Opportunity Name, Company, Stage, Deal Value, Expected Close Date, Deal Health, Next Action, Opportunity Owner

---

## STEP 6 — Section 5: 📥 Inbox Summary (4 min)

1. Add heading: `/heading 2` → type `📥 Inbox Summary`
2. Below the heading: type `/linked view of database` → select **Lead Inbox**
3. Create a new view:
   - **Name:** `New Today`
   - **Type:** Table
   - **Filter:**
     - Status → is → `New`
   - **Sort:**
     - Intake Date → descending
   - **Properties visible:** Name, Source, Company Name, Intake Date

---

## STEP 7 — Section 6: 📝 ملاحظات اليوم (2 min)

1. Add heading: `/heading 2` → type `📝 ملاحظات اليوم`
2. Below the heading: type `/toggle` → Enter
3. Toggle title: `📝 ملاحظات اليوم — 2026-04-10` (replace date each day)
4. Inside the toggle: empty text block
5. **Daily habit:** Each morning, create a new toggle with today's date and write under it.

---

## STEP 8 — Pin to Favorites (1 min)

1. Hover over `⭐ اليوم` in the sidebar
2. Click the `⋯` menu → `Add to Favorites`
3. Now it appears at the very top of the sidebar, always visible

---

## STEP 9 — Smoke Test (3 min)

1. Close Notion
2. Reopen Notion
3. The first thing you see should be: ⭐ اليوم in Favorites section
4. Click it
5. Verify all 6 sections render without errors
6. Verify:
   - Call Today: shows Tasks filtered correctly (may be empty if no Urgent Call tasks)
   - Follow-up Today: shows Tasks filtered correctly
   - Open Deals: shows Opportunities (may be empty)
   - Inbox Summary: shows Lead Inbox records with Status=New (empty if no leads yet)

---

## Done

⭐ اليوم page is ready. From tomorrow morning, this is the ONLY page you open.
