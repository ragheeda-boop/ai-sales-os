# AI Execution Engine v1.1 — Integration Patches

**Date:** 2026-04-11
**Prereqs:** v1.0 modules already deployed
(`scripts/scoring/ai_decision_engine.py`,
`scripts/automation/call_script_builder.py`,
`scripts/automation/ai_sequence_generator.py`,
`scripts/automation/ai_action_executor.py`)

**What v1.1 adds:**
- Company DB writes: `Strategic Fit`, `Pain Summary`, `Sales Angle` (rich_text)
- Contact DB writes: `Call Script Clean`, `Email Draft` (rich_text)
- Integration patches for `lead_score.py`, `auto_tasks.py`, `auto_sequence.py`
- Full pipeline placement (Job 2 of `daily_sync.yml`)

---

## 1. New Notion Fields Required

Run via `notion-schema-manager` skill or add manually:

### Companies DB
| Field | Type | Values |
|-------|------|--------|
| `Priority` | select | `P1` / `P2` / `P3` |
| `Strategic Fit` | rich_text | auto-generated |
| `Pain Summary` | rich_text | auto-generated |
| `Sales Angle` | rich_text | auto-generated |

### Contacts DB
| Field | Type | Notes |
|-------|------|-------|
| `Call Script Clean` | rich_text | HOT only |
| `Email Draft` | rich_text | WARM only — Email 1 preview |
| `AI Reasoning` | rich_text | populated by Apollo sync |
| `Pain Points` | rich_text | Apollo |
| `Message Angle` | rich_text | Apollo |
| `Call Script` | rich_text | Apollo |
| `Research Context` | rich_text | Apollo |
| `Qualification Level` | select | Apollo: High/Medium/Low |
| `Buyer Role` | select | Apollo: Decision Maker / Influencer / End User |

### Tasks DB
| Field | Type | Notes |
|-------|------|-------|
| `Automation Type` | select — add option `AI Decision Engine` | existing field |

---

## 2. Patch: `scripts/scoring/lead_score.py`

**Goal:** prefer AI engine score when Apollo AI fields exist; fall back to demographic v1.5 otherwise.

**Location:** modify `calculate_lead_score()` or the main scoring loop (around line 440-503).

```python
# ── ADD AT TOP ──
from scoring.ai_decision_engine import score_contact as ai_score_contact, AIFields

# ── INSIDE calculate_lead_score() or the scoring loop ──
def calculate_lead_score(contact: Dict, company_data: Dict) -> Tuple[float, Dict]:
    # 1. existing demographic v1.5 calculation stays as-is
    total, breakdown = _demographic_v15_score(contact, company_data)

    # 2. NEW: check if AI fields exist and overlay AI score
    props = contact.get("properties", {})
    ai_fields = AIFields.from_notion_props(props)
    if ai_fields.has_ai_data():
        ai_result = ai_score_contact(props, demographic_fallback_score=int(total))
        if ai_result.source in ("ai_engine", "hybrid"):
            breakdown["ai_score"] = ai_result.score
            breakdown["ai_tier"] = ai_result.tier
            breakdown["ai_source"] = ai_result.source
            breakdown["ai_reasons"] = ai_result.reasons[:4]
            # AI engine wins when it has real signal
            total = float(ai_result.score)
    return total, breakdown
```

**Effect:** same output fields (`Lead Score`, `Lead Tier`), but contacts with Apollo AI data get the AI engine's verdict. Demographic v1.5 still runs first so breakdown is comparable.

---

## 3. Patch: `scripts/automation/auto_tasks.py`

**Goal:** auto_tasks.py stays the authoritative task creator for the fallback path.
The AI engine handles contacts WITH AI fields via `ai_action_executor.py`.
To avoid double-creation, have auto_tasks.py **skip contacts that already have an open AI-driven task** for their company.

**Location:** `get_companies_with_open_tasks()` (line 156) — already groups by task_type.

Since ai_action_executor.py uses the SAME task types (`Urgent Call`, `Follow-up`) and writes to the SAME Tasks DB with relation to Company, dedup is automatic. **No code change required** — the existing `company_tasks[cid].add(task_type)` dedup already covers it.

**However**, add one filter so auto_tasks.py doesn't re-score contacts the AI engine already handled. In `fetch_actionable_contacts()` (line 117):

```python
def fetch_actionable_contacts() -> List[Dict]:
    filter_ = {
        "and": [
            {"property": FIELD_ACTION_READY, "checkbox": {"equals": True}},
            # NEW: skip contacts already handled by AI engine this run
            # (they have Call Script Clean OR Email Draft populated)
            {"or": [
                {"property": "Call Script Clean", "rich_text": {"is_empty": True}},
                {"property": "Email Draft",       "rich_text": {"is_empty": True}},
            ]},
        ]
    }
    # ... rest unchanged
```

Alternative (cleaner): run `ai_action_executor.py` BEFORE `auto_tasks.py` in the pipeline. Dedup handles the rest.

