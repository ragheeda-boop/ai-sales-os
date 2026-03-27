---
name: shared-sales-os-rules
description: "Foundation rules for AI Sales OS. This skill is the shared truth layer that every other skill depends on. Use it automatically whenever working with AI Sales OS data — syncing, scoring, creating tasks, analyzing pipeline, checking data quality, or touching Notion databases. If any AI Sales OS skill is active, this one should be too."
---

# AI Sales OS — Shared Operating Rules

These rules apply across every operation in AI Sales OS. They represent hard-won knowledge from real data validation against Notion and Apollo. Follow them because they prevent real bugs that have actually occurred in this system.

## System Architecture

```
Apollo.io (44,875 contacts, 15,407 companies)
    ↓
Python Scripts (daily_sync.py v2.1 → lead_score.py → action_ready_updater.py → auto_tasks.py → health_check.py)
    ↓
Notion CRM (7 databases, HOT/WARM/COLD views)
    ↓
GitHub Actions (daily at 7 AM KSA / 04:00 UTC)
```

All scripts live in: `💻 CODE/Phase 3 - Sync/`

## Codebase Files

| Script | Purpose | Status |
|--------|---------|--------|
| `daily_sync.py` | Apollo → Notion sync (3 modes: incremental/backfill/full) | ACTIVE |
| `lead_score.py` | Score calculator + Lead Tier writer | ACTIVE |
| `constants.py` | All field names, thresholds, SLA hours, seniority normalization | ACTIVE |
| `notion_helpers.py` | Shared Notion API utilities | ACTIVE |
| `action_ready_updater.py` | 5-condition gating for Action Ready checkbox | ACTIVE |
| `auto_tasks.py` | SLA-based task creator for Action Ready contacts | ACTIVE |
| `health_check.py` | Post-pipeline health validator | ACTIVE |

## Data Reality Constraints

These are facts confirmed by direct Notion API queries — not assumptions:

- **Intent Score is empty on 100% of contacts.** `Primary Intent Score` and `Secondary Intent Score` fields exist but contain no values. This is likely an Apollo plan limitation. The scoring formula gives Intent 10% weight, so this effectively means scoring runs on 90% of its intended inputs. Do not assume Intent data exists.

- **Stage field exists but is largely empty.** The `Stage` select field is present in both schema and code (`daily_sync.py` line 560 writes it), but Apollo returns stage data inconsistently. Roughly 85% of contacts have Stage = empty. Do not rely on Stage as a definitive filter without checking.

- **Seniority has duplicate values.** Both `"C-Suite"` and `"C suite"` exist as separate select options in Notion. The code has `_normalize_seniority()` and `SENIORITY_NORMALIZE` dict in `constants.py` to handle this, but any new code must also treat them as equivalent. The canonical value is `"C-Suite"` (with hyphen).

- **"Do Not Contact" in Outreach Status is different from "Do Not Call" checkbox.** Both exist. Both must be checked before any automation. `OUTREACH_BLOCKED` in `constants.py` contains `{"Do Not Contact", "Bounced", "Bad Data"}`.

- **56% of HOT contacts have Score = 100 exactly.** This ceiling effect comes from high engagement + C-Suite seniority with zero Intent. It's not a bug — it's a consequence of available data. Be aware when analyzing score distributions.

- **Tasks DB uses `status` type, NOT `select`.** The Status field in Tasks uses `{"status": {"name": "Not Started"}}` format, not `{"select": ...}`. Using the wrong format will silently fail.

## Scoring Formula (v1.1 — Current)

```
Score = Intent(10%) + Engagement(10%) + CompanySize(45%) + Seniority(35%)
```

The weights are intentionally skewed toward Size and Seniority because Intent and Engagement data is sparse. Do not switch to v2.0 weights until Intent data is actually populated.

| Tier | Score | SLA |
|------|-------|-----|
| HOT | >= 80 | 24 hours |
| WARM | 50-79 | 48 hours |
| COLD | < 50 | No action |

## Action Ready Conditions (All 5 Must Be True)

A contact becomes Action Ready only when:
1. Lead Score >= 50
2. Do Not Call = False
3. Outreach Status NOT in {Do Not Contact, Bounced, Bad Data}
4. Stage is NOT "Customer" or "Churned"
5. Has at least one contact method (email or phone)

## Primary Key Rules

- **Companies:** Apollo Account ID is the primary key. Domain is validation.
- **Contacts:** Apollo Contact ID is the primary key. Email is validation.
- NEVER create duplicates when Apollo ID exists — always update.
- NEVER match by name alone.

## Data Protection Rules

1. Never overwrite manual data (Owner, Status, Notes, Stage set by humans)
2. Only write engagement booleans (Email Sent, Replied, etc.) if Apollo explicitly returns the field — prevents overwriting manual True with False
3. No orphan contacts — every contact must link to a company
4. Companies sync before contacts (contacts reference company page IDs)
5. Never invent data for empty fields

## Constants Reference

All field names live in `constants.py`. Key exports:
- `FIELD_*` constants for every Notion property name
- `SCORE_HOT = 80`, `SCORE_WARM = 50`
- `SLA_HOT_HOURS = 24`, `SLA_WARM_HIGH_HOURS = 48`, `SLA_WARM_HOURS = 168`
- `SENIORITY_NORMALIZE` dict for normalizing Apollo seniority strings
- `OUTREACH_BLOCKED` set for filtering unsafe contacts

When writing new code, always import from `constants.py` — never hardcode field names.
