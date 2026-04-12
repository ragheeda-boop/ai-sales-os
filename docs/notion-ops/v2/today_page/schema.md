# ⭐ اليوم (Today) — Final Page Spec

**Version:** 0.1 Bootstrap | **Date:** 2026-04-10 | **Status:** ✅ LIVE in Notion

**Live URL:** https://www.notion.so/33e69eddf30181548db3cbe78bfc7a71
**Page ID:** `33e69edd-f301-8154-8db3-cbe78bfc7a71`

---

## Reality Statement

The previous backend (auto_tasks, opportunity_manager, analytics_tracker) was **built but never actually operated**. There are NO real Tasks, NO real Opportunities, and NO trusted historical data in those databases.

The v1.0 spec (which depended on Tasks + Opportunities + Apollo sync) is therefore **premature**. We need a version that only depends on what is **real today**: the Lead Inbox that Ragheed is filling manually.

This page (v0.1 Bootstrap) is that version.

---

## Purpose

The **only** page the operator opens each morning during the bootstrap phase.
Everything needed for manual lead triage and daily focus lives here.
This page depends **exclusively** on the 📥 Lead Inbox database.

---

## Design Principles (Bootstrap Mode)

1. **Only real data** — depend only on Lead Inbox. No Tasks, no Opportunities, no Apollo, no dashboards.
2. **Operator-first** — the operator can run the day from this page without touching any backend script.
3. **Honest about state** — do not pretend the CRM has contacts and tasks. It doesn't yet.
4. **Manual focus** — "today's focus" is a manual checklist, not a computed view.
5. **Upgradable** — clear upgrade path to v1.0 once real Tasks + Opportunities exist.

---

## Page Type

- Notion **page** (not database)
- No database properties
- Lives at the top of the sidebar, first item
- Pinned as Favorite
- Title: `اليوم` (icon `⭐` set separately to avoid duplication)

---

## Page Structure (6 sections — LOCKED for v0.1)

### Section 1 — 📥 Leads جديدة (New Leads)

**Block type:** Linked database view of **📥 Lead Inbox**
**Source DB:** https://www.notion.so/b9ae8e060ca64fc9a7f5d8706e229b59
**Filter:** `Status = New`
**Sort:** `Intake Date` descending
**Limit:** no explicit cap (should be small)
**Visible columns:** Name, Source, Company Name, Intake Owner, Intake Date
**Purpose:** Leads that arrived but haven't been triaged yet. Target = 0 at end of day.

---

### Section 2 — 🔍 Leads تحت المراجعة (Leads in Review)

**Block type:** Linked database view of **📥 Lead Inbox**
**Filter:** `Status = Review`
**Sort:** `Intake Date` ascending (oldest first)
**Visible columns:** Name, Company Name, Email, Phone, Warm Signal, Intake Owner, Intake Date
**Purpose:** Leads being evaluated — oldest at top so nothing rots.

---

### Section 3 — ✅ Leads مؤهلة وجاهزة للنقل (Qualified — Ready to Move)

**Block type:** Linked database view of **📥 Lead Inbox**
**Filter:** `Status = Qualified`
**Sort:** `Intake Date` ascending
**Visible columns:** Name, Company Name, Email, Phone, Title, Intake Owner, Intake Date
**Purpose:** Leads validated and ready to be manually copied into Contacts DB. Once copied, operator moves Status → `Moved`.

---

### Section 4 — 🚚 Leads نُقلت إلى CRM (Moved to CRM)

**Block type:** Linked database view of **📥 Lead Inbox**
**Filter:** `Status = Moved`
**Sort:** `Intake Date` descending (most recent first)
**Limit:** 10 rows
**Visible columns:** Name, Company Name, Intake Owner, Intake Date
**Purpose:** Audit trail of what was transferred to the real CRM. Running counter of true progress.

---

### Section 5 — 🎯 تركيز اليوم (Today's Focus)