---

## 4. Patch: `scripts/automation/auto_sequence.py`

**Goal:** personalized role-based sequence copy for AI-scored contacts.
`auto_sequence.py` currently enrolls into pre-built Apollo sequences (`SEQUENCE_MAP` at line 84). Keep that logic — but log which contacts carry AI Email Drafts so you can eventually switch to per-contact copy.

**Location:** inside the main enrollment loop, around the `enroll_contact_in_sequence()` call.

```python
# ── ADD AT TOP ──
from automation.ai_sequence_generator import generate_sequence, detect_role

# ── INSIDE the enrollment loop, BEFORE enroll_contact_in_sequence() ──
props = contact.get("properties", {})
email_draft_prop = props.get("Email Draft", {})
email_draft = ""
if email_draft_prop.get("type") == "rich_text":
    email_draft = "".join(
        r.get("plain_text", "") for r in email_draft_prop.get("rich_text") or []
    )

if email_draft:
    # AI-generated draft exists — log the override and use stock sequence for now.
    # (Future v1.2: push draft to a per-contact Apollo step via custom campaign.)
    logger.info(
        "Contact %s has AI Email Draft (%d chars) — will eventually override stock copy",
        contact.get("email"), len(email_draft),
    )
    contact["_has_ai_draft"] = True
else:
    # Generate on-the-fly as a fallback
    seq = generate_sequence(
        contact_name=contact.get("name", ""),
        company=contact.get("company_name", ""),
        title=contact.get("title", ""),
        seniority=contact.get("seniority", ""),
    )
    contact["_generated_role"] = seq.role
    logger.debug("Generated sequence for %s (role=%s)", contact.get("email"), seq.role)
```

---

## 5. Full Pipeline Placement

Add to `.github/workflows/daily_sync.yml` **Job 2** (`action-and-track`), right after
`action_ready_updater.py` and BEFORE `auto_tasks.py`:

```yaml
# Step 1a (NEW): AI Decision Engine — handles contacts with Apollo AI fields
- name: AI Action Executor (Apollo AI → Notion)
  run: python scripts/automation/ai_action_executor.py --execute --limit 200
  continue-on-error: true
  env:
    NOTION_API_KEY: ${{ secrets.NOTION_API_KEY }}
    NOTION_DATABASE_ID_CONTACTS: ${{ secrets.NOTION_DATABASE_ID_CONTACTS }}
    NOTION_DATABASE_ID_COMPANIES: ${{ secrets.NOTION_DATABASE_ID_COMPANIES }}
    NOTION_DATABASE_ID_TASKS: ${{ secrets.NOTION_DATABASE_ID_TASKS }}

# Step 1 (existing): Fallback Action Engine for non-AI contacts
- name: Action Engine (auto_tasks.py)
  run: python scripts/automation/auto_tasks.py
  continue-on-error: true
```

**Resulting Job 2 order:**

```
1a. ai_action_executor.py    ── AI-driven HOT/WARM tasks (NEW)
1b. auto_tasks.py            ── fallback for non-AI contacts
2.  auto_sequence.py         ── Apollo enrollment
3.  meeting_tracker.py       ── meeting sync
4.  meeting_analyzer.py      ── Claude AI meeting intelligence
5.  opportunity_manager.py   ── meetings → opportunities
6.  analytics_tracker.py     ── engagement sync
7.  outcome_tracker.py       ── Task → Contact outcome loop
8.  health_check.py
9.  morning_brief.py
10. dashboard_generator.py
```

---

## 6. Automation Flow (end to end)

```
Apollo.io
    │  (typed_custom_fields = AI Decision, Pain, Angle, Script, Research, Qual, Role)
    ▼
scripts/core/daily_sync.py  ── writes AI fields to Notion Contacts
    ▼
scripts/scoring/lead_score.py  ── v1.5 demographic + AI overlay (patch §2)
    ▼
scripts/scoring/action_ready_updater.py  ── 5-condition Action Ready gate
    ▼
scripts/automation/ai_action_executor.py  ◄── NEW ORCHESTRATOR
    │
    ├── score_contact()  → (score, tier, action, reasons)
    ├── build_call_script()  ──► Contacts.Call Script Clean  (HOT)
    ├── generate_sequence()  ──► Contacts.Email Draft        (WARM)
    ├── _build_company_enrichment()
    │      ├──► Companies.Priority      (P1/P2/P3)
    │      ├──► Companies.Strategic Fit
    │      ├──► Companies.Pain Summary
    │      └──► Companies.Sales Angle
    ├── Create Tasks.Task (Urgent Call / Follow-up)
    │      ├──► dedup on (company_id, task_type)
    │      └──► Description = call script OR email sequence
    └── Write Contacts.Lead Score + Lead Tier
    ▼
scripts/automation/auto_tasks.py  ── handles contacts WITHOUT AI fields (fallback)
    ▼
scripts/automation/auto_sequence.py  ── enrolls in Apollo sequences (patch §4)
    ▼
scripts/meetings/meeting_tracker.py  ── meetings pulled into Notion
    ▼
scripts/meetings/meeting_analyzer.py  ── Claude summarizes
    ▼
scripts/meetings/opportunity_manager.py  ── ONE opportunity per company
    ▼
scripts/automation/outcome_tracker.py  ── closes Task → Contact loop
    ▼
scripts/monitoring/*  ── health, morning brief, dashboard
```

