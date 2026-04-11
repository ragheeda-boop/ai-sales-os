# AI Sales Actions — Integration & Validation Guide

**Date:** 2026-04-11
**Status:** Code complete, pending dry-run validation
**Owner:** Ragheed

---

## 1. What this is

Apollo.io now populates a single **account-level rich_text field** on every
qualified account called **`AI Sales Actions`**. The block is semi-structured:

```
Segment: Enterprise FinTech
Fit: High
Priority: P1
Urgency: High
Signal: Series B raise, hiring CFO
Pain: Manual reconciliation, audit exposure
Target Role: CFO
Action: Call
Tone: Direct, high-urgency
Call Hook:
- You just raised Series B — reconciliation will break in 90 days
- New CFO means process rebuild is on the table right now
- We cut audit prep 70% for a team your size in 6 weeks
Email:
  Subject: Reconciliation bottleneck post-Series B
  Opening: Ahmed — saw the Series B close. Congrats.
  Pain: Scaling from 80 → 200 people breaks Excel reconciliation within 90 days.
  Value: We cut audit prep by 70% for FinTechs your size in under 6 weeks.
  CTA: Worth a 15-min call Thursday?
```

Our job is not to generate this — Apollo does. Our job is to **parse it,
persist the structured fields, and route our automation off of it** without
touching the company-centric v5.0 model.

---

## 2. Files added

| Path | Purpose |
|------|---------|
| `scripts/core/ai_sales_actions_parser.py` | Stdlib-only parser (pure function, zero deps). Tolerant to bullet variants, nested Email block, whitespace, case. |
| `scripts/enrichment/ai_sales_actions_enricher.py` | Notion reader/writer. Scans Companies where `AI Sales Actions` is populated, parses, writes sub-fields to Company, propagates email copy + call hook to linked Contacts. Idempotent via `AI Sales Actions Parsed At` vs `last_edited_time`. |

## 3. Files patched (surgical)

