# Notion v2 Sidebar Structure

**Version:** 2.0 | **Date:** 2026-04-10 | **Status:** Final

---

## Top-Level Sidebar (4 items only)

```
⭐ اليوم              ← Today page (الوحيدة التي تُفتح صباحًا)
📥 Lead Inbox         ← intake database (Manual/Referral/Import/Muqawil/Other)
📖 Manual             ← نسخة من MANUAL.md
🛠️ Runbook           ← نسخة من RUNBOOK.md
```

**No other items at the top level.**

---

## Background Folder (collapsed by default)

```
📁 Background
  ├─ Contacts
  ├─ Companies
  ├─ Tasks
  ├─ Meetings
  ├─ Opportunities
  ├─ Activities
  └─ Email Hub
```

These databases remain live and fully functional (backend writes to them daily).
The operator only opens them when explicitly needed — never as part of the daily routine.

---

## Archive Folder (reference only)

```
📁 Archive
  ├─ 📊 Old Dashboards
  │   ├─ AI_Sales_OS_Live_Dashboard
  │   ├─ AI_Sales_OS_MindMap
  │   ├─ AI_Sales_OS_Test_Report
  │   ├─ Companies_DB_Revenue_Engine_Analysis
  │   ├─ Company_Centric_Enforcement_Plan
  │   ├─ Full_System_Revenue_Engine_Analysis
  │   ├─ Sales_Dashboard_Accounts_view
  │   └─ تقرير_الاكتتابات_السعودية_2026
  └─ 📧 Old Morning Briefs
```

---

## Rules

1. **Only 4 items at the top level.** Never add a 5th.
2. **Background folder is collapsed** by default. Operator doesn't see the 7 DBs.
3. **Archive is for reference only.** Nothing new goes here.
4. **No duplicates.** If a page exists in Background, it does NOT exist at the top level.
5. **Order matters:** ⭐ اليوم is always first. Lead Inbox is always second.

---

## What was removed from the sidebar (2026-04-10)

- 🚀 Command Center (moved to Background or archived)
- 🔁 Autonomous Loop Dashboard (archived)
- 📚 SOPs & Workflow Reference (absorbed into Manual)
- All 8 HTML dashboards (moved to Archive/Old Dashboards)
- Morning Brief pages (archived)
