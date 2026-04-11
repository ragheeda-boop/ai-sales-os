# AI Execution Engine v1.0 — Design & Deployment Spec

**Status:** CODE COMPLETE — pending first dry-run
**Version:** 1.0 | 2026-04-11
**Owner:** Ragheed
**Modules added:**
`scripts/scoring/ai_decision_engine.py`,
`scripts/automation/call_script_builder.py`,
`scripts/automation/ai_sequence_generator.py`,
`scripts/automation/ai_action_executor.py`

---

## 1. Purpose

Convert Apollo AI Custom Fields into **fully automated sales execution**.
No human decides who to call, what to say, or when to send a follow-up.

Input: Apollo AI fields on a Notion contact.
Output: Lead Score, Tier, company-level Task with ready-to-read call script
or email sequence, and Company priority (P1/P2/P3) — all written back to Notion.

---

## 2. Execution Flow (text diagram)

```
Apollo AI Fields (on Contact in Notion)
        │
        ▼
scripts/core/daily_sync.py        [existing — already pulls Apollo AI fields]
        │
        ▼
scripts/scoring/lead_score.py     [existing — demographic v1.5 baseline]
        │
        ▼
scripts/scoring/action_ready_updater.py   [existing — 5-condition gate]
        │
        ▼
scripts/automation/ai_action_executor.py  ◄── NEW ORCHESTRATOR
        │
        ├──► ai_decision_engine.score_contact(props, demographic_fallback)
        │         │
        │         ├── AIFields.from_notion_props()
        │         ├── score_from_ai_fields()   → ScoreResult
        │         ├── hybrid_score()           → combine with v1.5
        │         └── handle_edge_cases()      → DM demotion, kill signals
        │
        ├──► HOT? → call_script_builder.build_call_script()
        │             └── opening / discovery / pitch / objections / CTA
        │
        ├──► WARM? → ai_sequence_generator.generate_sequence()
        │             └── role-detected 3-email sequence
        │
        ├──► company-level dedup (company_id, task_type)
        │
        ├──► create Task in Notion (Task Title, Description, Due, Priority, relations)
        │
        ├──► update Contact: Lead Score + Lead Tier
        │
        └──► update Company: Priority (P1/P2/P3)
```

---

## 3. Decision Engine Rules

### Inputs (Apollo AI fields on Contact)
| Field | Type | Role in engine |
|-------|------|----------------|
| AI Decision | YES/NO | 40-point component |
| Buyer Role | Decision Maker / Influencer / etc. | 25-point component |
| Qualification Level | High/Med/Low or 1-5 | 15-point component |
| Pain Points | text | 10-point component (keyword density) |
| Research Context | text | 10-point + kill-signal override |
| AI Reasoning | text | merged into pain density |
| Message Angle | text | used by sequence + call builders |
| Call Script | text | used by call_script_builder |

### Weights (AI_WEIGHTS in ai_decision_engine.py)
```
AI Decision    40%
Buyer Role     25%
Qualification  15%
Pain Density   10%
Research       10%
───────────── 100%
```

### Tier rules (order matters)
```
AI=YES + Decision Maker                  → HOT
AI=YES + score >= 80                     → HOT
AI=YES + other role                      → WARM
AI=NO  + score < 50                      → COLD
score >= 80                              → HOT
score >= 50                              → WARM
otherwise                                → COLD
```

### Overrides
| Rule | Effect |
|------|--------|
| KILL signal in research context (`not a fit`, `bankrupt`, `competitor`, …) | score capped at 35 → COLD |
| AI=NO + low pain density | score capped at 40 → COLD |
| DM + strong research (score 70-79) | bumped to 82 → HOT |
| Role strength < 0.6 + tier=HOT | demoted HOT → WARM (`handle_edge_cases`) |

### Fallback
If a contact has **no** AI fields, `score_contact()` returns
`source="fallback_v1.5"` so `scoring/lead_score.py` remains authoritative.

### Hybrid
When both exist, `hybrid_score()` takes the higher of the two and keeps the
AI engine's reasoning. This prevents either engine from silently burying a
real lead.

---

## 4. Action Engine Rules

Driven by `decide_action(tier)` in `ai_decision_engine.py`:

| Tier | Task Type | SLA | Priority | Description content |
|------|-----------|-----|----------|---------------------|
| HOT  | `Urgent Call` | 24h | Critical | Full call script (opening, discovery, pitch, objections, CTA) |
| WARM | `Follow-up`   | 48h | High     | Role-detected 3-email sequence (Email 1/2/3) |
| COLD | — | — | Low | Score written only, no task |

**Company-centric dedup** (matches `auto_tasks.py` v2.0):
- Key = `(company_id, task_type)`
- Preloaded once per run from all open tasks
- Also tracks in-run creations to prevent double-creates inside one batch

