# Notion Sidebar v2.0 — LIVE State

**Date:** 2026-04-10
**Status:** ✅ Structure deployed via API. Sidebar order requires 1 manual drag step.

---

## Top-Level (Workspace Root) — 5 items

All 5 moved to workspace root via `notion-move-pages` with `{"type": "workspace"}`.

| # | Page | ID | URL |
|---|---|---|---|
| 1 | ⭐ اليوم | `33e69edd-f301-8154-8db3-cbe78bfc7a71` | https://www.notion.so/33e69eddf30181548db3cbe78bfc7a71 |
| 2 | 📖 Manual | `33e69edd-f301-8168-a315-c47538e60d99` | https://www.notion.so/33e69eddf3018168a315c47538e60d99 |
| 3 | 🛠️ Runbook | `33e69edd-f301-8180-84fb-c4c157705994` | https://www.notion.so/33e69eddf301818084fbc4c157705994 |
| 4 | 📁 Background | `33e69edd-f301-817e-973d-e7c17bc0c0e8` | https://www.notion.so/33e69eddf301817e973de7c17bc0c0e8 |
| 5 | 📦 Archive | `33e69edd-f301-81bb-b932-c89747bb752a` | https://www.notion.so/33e69eddf30181bbb932c89747bb752a |

**Note:** 📥 Lead Inbox (`b9ae8e06-0ca6-4fc9-a7f5-d8706e229b59`) is a database already at workspace root. It is the 6th top-level item.

---

## 📁 Background — 6 databases moved

| DB | ID | Previous parent |
|---|---|---|
| 🏢 Companies | `331e04a6-2da7-4afe-9ab6-b0efead39200` | workspace root |
| 👤 Contacts | `9ca842d2-0aa9-460b-bdd9-58d0aa940d9c` | workspace root |
| ✅ Tasks | `5644e28a-e9c9-422b-90e2-10df500ad607` | workspace root |
| 📅 Meetings | `c084e81d-e262-4e6c-873e-9e0dc60f5a35` | workspace root |
| 💰 Opportunities | `abfee51c-53af-47f7-9834-851b15e8a92b` | workspace root |
| 📧 Email Hub V1.0 | `c590578c-c3a3-4a57-ac57-1a6ed113be4b` | workspace root |

**Missing:** 📝 Activities DB was listed in the blueprint but **does not exist** in the workspace. No "Activities" database was found in search. Skipped. Remove from CLAUDE.md if confirmed not needed.

---

## 📦 Archive — 5 v4.0 pages moved

| Page | ID |
|---|---|
| 🚀 Sales Operating System — Command Center v4.0 | `32b69edd-f301-81d3-9388-ee77ee19db27` |
| 📊 Sales Command Center — Dashboard v4.0 | `32b69edd-f301-81d2-b996-d7235a01d13f` |
| 🔁 Autonomous Loop Dashboard v4.0 | `33069edd-f301-8148-b799-d8a739d89609` |
| 🎯 AI Sales OS — Live Dashboard | `33169edd-f301-812b-a9ac-d7c627b99a60` |
| ⚡ Task Center — Daily Operations | `33069edd-f301-8129-b1bd-e37d91b40977` |

**Note:** Command Center v4.0 was the previous parent of ⭐ اليوم and the 4 new v2.0 pages. It was emptied (5 children moved to workspace root) before being archived, so archiving it did not bury the v2.0 structure.

---

## ✋ Manual Action Required (1 step)

The Notion API **cannot control sidebar order**. All 5 top-level pages exist and are pinned candidates, but Ragheed must manually drag them into the exact order shown in the blueprint:

**Target sidebar order (drag top to bottom):**

```
⭐ اليوم              ← 1st (PRIMARY)
📥 Lead Inbox          ← 2nd
📖 Manual              ← 3rd
🛠️ Runbook            ← 4th
───────────────────
📁 Background          ← 5th (collapsed)
📦 Archive             ← 6th (collapsed)
```

**Steps in Notion UI:**
1. Right-click each of the 6 items → "Add to Favorites" (optional but recommended for top-of-sidebar pinning)
2. Drag ⭐ اليوم to the top
3. Drag 📥 Lead Inbox below it
4. Drag 📖 Manual, then 🛠️ Runbook below
5. Drag 📁 Background and 📦 Archive to the bottom (or collapse them)

**Verification:** Open sidebar and confirm the 6 items are in the correct visual order.

---

## API Calls Executed

1. `notion-create-pages` — created 4 new pages (Manual, Runbook, Background, Archive) under Command Center v4.0
2. `notion-move-pages` — moved 6 DBs → Background
3. `notion-move-pages` — moved 4 v4.0 dashboards → Archive
4. `notion-move-pages` — moved 5 pages (Today + 4 new) → workspace root
5. `notion-move-pages` — moved Command Center v4.0 → Archive

Total: 5 API calls, 16 items relocated, 0 items deleted (all moves are reversible).