**Block type:** Manual checklist (to-do blocks)
**Source:** None — fully manual
**Content:** 5 empty to-do items the operator fills each morning
**Purpose:** Operator writes the 3–5 most important things for today. This is a **manual discipline**, not a computed view. Replaces "📞 اتصل اليوم" from v1.0.

---

### Section 6 — 📝 ملاحظات اليوم (Today's Notes)

**Block type:** Toggle heading
**Title:** `📝 ملاحظات اليوم`
**Content:** empty text block
**Purpose:** Free-form notes for conversations, blockers, decisions. New toggle each day; old toggles become historical record.

---

## Explicitly Excluded from v0.1

| What | Why |
|---|---|
| ❌ 📞 اتصل اليوم (Tasks view) | No real Tasks yet. auto_tasks never operated. |
| ❌ ✉️ تابع اليوم (Tasks view) | Same reason. |
| ❌ 💼 الصفقات (Opportunities view) | No real Opportunities yet. opportunity_manager never operated. |
| ❌ Morning Brief | Depends on Tasks + Contacts. Frozen in workflow. |
| ❌ Sales Dashboard | Depends on mass Contacts/Companies data. Frozen. |
| ❌ Apollo sync status header | Irrelevant while we're in manual intake mode. |
| ❌ HOT/WARM/Overdue counters | Depend on Lead Score which isn't being trusted yet. |

These sections return in **v1.0** once the upgrade criteria below are met.

---

## Daily Flow (Bootstrap)

| Time | Action | Section |
|---|---|---|
| 9:00 | Open ⭐ اليوم. Check 📥 Leads جديدة count. | 1 |
| 9:05 | Triage new leads → Review or Rejected. Fill in 🎯 تركيز اليوم. | 1, 5 |
| 9:30 | Work through 🔍 Leads تحت المراجعة — decide Qualified / Rejected / Duplicate. | 2 |
| 11:00 | For each ✅ Qualified lead, copy manually into Contacts DB → set Status = Moved. | 3 |
| 12:00 | Lunch | — |
| 14:00 | Execute 🎯 تركيز اليوم items (outreach, meetings, manual follow-ups). | 5 |
| 16:00 | Second pass on Lead Inbox — clear remaining New/Review. | 1, 2 |
| 16:45 | Final triage. Target: 0 leads in Status=New. | 1 |
| 16:55 | Write 📝 ملاحظات اليوم. | 6 |
| 17:00 | Close Notion. | — |

---

## Success Criteria (Bootstrap)

At 5 PM, the operator should be able to answer:
1. How many new leads did I triage today?
2. How many leads did I move to the real CRM today?
3. What's the one thing I committed to for tomorrow?

If these can be answered in under 30 seconds → the page is working.

---

## Upgrade Path → v1.0

The Today page upgrades to v1.0 when **ALL** of these are true:

1. ≥ 20 leads have reached `Status = Moved` and exist in Contacts DB
2. `scripts/automation/auto_tasks.py` has been run successfully at least 3 times against real Moved contacts
3. At least 1 real Opportunity exists in the Opportunities DB (non-test)
4. At least 1 real Meeting exists in the Meetings DB (non-test)
5. Operator has had ≥ 5 real sales conversations traceable through the system

When those 5 gates pass, Day N+1 = v1.0 build: re-introduce 📞 اتصل اليوم, ✉️ تابع اليوم, 💼 الصفقات sections (spec already exists in git history at this file, v1.0).

---

## Change log

| Date | Change |
|---|---|
| 2026-04-10 | Initial v1.0 lock — 6 sections (Header, Call, Follow-up, Deals, Inbox, Notes). Depended on Tasks + Opportunities DBs. |
| 2026-04-10 | **Pivoted to v0.1 Bootstrap Mode** — replaced Tasks/Opportunities sections with Lead Inbox-only views. Reality: no real Tasks or Opportunities exist yet. Page now depends exclusively on 📥 Lead Inbox. Added upgrade path to v1.0. |
