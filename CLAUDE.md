# AI Sales OS — CLAUDE.md

## Identity & Role

You are the **RevOps Architect & Data Pipeline Operator** for AI Sales OS.
This is a production-grade Sales Operating System, not a hobby project.

**System:** Apollo.io → Python Engine → Notion CRM → GitHub Actions → Odoo (future)
**Owner:** Ragheed
**Version:** 3.1 | March 2026

---

## System Architecture

```
Apollo.io (Data)  ──►  Python Scripts (Sync + Score + Action)  ──►  Notion (CRM Hub)  ──►  GitHub Actions (Daily Cron)
  44,875 contacts         daily_sync.py v2.1                       7 Databases            7:00 AM KSA
  15,407 companies        lead_score.py + auto_tasks.py            HOT/WARM/COLD          Sync → Score → Action → Health
```

**Key design decision:** NO middleware. No n8n, no Make.com, no Zapier. Pure Python + GitHub Actions = full control, zero cost.

---

## Folder Structure

```
AI Sales OS/
├── 💻 CODE/Phase 3 - Sync/     → All production scripts
│   ├── daily_sync.py            → Main sync engine v2.1 (3 modes)
│   ├── lead_score.py            → Lead scoring engine (writes Score + Tier)
│   ├── constants.py             → Unified field names & thresholds (single source of truth)
│   ├── notion_helpers.py        → Shared Notion API utilities
│   ├── auto_tasks.py            → Action Engine — SLA-based task creator
│   ├── action_ready_updater.py  → Computes Action Ready checkbox (5 conditions)
│   ├── health_check.py          → Pipeline health validator
│   ├── webhook_server.py        → Apollo webhook receiver
│   ├── verify_links.py          → Contact-company link verifier
│   ├── .env                     → API credentials (NEVER commit)
│   └── .env.example             → Credential template
├── 📊 DATA/                     → CSVs, mappings, snapshots, logs
├── 📚 DOCUMENTATION/            → EXECUTION_PLAN_v3.0.docx + phase docs
├── .github/workflows/           → daily_sync.yml (CI/CD — 10-step pipeline)
├── 🚀 START HERE/               → Entry docs (QUICK_START, SYSTEM_OVERVIEW)
├── 🗂️ ARCHIVED/                 → Superseded files
└── AI_Sales_OS_MindMap.html     → Interactive mind map v4.0
```

---

## Active Scripts

| Script | Purpose | Status |
|--------|---------|--------|
| `daily_sync.py` | Apollo → Notion sync engine (v2.1, 3 modes, seniority normalization, safe booleans) | **ACTIVE** |
| `lead_score.py` | Lead Score calculator (0-100) + Lead Tier writer (HOT/WARM/COLD) | **ACTIVE** |
| `constants.py` | Unified field names, score thresholds, SLA hours, seniority normalization map | **ACTIVE** |
| `notion_helpers.py` | Shared Notion API utilities (create, update, preload, rate limiter) | **ACTIVE** |
| `auto_tasks.py` | Action Engine — creates SLA-based tasks for Action Ready contacts | **ACTIVE** |
| `action_ready_updater.py` | Evaluates 5 conditions to set Action Ready checkbox | **ACTIVE** |
| `health_check.py` | Post-pipeline health validator (checks stats files for anomalies) | **ACTIVE** |
| `webhook_server.py` | Apollo webhook receiver | **ACTIVE** |
| `verify_links.py` | Contact-company link verifier | **ACTIVE** |
| `job_postings_sync.py` | Job posting signals from Apollo | **PLANNED (Phase 3)** |

Superseded scripts (still in CODE folder but replaced by daily_sync.py):
- `sync_companies.py`, `sync_contacts.py`, `apollo_sync_scheduler.py`, `initial_load_from_csv.py`

---

## daily_sync.py — Sync Engine v2.1

### Three Modes

| Mode | Usage | Description |
|------|-------|-------------|
| `--mode incremental` | Daily use | Last N hours (default 24h). GitHub Actions uses `--hours 26` for overlap. |
| `--mode backfill` | Gap recovery | Historical range with checkpoint. Resumes from `backfill_checkpoint.json` if interrupted. |
| `--mode full` | First-time / rebuild | ALL records. Alphabetical A-Z partitioning to handle Apollo's 50K pagination limit. |

### Key Technical Details

- **Triple Dedup:** Apollo ID → Email → in-memory `seen_ids` set. No duplicates possible.
- **Pre-loading:** Loads ALL existing Notion records into memory before sync to minimize API calls.
- **Alphabetical Partitioning (full mode):** Splits queries A-Z + numbers because Apollo caps at 50,000 results per search.
- **Seniority Normalization:** Uses `SENIORITY_NORMALIZE` dict from constants.py to unify "C-Suite"/"C suite"/"c-suite" variants.
- **Safe Boolean Writing:** Only writes engagement checkboxes (Email Sent, Replied, etc.) if Apollo explicitly returns the field — prevents overwriting manual True with False.
- **Rate Limiting:** 5x exponential backoff on 429/500 errors.
- **Parallel Workers:** `MAX_WORKERS = 3` for Notion writes.

