# 📥 Lead Inbox — Notion Build Steps

**Estimated time:** 25 minutes | **Prerequisites:** Notion workspace access + Schema locked

---

## STEP 1 — Create the Database (2 min)

1. Open Notion workspace `AI Sales OS`
2. In sidebar, below ⭐ اليوم, click `+ Add a page`
3. Page title: `📥 Lead Inbox`
4. Choose layout: **Table — Full page**
5. Icon: 📥 (already in title)

---

## STEP 2 — Add the 12 Fields in order (10 min)

The default `Name` column is already there. Add the remaining 11 fields by clicking `+` in the table header.

### 2.1 — Name (already exists)
- Rename if needed → `Name`
- Type: Title (default)

### 2.2 — Source
- Type: **Select**
- Options (exact order):
  1. `Manual` (gray)
  2. `Referral` (green)
  3. `Import` (blue)
  4. `Muqawil` (purple)
  5. `Other` (default)
  6. `Apollo` (red) ← reserved, do not use yet

### 2.3 — Company Name
- Type: **Text** (rich text)

### 2.4 — Email
- Type: **Email**

### 2.5 — Phone
- Type: **Phone**

### 2.6 — Title
- Type: **Text** (rich text)

### 2.7 — Status ⚠️ CRITICAL
- Type: **Status** (NOT Select — this is a different type in Notion)
- Groups and values:
  - **To-do** group → rename to "Not started" if needed:
    - `New` (gray)
  - **In progress** group:
    - `Review` (yellow)
  - **Complete** group:
    - `Qualified` (green)
    - `Rejected` (red)
    - `Duplicate` (orange)
    - `Moved` (blue)
- Default value: `New`

### 2.8 — Warm Signal
- Type: **Text** (rich text)

### 2.9 — Intake Owner
- Type: **Select**
- Options:
  - `Ibrahim`
  - `Ragheed`
  - `Soha`

### 2.10 — Intake Date
- Type: **Date**
- Include time: OFF
- Default: Today (when using templates)

### 2.11 — Notes
- Type: **Text** (rich text)

### 2.12 — Rejection Reason
- Type: **Select**
- Options:
  - `Not ICP`
  - `No Contact Info`
  - `Duplicate`
  - `Low Quality`
  - `Other`

---

## STEP 3 — Create 4 Views (5 min)

Click `+ Add view` for each:

### View 1: `جديد` (New)
- Type: Table
- Filter: **Status** equals `New`
- Sort: **Intake Date** descending
- Visible properties: Name, Source, Company Name, Intake Owner, Intake Date

### View 2: `قيد المراجعة` (Review)
- Type: Table
- Filter: **Status** equals `Review`
- Sort: **Intake Date** ascending (oldest first — FIFO)
- Visible properties: Name, Source, Company Name, Email, Phone, Warm Signal, Intake Owner

### View 3: `جاهز للنقل` (Ready to move)
- Type: Table
- Filter: **Status** equals `Qualified`
- Sort: **Intake Date** ascending
- Visible properties: Name, Company Name, Email, Phone, Title, Intake Owner, Warm Signal

### View 4: `مؤرشف` (Archived)
- Type: Table
- Filter: **Status** is `Rejected` OR `Duplicate` OR `Moved`
- Sort: **Intake Date** descending
- Visible properties: Name, Source, Status, Rejection Reason, Intake Date

---

## STEP 4 — Create 3 Templates (5 min)

Click the dropdown arrow next to `New` button (top-right of the table) → `+ New template`.

### Template 1: ➕ Manual
- Name: `➕ Manual`
- Pre-filled fields:
  - Source → `Manual`
  - Status → `New`
  - Intake Owner → `Ragheed`
  - Intake Date → (leave empty — Notion will set today)
- Body: empty

### Template 2: 🤝 Referral
- Name: `🤝 Referral`
- Pre-filled fields:
  - Source → `Referral`
  - Status → `New`
  - Intake Owner → `Ragheed`
- Body: add a prompt header →
  ```
  ### من أحاله
  (اسم الشخص + علاقته)
  ### لماذا دافئ
  (سبب الإحالة)
  ```

### Template 3: 💳 Business Card
- Name: `💳 Business Card`
- Pre-filled fields:
  - Source → `Manual`
  - Status → `New`
  - Intake Owner → `Ragheed`
  - Notes → `من معرض/حدث: `
- Body: empty

---

## STEP 5 — Pin to Sidebar (1 min)

- Drag `📥 Lead Inbox` in sidebar so it appears **directly below ⭐ اليوم**
- No other page should be between them

---

## STEP 6 — Smoke Test (2 min)

1. Click `New ▼` → `➕ Manual`
2. Fill Name = "Test Lead 1", Email = "test1@test.com", Company Name = "Test Co"
3. Verify it appears in `جديد` view
4. Change Status → `Review` → confirm it moves to `قيد المراجعة`
5. Change Status → `Qualified` → confirm it moves to `جاهز للنقل`
6. Delete the test record

---

## Done

Lead Inbox is ready for Day 2 operational use.
Next step: Day 3 — build ⭐ اليوم page (Today).