**Task Owner:** inherited via the existing `auto_tasks.py` flow — this
executor only creates the task; the owner comes from Primary Company Owner
(Decision #18). For manual override, set owner in the Notion UI.

---

## 5. Call Script Structure (`call_script_builder.py`)

Transforms raw AI `Call Script` + `Pain Points` into:

1. **OPENING (15s)** — extracted from AI script OR template fallback
2. **DISCOVERY** — 3 questions tied to the #1 pain
3. **PAIN → VALUE PITCH** — merges Message Angle + pain + company
4. **OBJECTION HANDLING** — 5 pre-written responses (budget, timing, competitor, not interested, "just send email")
5. **CTA** — HOT: ask for calendar slot | WARM: ask permission for Loom
6. **SHORT VERSION** — voicemail / <30 sec variant

Output written to Task.Description as Markdown.

---

## 6. Sequence Engine (`ai_sequence_generator.py`)

Role detection via regex over `Title + Seniority + Buyer Role`:
```
CEO / CFO / COO / CTO / Sales / Legal / Generic
```
Each role has its own **angle**, **metric**, and **pain reframe** in `ROLE_HOOKS`.

Output: 3 emails (Intro / Value Reminder / Break-up) wrapped in `EmailSequence`.
Markdown preview goes into Task.Description for WARM leads.

---

## 7. Notion Field Mapping

### Contacts DB — written by executor
| Field | Source |
|-------|--------|
| `Lead Score` (number) | `ScoreResult.score` |
| `Lead Tier` (select) | `ScoreResult.tier` |
| `Action Ready` (checkbox) | [already written by action_ready_updater.py] |

### Tasks DB — created by executor
| Field | Value |
|-------|-------|
| `Task Title` | `[TIER] {task_type} — company {id8}` |
| `Task Type` | `Urgent Call` / `Follow-up` |
| `Priority` | `Critical` / `High` |
| `Status` | `Not Started` (status type) |
| `Due Date` | `now + SLA hours` |
| `Company` (relation) | linked company |
| `Contact` (relation) | best-scored contact at company |
| `Description` (rich_text) | Markdown from call_script or sequence |
| `Auto Created` (checkbox) | `True` |
| `Automation Type` (select) | `AI Decision Engine` |

### Companies DB — written by executor
| Field | Value |
|-------|-------|
| `Priority` (select) | `P1` (HOT) / `P2` (WARM) / `P3` (COLD) |

---

## 8. Edge Cases (handled)

| Case | Handling |
|------|----------|
| Missing AI fields | `score_contact` returns fallback_v1.5 source; caller uses demographic score |
| AI=YES but non-DM | Engine still issues WARM, `handle_edge_cases` demotes HOT→WARM if role<0.6 |
| AI=NO but strong pain signals | Stays COLD unless pain density ≥ 0.2 AND research has triggers |
| No linked company | Score written, task skipped (stats.tasks_skipped_not_ready++) |
| Open task already exists for (company, type) | Dedup cache skips; stats.tasks_skipped_dedup++ |
| Conflicting signals (YES+kill signal) | Kill signal wins, score capped at 35 |
| Duplicate contacts | Company-centric dedup ensures ONE task per company per type |
| Description > 2000 chars | Truncated at 1950 (Notion limit) |

---

## 9. CLI

```bash
# Dry run (default — no writes)
python automation/ai_action_executor.py

# Execute — all Action Ready contacts
python automation/ai_action_executor.py --execute

# HOT only
python automation/ai_action_executor.py --execute --tier HOT

# First 20 (testing)
python automation/ai_action_executor.py --execute --limit 20

# Self-test decision engine only
python scoring/ai_decision_engine.py --self-test

# Preview call script / sequence standalone
python automation/call_script_builder.py
python automation/ai_sequence_generator.py
```

Env vars required (hard fail if missing):
`NOTION_API_KEY`, `NOTION_DATABASE_ID_CONTACTS`, `NOTION_DATABASE_ID_COMPANIES`, `NOTION_DATABASE_ID_TASKS`.

---

## 10. Pipeline Integration

Insert as a NEW step in `.github/workflows/daily_sync.yml` — Job 2, right
after `action_ready_updater.py` and before `auto_tasks.py`:

```yaml
- name: AI Action Executor (Apollo AI → Notion)
  run: python scripts/automation/ai_action_executor.py --execute --limit 200
  continue-on-error: true
```

**Ordering rationale:** runs BEFORE `auto_tasks.py` so AI-driven tasks take
dedup priority. The fallback `auto_tasks.py` then handles contacts without AI
fields using the existing v1.5 demographic path.

---

## 11. Deployment Checklist

- [ ] `pip install` — no new dependencies required (uses existing `notion_helpers`)
- [ ] Verify Notion Contact DB has fields: `AI Decision`, `AI Reasoning`, `Pain Points`, `Message Angle`, `Call Script`, `Research Context`, `Qualification Level`, `Buyer Role` — add via `notion_schema_manager` skill if missing
- [ ] Verify Companies DB has `Priority` (select) with values P1/P2/P3
- [ ] Verify Tasks DB has `Automation Type` select option `AI Decision Engine`
- [ ] Run `python scripts/scoring/ai_decision_engine.py --self-test` — sanity check
- [ ] Run `python scripts/automation/ai_action_executor.py --limit 5` (dry run)
- [ ] Inspect first 5 results in `data/logs/ai_action_executor_stats.json`
- [ ] Spot-check 2 HOT tasks manually — does the call script read like a rep would use it?
- [ ] Run `python scripts/automation/ai_action_executor.py --execute --limit 50`
- [ ] Add step to `daily_sync.yml` Job 2
- [ ] Update `CLAUDE.md`: Active Scripts table, Feature Registry, Decision Log entry
- [ ] Run `python scripts/core/doc_sync_checker.py --strict`

---

## 12. Rollback

Safe to disable by removing the `daily_sync.yml` step. Contacts revert to
the legacy `auto_tasks.py` path. No schema changes are destructive — all
fields written are either new or already owned by the system.

To undo tasks created by this engine:
```python
# In Notion query: Automation Type = "AI Decision Engine" AND Status = "Not Started"
# Bulk complete or delete.
```

---

## 13. Future (v1.1+)

- Pull AI fields live from Apollo `typed_custom_fields` during the same run
  to avoid dependence on daily_sync lag
- Add Slack notification for every new HOT task
- Feed calibration results back into `ai_decision_engine.AI_WEIGHTS`
- Extend sequence generator to hit Apollo API and actually enroll (currently
  the sequence is a **preview** pasted into task description — enrollment
  remains `auto_sequence.py`'s job)