| Path | Change |
|------|--------|
| `scripts/core/constants.py` | +19 constants: `FIELD_AI_*` names, `AI_ACTION_*` / `AI_PRIORITY_*` canonical values, `AI_PRIORITY_BOOST` / `AI_FIT_BOOST` / `AI_SCORE_BOOST_MAX`. No existing constants touched. |
| `scripts/automation/auto_tasks.py` | +`preload_company_ai_fields()` bulk reader. `create_company_task()` takes optional `ai_data` and (a) overrides `Priority` via `AI Priority`, (b) appends Apollo reasoning to `Description`, (c) sets `Automation Type = "AI Sales Actions"` when the override fires. Main loop skips companies where `AI Action Type = None`; skips Email/Sequence actions for non-HOT contacts (those are auto_sequence's job). |
| `scripts/automation/auto_sequence.py` | +`preload_company_ai_actions()` bulk reader. Main loop skips `AI Action Type = None` (do-not-contact) and `AI Action Type = Call` (handled by auto_tasks). Logs AI Email Draft presence for future per-contact copy override. |
| `scripts/scoring/lead_score.py` | `fetch_company_data()` now also reads `AI Priority` + `AI Fit`. `calculate_lead_score()` applies an additive, capped boost (max `AI_SCORE_BOOST_MAX = 12`) on top of v1.5 formula. Clamped to 0-100 after boost. Breakdown includes `ai_priority`, `ai_fit`, `ai_boost`. |

**No script was rewritten. No existing field was renamed. No company-centric
dedup or ownership logic was touched.**

---

## 4. New Notion properties required

Add before first run via `notion-schema-manager` skill or manually.

### Companies DB

| Field | Type | Values |
|-------|------|--------|
| `AI Sales Actions` | rich_text | raw Apollo block (may already exist) |
| `AI Priority` | select | `P1` / `P2` / `P3` |
| `AI Fit` | select | `High` / `Medium` / `Low` |
| `AI Urgency` | select | `High` / `Medium` / `Low` |
| `AI Segment` | rich_text | free-text |
| `AI Signal` | rich_text | free-text |
| `AI Pain Summary` | rich_text | free-text |
| `AI Target Role` | rich_text | free-text |
| `AI Action Type` | select | `Call` / `Email` / `Sequence` / `None` |
| `AI Tone` | rich_text | free-text |
| `AI Sales Actions Parsed At` | date | set by enricher |

### Contacts DB

| Field | Type | Notes |
|-------|------|-------|
| `AI Call Hook` | rich_text | bullets joined with • |
| `AI Email Subject` | rich_text | from Apollo Email block |
| `AI Email Opening` | rich_text | |
| `AI Email Pain` | rich_text | |
| `AI Email Value` | rich_text | |
| `AI Email CTA` | rich_text | |

### Tasks DB

| Field | Type | Notes |
|-------|------|-------|
| `Automation Type` | select — **add option** `AI Sales Actions` | existing field |

---

## 5. Example — parsed output

Input is the block above. `parse_ai_sales_actions_typed()` returns a
`ParsedAISalesActions` whose `as_dict()` is:

```json
{
  "segment": "Enterprise FinTech",
  "fit": "High",
  "priority": "P1",
  "urgency": "High",
  "signal": "Series B raise, hiring CFO",
  "pain": "Manual reconciliation, audit exposure",
  "target_role": "CFO",
  "action": "Call",
  "tone": "Direct, high-urgency",
  "call_hook": [
    "You just raised Series B — reconciliation will break in 90 days",
    "New CFO means process rebuild is on the table right now",
    "We cut audit prep 70% for a team your size in 6 weeks"
  ],
  "email_subject": "Reconciliation bottleneck post-Series B",
  "email_opening": "Ahmed — saw the Series B close. Congrats.",
  "email_pain": "Scaling from 80 → 200 people breaks Excel reconciliation within 90 days.",
  "email_value": "We cut audit prep by 70% for FinTechs your size in under 6 weeks.",
  "email_cta": "Worth a 15-min call Thursday?",
  "is_valid": true
}
```

**Edge-case behaviour (self-test in the parser):**

- Lowercase keys (`priority:`, `fit -`) → still parsed.
- `Action: Send Email` → normalized to canonical `Email`.
- `Fit: strong` → normalized to `High`.
- Missing Email block → email_* fields empty, `is_valid` still true if ≥3 other fields present.
- Malformed bullets (`•`, `–`, `1.`, `-`) → all stripped identically.

---

## 6. Example — task payload written by auto_tasks.py

With the enricher populated Company fields `AI Action Type=Call`,
`AI Priority=P1`, `AI Target Role=CFO`, the patched `auto_tasks.py`
produces (for a HOT contact at that company):

```python
{
  "Task Title":    "🔥 URGENT CALL: Acme FinTech — Sarah Al-Qahtani",
  "Task Priority": "Critical",            # overridden from P1 (already Critical here)
  "Status":        "Not Started",
  "Due Date":      "<now + 24h>",
  "Task Type":     "Urgent Call",
  "Automation Type": "AI Sales Actions",   # flipped from "Lead Scoring"
  "Description":
    "Company-level task for Acme FinTech. 3 contact(s) qualify. "
    "Best contact: Sarah Al-Qahtani (Score: 88, Tier: HOT). "
    "Action: CALL via Phone.\n\n"
    "── Apollo AI Sales Actions ──\n"
    "Apollo Action: Call\n"
    "Apollo Priority: P1\n"
    "Urgency: High\n"
    "Target Role: CFO\n"
    "Signal: Series B raise, hiring CFO\n"
    "Pain: Manual reconciliation, audit exposure\n"
    "Call Hooks:\n"
    "• You just raised Series B — reconciliation will break in 90 days\n"
    "• New CFO means process rebuild is on the table right now\n"
    "• We cut audit prep 70% for a team your size in 6 weeks",
  "Company":   { "relation": [...] },
  "Contact":   { "relation": [...] },
  "Task Owner": "Ragheed",
  "Owner Source": "Company Primary"
}
```

---

## 7. auto_sequence.py behaviour

For each Action Ready contact:

| Company `AI Action Type` | Behaviour |
|---|---|
| _empty_ (no AI data) | unchanged — enrolls in stock sequence as before |
| `None` | **skipped** (Apollo said do-not-contact) — counted in `skipped_ai_none` |
| `Call` | **skipped** (auto_tasks handles it) — counted in `skipped_ai_call_only` |
| `Email` / `Sequence` | enrolls in stock sequence; if contact has a propagated `AI Email Subject`, logs `"AI Email Draft present — stock sequence will be used"` so a future v1.2 can swap in per-contact copy |

No Apollo enrollment call was changed. No sender rotation was changed.

---

## 8. lead_score.py boost math

```
base_v1_5 = Intent(10%) + Engagement(10%) + Size(35%) + Seniority(30%) + Industry(15%)

ai_priority_pts = { P1: 8, P2: 4, P3: 0 }[AI Priority] or 0
ai_fit_pts      = { High: 4, Medium: 2, Low: 0 }[AI Fit] or 0
ai_boost        = min(ai_priority_pts + ai_fit_pts, 12)

total = clamp(base_v1_5 + ai_boost, 0, 100)
```

**Why conservative:**

- Max boost = **12 points** — cannot push a COLD (score 35) into HOT on AI
  signal alone. A 35 + 12 = 47 → still WARM-adjacent but not auto-HOT.
- A contact already at 70 becomes 82 with (P1 + High) — consistent with the
  hand-rule "DM + strong research bumps 70-79 → 82" from v1.0 spec.
- Zero boost when AI fields are absent — no regression on demographic-only
  contacts.
- Clamped to 100 — cannot blow past the ceiling.

**Breakdown additions:** `ai_priority`, `ai_fit`, `ai_boost` appear in the
returned breakdown dict so `score_calibrator.py` can see the contribution
separately when it runs its weekly review.

---

## 9. End-to-end flow

```
Apollo.io
  │ AI Sales Actions (raw rich_text on Account)
  ▼
scripts/core/daily_sync.py        [existing — already syncs the raw field]
  ▼
scripts/enrichment/ai_sales_actions_enricher.py   ◄── NEW
  │   parse_ai_sales_actions_typed()
  │   ├──► Companies.{AI Priority, AI Fit, AI Urgency, AI Segment,
  │   │                AI Signal, AI Pain Summary, AI Target Role,
  │   │                AI Action Type, AI Tone, AI Sales Actions Parsed At}
  │   └──► Contacts.{AI Call Hook, AI Email Subject/Opening/Pain/Value/CTA}
  ▼
scripts/scoring/lead_score.py     [patched — conservative boost]
  ▼
scripts/scoring/action_ready_updater.py   [unchanged — 5-condition gate]
  ▼
scripts/automation/auto_tasks.py  [patched — AI Priority override + AI=None skip]
  ▼
scripts/automation/auto_sequence.py  [patched — AI=None/Call skip + draft logging]
  ▼
scripts/meetings/* + scripts/monitoring/*  [unchanged]
```

---

## 10. Deploy order

1. **Schema** — add the Company and Contact fields in §4 via
   `notion-schema-manager`. Add `AI Sales Actions` option to
   `Automation Type` select on Tasks DB.
2. **Parser self-test** — `python scripts/core/ai_sales_actions_parser.py`
   (the `__main__` block prints parsed `clean` / `messy` / `empty` cases).
   Confirm the sample block produces `is_valid: true` and all fields.
3. **Enricher dry-run** — `python scripts/enrichment/ai_sales_actions_enricher.py --limit 5`.
   Inspect log output: each company should print `priority`, `fit`, `action`,
   `hooks`, `email` summary plus the would-update contact count. No writes yet.
4. **Enricher live, small batch** — `python scripts/enrichment/ai_sales_actions_enricher.py --execute --limit 20`.
   Spot-check 3 companies in Notion: AI sub-fields populated? Call Hook
   propagated to their contacts?
5. **lead_score.py dry-run** — `python scripts/scoring/lead_score.py --dry-run`.
   In the logged breakdowns, confirm `ai_boost` is populated (non-zero) for
   contacts at P1/P2 companies and `0.0` elsewhere.
6. **auto_tasks.py dry-run** — `python scripts/automation/auto_tasks.py --dry-run --limit 20`.
   Confirm the log shows `Preloaded AI fields for N companies` and
   `Skipped (AI=None/Email/Seq): X`. Spot the override counter.
7. **auto_sequence.py dry-run** — `python scripts/automation/auto_sequence.py --dry-run --limit 20`.
   Confirm new counters appear in the summary.
8. **Enricher full run** — `python scripts/enrichment/ai_sales_actions_enricher.py --execute`.
9. **Live pipeline run** — one manual GitHub Actions trigger, then inspect:
   - `data/logs/ai_sales_actions_enricher_stats.json`
   - `last_action_stats.json` — look for `ai_overrides_applied > 0`
   - `last_sequence_stats.json` — look for `skipped_ai_call_only > 0`
10. **Add enricher to daily_sync.yml Job 1** between `daily_sync.py` and
    `lead_score.py` (before scoring so the boost has data to work with):

    ```yaml
    - name: AI Sales Actions Enricher
      run: python scripts/enrichment/ai_sales_actions_enricher.py --execute
      continue-on-error: true
      env:
        NOTION_API_KEY: ${{ secrets.NOTION_API_KEY }}
        NOTION_DATABASE_ID_COMPANIES: ${{ secrets.NOTION_DATABASE_ID_COMPANIES }}
        NOTION_DATABASE_ID_CONTACTS: ${{ secrets.NOTION_DATABASE_ID_CONTACTS }}
    ```
11. **Docs** — Update `CLAUDE.md` Active Scripts table + Decision Log
    entry #27 "AI Sales Actions Integration".
12. **doc_sync_checker** — `python scripts/core/doc_sync_checker.py --strict`.

---

## 11. Validation checklist

- [ ] Parser `is_valid` true for the Apollo clean sample.
- [ ] Parser returns empty dict on empty input without raising.
- [ ] Parser tolerates lowercase keys, bullet variants, and missing Email block.
- [ ] Enricher dry-run lists companies without writing.
- [ ] Enricher live writes `AI Priority` + `AI Fit` as select values, not rich_text.
- [ ] Enricher writes `AI Sales Actions Parsed At` (date) on every processed company.
- [ ] Second enricher run with no `--force` skips fresh companies
      (`companies_skipped_fresh > 0`).
- [ ] Enricher propagates `AI Call Hook` to every linked contact.
- [ ] `lead_score.py --dry-run` shows `ai_boost` ≤ 12 in the breakdown.
- [ ] `auto_tasks.py --dry-run` skips companies with `AI Action Type = None`.
- [ ] `auto_tasks.py` task description includes the `── Apollo AI Sales Actions ──` block.
- [ ] `auto_tasks.py` sets `Automation Type = "AI Sales Actions"` when AI Priority overrides.
- [ ] `auto_sequence.py` skips contacts whose company has `AI Action Type = Call`.
- [ ] `auto_sequence.py` logs AI Email Draft presence (doesn't crash on missing field).
- [ ] Company-centric dedup still holds: ONE task per (company, task_type).

---

## 12. Risks & edge cases

| Risk | Mitigation |
|------|------------|
| Malformed `AI Sales Actions` block crashes enricher | Parser never raises — returns empty dict with `is_valid=false`. Enricher increments `companies_skipped_invalid` and moves on. |
| Unknown select value (e.g. `Fit: excellent`) | Parser normalizes via `normalize_fit()` → `"High"`. Unknown value leaves the select unwritten (rich_text still set). |
| Apollo edits the block → parsed snapshot goes stale | `_needs_reparse()` compares `last_edited_time` to `AI Sales Actions Parsed At` and reparses automatically. `--force` bypasses the check. |
| `AI Action Type = Call` at a company where the contact is not DM | auto_tasks still creates the task — we trust Apollo's Company-level Action. If this proves wrong, add a DM check gate in §11 validation. |
| `AI Email Draft` present but enroller still sends stock copy | Logged, not blocking. v1.2 will add per-contact copy override. |
| Scoring double-counts (MUHIDE Fit 100 + AI Fit High) | Not a double-count — MUHIDE Fit flows through `industry_fit * 15%`; AI Fit is additive as an independent Apollo signal. Hard cap of 12 prevents runaway. |
| Unowned companies | Company fields are written regardless of owner. Task creation still requires a Primary Company Owner or Contact Owner fallback (unchanged behaviour). |
| Notion select needs pre-defined options | Adding new values via the API is allowed on unrestricted selects. If the DB was created with restricted options, the add-option step in §10.1 is required before run. |
| Large call hook causes description > 1990 chars | `description_body[:1990]` truncation in `create_company_task`. |
| Contact-level `Company` relation is empty | auto_sequence falls back to the unchanged path (no AI gating possible for that contact). |

---

## 13. Rollback

Safe rollback is a one-line deletion of the enricher step from `daily_sync.yml`.
The AI engine never deletes or mutates existing non-AI fields — all writes are
additive:

- To clear bad AI Priority / AI Fit on Companies: filter by
  `AI Sales Actions Parsed At is not empty` and bulk-clear the select fields
  in the Notion UI.
- To revert scoring: comment out the `total += ai_boost` line in
  `lead_score.py` and run `python scripts/scoring/lead_score.py --force`.
- To revert auto_tasks/auto_sequence: `git revert` the patch commit — the
  `ai_data` parameter is optional with a `None` default, so callers that
  don't pass it behave exactly as pre-patch.

---

## 14. Decision Log entry (add to CLAUDE.md §Decision Log)

> **27. AI Sales Actions Integration (2026-04-11)** — Apollo populates a
> single account-level `AI Sales Actions` rich_text block per qualified
> company. New parser (`scripts/core/ai_sales_actions_parser.py`, stdlib-only)
> turns it into 16 structured fields. New enricher
> (`scripts/enrichment/ai_sales_actions_enricher.py`) writes the parsed
> fields to Companies and propagates Call Hook + Email copy to linked
> Contacts (idempotent via `AI Sales Actions Parsed At` vs `last_edited_time`).
> `auto_tasks.py` now reads `AI Action Type` and skips `None`/`Email`/`Sequence`
> (routed through `auto_sequence.py`); `AI Priority` overrides task priority
> and sets `Automation Type = "AI Sales Actions"`. `auto_sequence.py` skips
> `AI Action Type = None`/`Call`. `lead_score.py` applies an additive,
> capped boost (max 12 points, `P1=8, P2=4; High=4, Medium=2`) on top of
> v1.5 formula. Company-centric dedup unchanged. No script rewritten — all
> edits surgical.
