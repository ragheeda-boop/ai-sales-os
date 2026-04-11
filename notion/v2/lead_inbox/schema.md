# 📥 Lead Inbox — Final Schema

**Version:** 2.0 (LIVE in Notion) | **Date:** 2026-04-10 | **Status:** ✅ Built & validated

**Live URL:** https://www.notion.so/b9ae8e060ca64fc9a7f5d8706e229b59
**Data Source ID:** `64aec610-22b2-4444-a8a5-80c238a86633`

---

## Purpose

Single entry point for every new lead that does NOT come through Apollo's automatic sync.
All manual leads, referrals, imported lists, and Muqawil leads pass through this inbox.

---

## Database Properties (12 fields — LOCKED)

| # | Property Name | Type | Options / Config | Required | Default |
|---|---|---|---|---|---|
| 1 | **Name** | Title | — | ✅ | — |
| 2 | **Source** | Select | `Manual` · `Referral` · `Import` · `Muqawil` · `Other` · `Apollo` *(reserved)* — 6 values total, no Business Card (handled via Manual + Notes prefix) | ✅ | per template |
| 3 | **Company Name** | Rich text | — | ⚪ | — |
| 4 | **Email** | Email | — | ⚪ * | — |
| 5 | **Phone** | Phone | — | ⚪ * | — |
| 6 | **Title** | Rich text | — | ⚪ | — |
| 7 | **Status** | **Status** (not Select) | See state machine below | ✅ | New |
| 8 | **Warm Signal** | Rich text | سبب الدفء بسطر واحد | ⚪ | — |
| 9 | **Intake Owner** | Select | `Ibrahim` · `Ragheed` · `Soha` | ✅ | per template |
| 10 | **Intake Date** | Date | includeTime: false | ✅ | Today |
| 11 | **Notes** | Rich text | — | ⚪ | — |
| 12 | **Rejection Reason** | Select | `Not ICP` · `No Contact Info` · `Duplicate` · `Low Quality` · `Other` | ⚪ ** | — |

\* At least one of Email or Phone must exist before Status can move to Qualified.
\*\* Required only when Status = Rejected.

---

## Source field — Final Values

### Active Sources (first 14 days)
- **Manual** — entered by hand via ➕ Manual template
- **Referral** — warm intro from existing network
- **Import** — bulk upload via `scripts/intake/import_list.py` (Day 4)
- **Muqawil** — from `pipelines/muqawil/` (manual dual-entry for now)
- **Other** — anything that doesn't fit above

### Reserved Sources (in dropdown but NOT used in first 14 days)
- **Apollo** — reserved. Apollo contacts continue flowing through the existing `daily_sync.py` → Contacts DB path. They do NOT enter Lead Inbox. This value exists only to keep the schema forward-compatible.

### Deferred Sources (NOT in schema yet)
- Scraped · Platform · BusinessCard · CallCenter → Phase 2

---

## Status field — State Machine (type: `status`, NOT `select`)

```
      ┌──────┐
      │ New  │  (Not started)
      └───┬──┘
          │ quick triage
          ▼
      ┌────────┐
      │ Review │  (In progress)
      └───┬────┘
          │
    ┌─────┼─────┬──────────┐
    ▼     ▼     ▼          ▼
Qualified Rejected Duplicate (Complete group)
    │
    ▼
  Moved  (Complete — final state)
```

### Status values grouped by Notion `status` type

**Not started:**
- `New` — just arrived, not yet triaged (color: gray)

**In progress:**
- `Review` — being evaluated (color: yellow)

**Complete:**
- `Qualified` — validated, ready to move to Contacts DB (color: green)
- `Rejected` — not ICP or bad data (color: red)
- `Duplicate` — already exists in Contacts DB (color: orange)
- `Moved` — already transferred to Contacts DB (color: blue)

### Rules
1. Default on create → `New`
2. `New` → `Review` (next allowed step)
3. `Review` → `Qualified` / `Rejected` / `Duplicate` (triage decision)
4. `Qualified` → `Moved` (after manual copy to Contacts DB — Day 4+ will automate)
5. `Rejected` requires Rejection Reason to be filled
6. `Moved` is terminal — no further transitions

---

## Validation Rules (enforced manually until Day 4 automation)

Before Status can move to `Qualified`:
- [ ] Name is filled
- [ ] Company Name is filled
- [ ] At least one of (Email, Phone) is filled
- [ ] Intake Owner is assigned
- [ ] Source is not empty

Before Status can move to `Rejected`:
- [ ] Rejection Reason is filled

---

## Relationship to Other Databases

| From → To | When | How |
|---|---|---|
| Lead Inbox → Contacts DB | Status = Qualified → Moved | Manual copy in Day 2–13. Automated by `scripts/intake/move_to_contacts.py` starting Day 14+ |
| Apollo sync → Contacts DB | Every 24h | Unchanged. Does NOT pass through Lead Inbox. |
| Muqawil pipeline → Lead Inbox | Manual for now | Future: `scripts/intake/from_muqawil.py` |

---

## What this schema is NOT

- ❌ Not a Contacts DB replacement
- ❌ Not a scoring engine input (scoring happens only after Moved → Contacts DB)
- ❌ Not an Apollo mirror
- ❌ Not a CRM

It is purely a **staging/triage queue** for non-Apollo leads.

---

## Change log

| Date | Change |
|---|---|
| 2026-04-10 | Initial lock — 12 fields, 6 sources (1 reserved), 6 status values |
| 2026-04-10 | **LIVE BUILD** — DB created via API, Status options customized manually (New/Review/Qualified/Rejected/Duplicate/Moved), 5 Arabic views active (🆕 جديد, 🔍 قيد المراجعة, ✅ جاهز للنقل, 📋 كل السجلات, 🗄️ مؤرشف), 3 templates created (Manual, Referral, Business Card as Manual+Notes), validation checklist page attached in Notion |