### Commands

```bash
python daily_sync.py --mode incremental --days 7    # last 7 days
python daily_sync.py --mode backfill --days 365      # full year with checkpoint
python daily_sync.py --mode full                     # everything (2-4 hours)
python daily_sync.py                                 # defaults to incremental --hours 24
```

---

## lead_score.py — Scoring Engine

Now writes both **Lead Score** (number 0-100) and **Lead Tier** (HOT/WARM/COLD select) in a single update.

### Formula (v1.1 — current calibrated weights)

```
Score = (Intent × 10%) + (Engagement × 10%) + (Company Size × 45%) + (Seniority × 35%)
```

**Why these weights?** Most contacts are cold Apollo data with no outreach history. Intent and Engagement are mostly empty, so giving them high weight would make scores meaninglessly low. Size and Seniority are available for nearly all records and provide the best signal right now.

### Future v2.0 weights (activate ONLY when signals data exists)

```
Score = (Intent × 30%) + (Engagement × 25%) + (Signals × 25%) + (Size × 10%) + (Seniority × 10%)
```

**IMPORTANT:** Do NOT switch to v2.0 weights until job postings, job change, and intent trend data are actually populated. Giving 25% weight to empty fields would weaken all scores.

### Lead Classification

| Tier | Score | Action |
|------|-------|--------|
| **HOT** | ≥ 80 | Call today — high-value decision makers |
| **WARM-HIGH** | 60–79 | Follow up within 48 hours |
| **WARM** | 50–59 | Nurture over 1 week |
| **COLD** | < 50 | No action — monitor only |

### Expected Calibration Targets

- HOT: 0.5–2% of total contacts
- WARM: 10–20%
- COLD: 80%+ (normal for cold Apollo data — this is expected, not a problem)

### Commands

```bash
python lead_score.py                # score unscored contacts only
python lead_score.py --force        # recalculate ALL scores
python lead_score.py --dry-run      # calculate but don't write
```

---

## auto_tasks.py — Action Engine

Creates Notion tasks for contacts where Action Ready = True, based on Lead Tier and SLA deadlines.

### Priority Rules

| Tier | Min Score | Priority | Action | Channel | SLA |
|------|-----------|----------|--------|---------|-----|
| **HOT** | ≥ 80 | Critical | CALL | Phone | 24 hours |
| **WARM** | ≥ 50 | High | FOLLOW-UP | Email | 48 hours |

### Duplicate Prevention

Before creating a task, checks the Tasks DB for any existing open task (Status ≠ "Completed") linked to the same contact. If one exists, the contact is skipped.

### Commands

```bash
python auto_tasks.py                    # create tasks for all Action Ready contacts
python auto_tasks.py --dry-run          # show what would be created
python auto_tasks.py --limit 20         # limit to first N contacts (testing)
python auto_tasks.py --mark-overdue     # only check and log overdue tasks
```

---

## action_ready_updater.py — Action Ready Evaluator

Evaluates and writes the `Action Ready` checkbox for all scored contacts. A contact is Action Ready ONLY if ALL 5 conditions are met:

1. Lead Score >= 50
2. Do Not Call = False
3. Outreach Status NOT in {Do Not Contact, Bounced, Bad Data}
4. Stage is NOT "Customer" or "Churned"
5. Has at least one contact method (email or phone)

### Commands

```bash
python action_ready_updater.py              # update all scored contacts
python action_ready_updater.py --dry-run    # show what would change
```

---

## health_check.py — Pipeline Health Validator

Runs after the pipeline to validate results by checking stats JSON files.

### Checks

- **CRITICAL:** Zero records processed (sync may have failed)
- **WARNING:** High duplicate rate (>5%)
- **WARNING:** Failed records in sync
- **WARNING:** Action Engine errors
- **INFO:** Zero tasks created (all contacts may already have open tasks)

### Commands

```bash
python health_check.py              # run all checks
python health_check.py --strict     # exit 1 on any warning (not just critical)
```

---

## constants.py — Unified Constants

Single source of truth for all field names, score thresholds, SLA hours, and seniority normalization. Changing a field name here changes it across all scripts that import from constants.

Key exports: `FIELD_*` constants, `SCORE_HOT`/`SCORE_WARM`, `SLA_*_HOURS`, `SENIORITY_NORMALIZE`, `OUTREACH_BLOCKED`

---

## Notion Schema

### Companies Database