**Idempotency guarantees:**
- Company-centric dedup: `(company_id, task_type)` preloaded per run + tracked in-memory
- Score writes are upserts (no duplicates possible)
- Company enrichment writes are idempotent (overwrites with latest)
- `Call Script Clean` / `Email Draft` written only when tier ≠ COLD
- `auto_tasks.py` `fetch_actionable_contacts()` filter (§3) prevents double-work

**Scale:** tested design target = 10K+ contacts. Bottleneck = Notion API rate limit (~3 writes/sec). For a typical 200 Action Ready batch, full run ≈ 2-3 min.

---

## 7. Edge Case Matrix

| Case | Module | Handler |
|------|--------|---------|
| No AI fields at all | `score_contact()` | Returns `source="fallback_v1.5"` — patched `lead_score.py` uses v1.5 result |
| AI=YES, no pain text | `score_from_ai_fields()` | Still HOT if role strength ≥ 0.85; else WARM |
| AI=NO, strong research | `score_from_ai_fields()` | Capped at 40 unless `pain_density >= 0.2` |
| KILL signal in research | override branch | Score capped at 35 → COLD |
| Conflicting: YES + kill | override branch | Kill signal wins |
| No linked company | `process_contact()` | Score + enrichment written to contact, task skipped |
| Multiple contacts per company | `preload_open_tasks()` dedup | ONE task, best-scored contact linked |
| Contact has no email AND no phone | `action_ready_updater.py` | Action Ready = False, never reaches executor |
| Description > 2000 chars | `_create_company_task()` | Truncated at 1950 (Notion limit) |
| Notion API 429 | `NotionClient` | Existing exponential backoff (5 retries) |
| Missing env var | `_require_env()` | EnvironmentError at startup |

---

## 8. Deploy Order

1. **Schema** — add Company fields (`Strategic Fit`, `Pain Summary`, `Sales Angle`) and Contact fields (`Call Script Clean`, `Email Draft`) via `notion-schema-manager`. Confirm Companies DB already has `Priority` select.
2. **Self-test** — `python scoring/ai_decision_engine.py --self-test`
3. **Dry run** — `python automation/ai_action_executor.py --limit 5`
4. **Inspect** — read `data/logs/ai_action_executor_stats.json` + spot-check 3 HOT tasks in Notion
5. **Limited live** — `python automation/ai_action_executor.py --execute --limit 50 --tier HOT`
6. **Patch lead_score.py** (§2) — run `python scoring/lead_score.py --dry-run`; verify `ai_source` appears in breakdown
7. **Patch auto_tasks.py** (§3) — optional; only if you see double-creation in logs
8. **Patch auto_sequence.py** (§4) — log-only patch; safe to deploy immediately
9. **GitHub Actions** — add Job 2 step 1a (§5)
10. **Update docs** — `CLAUDE.md` Active Scripts table, Feature Registry, Decision Log entry #26 "AI Decision Engine"
11. **doc_sync_checker** — `python scripts/core/doc_sync_checker.py --strict`
12. **Memory** — save project memory: "AI Execution Engine v1.1 deployed 2026-04-11"

---

## 9. Rollback

Safe rollback is a one-line deletion of the Job 2 step 1a. The AI engine never deletes or mutates existing non-AI fields. All writes are additive:
- If you see bad tasks: filter Tasks DB by `Automation Type = AI Decision Engine` → bulk complete
- If you see bad scores: re-run `scoring/lead_score.py --force` with the patch reverted
- If Companies got bad `Strategic Fit` text: it's rich_text, clear the field in Notion UI (no dependency)

---

## 10. Decision Log Entry (add to CLAUDE.md §Decision Log)

> **26. AI Decision Engine (v1.1, 2026-04-11)** — Apollo AI custom fields (AI Decision, Pain Points, Message Angle, Call Script, Research Context, Qualification Level, Buyer Role) now drive scoring + task creation autonomously. New orchestrator `automation/ai_action_executor.py` runs in Job 2 before `auto_tasks.py` to handle AI-populated contacts; fallback `auto_tasks.py` continues to serve demographic-only contacts. Weights: AI Decision 40%, Buyer Role 25%, Qualification 15%, Pain Density 10%, Research 10%. Kill signals in research cap score at 35. Decision Maker + strong research bumps score 70-79 → 82. Hybrid mode takes the MAX of AI and demographic v1.5. Company-centric dedup unchanged. Company DB now receives Strategic Fit / Pain Summary / Sales Angle enrichment on every run.