Key fields: Name, Domain, Industry, Employee Count, Apollo Account ID (primary key), Website, Phone, Country, City, Annual Revenue

### Contacts Database

Key fields: Name, Email, Title, Seniority, Lead Score (number 0-100), Lead Tier (HOT/WARM/COLD select), Action Ready (checkbox), Intent Score, Outreach Status, Stage, Do Not Call, Email Sent/Opened/Bounced, Replied, Meeting Booked, Demoed, Last Contacted, Contact Responded, First Contact Attempt, Opportunity Created, Apollo Contact ID (primary key), Company (relation to Companies)

### Tasks Database

Key fields: Task Title (title), Priority (select: Critical/High/Medium/Low), Status (**status type** — NOT select — values: "Not Started"/"In Progress"/"Completed"), Due Date, Start Date, Task Type, Team, Contact (relation), Company (relation), Opportunity (relation), Context, Description, Expected Outcome, Auto Created (checkbox), Automation Type (select), Trigger Rule, Completed At

**IMPORTANT:** Tasks DB Status field is `status` type, not `select`. Use `{"status": {"name": "Not Started"}}` not `{"select": ...}`.

### Other Databases

Opportunities, Meetings, Activities, Email Hub — used for execution workflow.

---

## Primary Key Rules (CRITICAL)

- **Companies:** Primary Key = `Apollo Account ID`. Validation = `Domain`.
- **Contacts:** Primary Key = `Apollo Contact ID`. Validation = `Email`.
- NEVER create duplicates if Apollo ID exists — ALWAYS update.
- NEVER match based on name only.

---

## Data Rules

1. **Never overwrite manual data.** Fields like Owner, Status, Notes, Stage — if manually edited, Apollo data must not overwrite them.
2. **Update only missing or dynamic fields.** Empty fields, engagement data, intent scores, last contacted.
3. **No orphan contacts.** Every contact MUST be linked to a company. If no company found: log as orphan, do NOT create.
4. **Companies before Contacts.** Company sync must complete before contact sync.
5. **No invented data.** Never guess or fabricate values for empty fields.

---

## GitHub Actions Pipeline

**File:** `.github/workflows/daily_sync.yml`
**Schedule:** Daily at 7:00 AM KSA (04:00 UTC)

Pipeline steps (10 total):
1. Checkout repository
2. Setup Python 3.11 with pip cache
3. Install dependencies
4. `daily_sync.py --mode incremental --hours 26` (sync)
5. `lead_score.py` (recalculate scores + write Lead Tier)
6. `action_ready_updater.py` (evaluate Action Ready for scored contacts)
7. `auto_tasks.py` (create tasks for Action Ready contacts, continue-on-error)
8. `health_check.py` (validate pipeline run)
9. Upload logs as artifacts (30-day retention)
10. Notify on failure (tail last 30 lines of each log)

**Required Secrets:** `APOLLO_API_KEY`, `NOTION_API_KEY`, `NOTION_DATABASE_ID_CONTACTS`, `NOTION_DATABASE_ID_COMPANIES`, `NOTION_DATABASE_ID_TASKS`

**Manual trigger:** Available from GitHub UI with mode selection (incremental / backfill_week / backfill_month / full), plus toggles for `run_lead_score` and `run_action_engine`.

**Cost:** Free. GitHub Actions free tier = 2,000 min/month. Daily run ≈ 15 min × 30 = 450 min/month.

---

## Execution Plan (4 Phases)

### Phase 1: ACTIVATE — COMPLETE
- [x] Full Sync running (all 60K+ records)
- [x] Lead Score engine built (v1.1 weights)
- [x] Lead Tier writing (HOT/WARM/COLD alongside score)
- [x] Seniority normalization (constants.py + _normalize_seniority)
- [x] Safe boolean writing (prevents overwriting manual data)
- [x] daily_sync.py v2.1 (added Stage, Outreach Status, engagement booleans, Last Contacted, Departments)
- [ ] Calibration — run `lead_score.py --force` to write Lead Tier for all contacts
- [ ] Push code to GitHub, add `NOTION_DATABASE_ID_TASKS` secret, activate workflow
- **Gate:** Calibration must pass before activating Actions

### Phase 2: ACTION — CODE COMPLETE (pending first run)
- [x] Built `constants.py` — unified field names & thresholds
- [x] Built `auto_tasks.py` — SLA-based task creator (HOT=24h call, WARM=48h follow-up)
- [x] Built `action_ready_updater.py` — 5-condition gating (score, DNC, outreach, stage, contact method)
- [x] Built `health_check.py` — post-pipeline health validator
- [x] Updated `daily_sync.yml` — 10-step pipeline with Action Engine + Health Check
- [ ] First run: `action_ready_updater.py` then `auto_tasks.py --dry-run` to validate
- [ ] Create Notion task views for sales workflow
- **Gate:** Tasks must generate correctly before Phase 3

### Phase 3: ENRICH ← NEXT
- [ ] Job Postings signal (`organizations/job_postings` Apollo endpoint)
- [ ] Job Change detection (build from `people_match` + compare)
- [ ] Intent Trend tracking (compare intent scores between syncs)
- [ ] Lead Score v2.0 (activate new weights with signals data)
- **Gate:** Signals must have data before v2 weights activate

### Phase 4: OPTIMIZE
- [ ] Odoo ERP integration (push qualified opportunities)
- [ ] Revenue pipeline tracking
- [ ] Advanced analytics
- [ ] Full end-to-end automation

---

## Apollo API Endpoints Used

| Endpoint | Purpose | Mode |
|----------|---------|------|
| `contacts/search` | Fetch contacts with filters | All modes |
| `accounts/search` | Fetch companies with filters | All modes |
| `organizations/job_postings` | Job posting signals | Phase 3 (planned) |
| `organizations/enrich` | Company enrichment | Phase 3 (planned) |
| `people_match` | Job change detection | Phase 3 (planned) |
| `mixed_people_api_search` | Advanced people search | Available |

---

## Signals Feasibility (from Apollo API)

| Signal | Method | Status |
|--------|--------|--------|
| **Job Postings** | Direct API endpoint | Available (Phase 3) |
| **Job Change** | Build detection via people_match + historical compare | Buildable (Phase 3) |
| **Intent Trend** | Compare intent scores between sync runs | Simple compare (Phase 3) |
| **News/Events** | No Apollo API | NOT available |
| **Email Engagement Detail** | Internal Apollo data, not exposed | NOT available |

---

## Key Decisions (Decision Log)

1. **No Middleware** — Rejected n8n, Make.com, Zapier. Pure Python + GitHub Actions.
2. **Embed Signals in Schema** — Signals stored as fields on Companies/Contacts, NOT a separate database.
3. **Triple Dedup** — Apollo ID → Email → seen_ids. Prevents duplicates even with pagination overlap.
4. **Time-Window Splitting** — Incremental uses 26-hour window (2h overlap). Dedup handles the rest.
5. **Alphabetical Partitioning** — Full mode splits A-Z + numbers to handle Apollo's 50K cap.
6. **Phase-Gated Execution** — Each phase must pass validation before proceeding.
7. **v1.1 Weights First** — Size + Seniority weighted high because Intent + Engagement data is sparse.
8. **80% COLD is Normal** — Cold Apollo data with no outreach = low scores expected. Not a bug.
9. **Safe Boolean Writing** — Only write engagement checkboxes if Apollo explicitly returns the field. Prevents overwriting manually-set True with False.
10. **Unified Constants** — All field names in constants.py. No hardcoded strings in individual scripts.
11. **Action Ready Gating** — 5-condition check before any task is created. Prevents tasks for DNC, bounced, churned, or contacts without contact methods.

---

## Execution Behavior

- Execute sequentially. No jumping between phases.
- Validate after each batch. Report: created / updated / skipped / errors.
- Do NOT redesign schema during execution.
- Do NOT suggest alternatives mid-execution.
- Accuracy over speed. A slow correct system beats a fast broken one.

---

## Environment Setup

```bash
cd "💻 CODE/Phase 3 - Sync"
cp .env.example .env
# Fill in API keys
pip install -r requirements.txt
```

Required env vars: `APOLLO_API_KEY`, `NOTION_API_KEY`, `NOTION_DATABASE_ID_CONTACTS`, `NOTION_DATABASE_ID_COMPANIES`, `NOTION_DATABASE_ID_TASKS`

---

## Files That Matter Most

| Need | File |
|------|------|
| Sync engine | `💻 CODE/Phase 3 - Sync/daily_sync.py` |
| Lead scoring | `💻 CODE/Phase 3 - Sync/lead_score.py` |
| Constants (field names, thresholds) | `💻 CODE/Phase 3 - Sync/constants.py` |
| Action Engine (task creation) | `💻 CODE/Phase 3 - Sync/auto_tasks.py` |
| Action Ready evaluator | `💻 CODE/Phase 3 - Sync/action_ready_updater.py` |
| Health check | `💻 CODE/Phase 3 - Sync/health_check.py` |
| Notion utilities | `💻 CODE/Phase 3 - Sync/notion_helpers.py` |
| Execution plan | `📚 DOCUMENTATION/EXECUTION_PLAN_v3.0.docx` |
| Field mapping | `📚 DOCUMENTATION/System Architecture/FIELD_MAPPING_RULES.md` |
| GitHub Actions | `.github/workflows/daily_sync.yml` |
| Mind map | `AI_Sales_OS_MindMap.html` |
| Credentials | `💻 CODE/Phase 3 - Sync/.env` (NEVER commit) |
