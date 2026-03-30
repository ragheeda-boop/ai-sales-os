# AI Sales OS — CLAUDE.md

## Identity & Role

You are the **RevOps Architect & Data Pipeline Operator** for AI Sales OS.
This is a production-grade Sales Operating System, not a hobby project.

**System:** Apollo.io → Python Engine → Notion CRM → GitHub Actions → Odoo (future)
**Owner:** Ragheed
**Version:** 4.3 | March 2026 | Phase 3.5 Complete + Live Dashboard

---

## System Architecture

```
Apollo.io (Data)  ──►  Python Scripts (19 scripts)  ──►  Notion (CRM Hub)  ──►  GitHub Actions (Daily + Weekly)
  44,875 contacts         Sync + Enrich + Score +            7 Databases            7:00 AM KSA
  15,407 companies        Action + Sequence + Meet           HOT/WARM/COLD          2-job pipeline + weekly calibration
                          Dashboard (auto-regenerated HTML)  Live Sales Dashboard   Sales_Dashboard_Accounts.html
```

**Autonomous Sales Loop:** Score → Task → Auto-Sequence → Track Results → Meet → Analyze → Opportunity → Calibrate → Better Score

**Key design decision:** NO middleware. No n8n, no Make.com, no Zapier. Pure Python + GitHub Actions = full control, zero cost.

---

## Folder Structure

```
AI Sales OS/
├── CLAUDE.md                    → AI instructions & system reference (this file)
├── README.md                    → Project overview
├── AI_Sales_OS_MindMap.html     → Interactive mind map v8.0 (Arabic)
├── Muhide.png                   → Brand logo
│
├── Sales_Dashboard_Accounts.html → Account-based Sales Dashboard (auto-regenerated daily)
│
├── 💻 CODE/Phase 3 - Sync/      → All 19 production scripts
│   ├── daily_sync.py            → Main sync engine v2.3 (3 modes + local timestamp filter)
│   ├── lead_score.py            → Lead scoring engine (writes Score + Tier)
│   ├── constants.py             → Unified field names & thresholds (single source of truth)
│   ├── notion_helpers.py        → Shared Notion API utilities
│   ├── auto_tasks.py            → Action Engine — SLA-based task creator
│   ├── action_ready_updater.py  → Computes Action Ready checkbox (5 conditions)
│   ├── health_check.py          → Pipeline health validator
│   ├── job_postings_enricher.py → Intent proxy from Apollo Job Postings
│   ├── auto_sequence.py         → Auto-enroll contacts in Apollo Sequences
│   ├── analytics_tracker.py     → Apollo Analytics → Notion engagement sync
│   ├── score_calibrator.py      → Self-learning weight adjustment
│   ├── morning_brief.py         → Daily intelligence report generator
│   ├── meeting_tracker.py       → Meeting sync + Contact stage update [Phase 3.5]
│   ├── meeting_analyzer.py      → AI meeting intelligence via Claude API [Phase 3.5]
│   ├── opportunity_manager.py   → Meetings → Opportunities + stale deal detection [Phase 3.5]
│   ├── dashboard_generator.py   → Pulls live Notion data → regenerates Sales_Dashboard_Accounts.html [v4.2]
│   ├── doc_sync_checker.py      → Documentation drift validator [v4.1]
│   ├── webhook_server.py        → Apollo webhook receiver
│   ├── verify_links.py          → Contact-company link verifier
│   ├── .env                     → API credentials (NEVER commit)
│   ├── .env.example             → Credential template
│   ├── requirements.txt         → Python dependencies
│   └── *.log                    → Runtime logs (auto-generated, gitignored)
│
├── 🎯 PRESENTATIONS/            → All presentation files
│   ├── English/
│   │   └── AI_Sales_OS_Presentation.pptx       → Main English technical deck (v4.1)
│   ├── Arabic/
│   │   ├── عرض_تقديمي_AI_Sales_OS_v4.1.pptx   → Arabic v4.1 (latest)
│   │   └── عرض_تقديمي_v2.pptx                 → Arabic v2 overview
│   └── CEO Pitch/
│       └── AI_Sales_OS_CEO_Pitch_v2.pptx       → Executive pitch deck (Arabic)
│
├── 📊 DATA/
│   ├── Import CSVs/             → Initial data import files (companies + contacts)
│   ├── Logs/                    → Sync run logs and runtime stats JSON
│   ├── Mapping Files/           → Apollo↔Notion field mapping + setup tracker
│   └── Notion Snapshots/        → Point-in-time JSON snapshots
│
├── 📚 DOCUMENTATION/
│   ├── EXECUTION_PLAN_v3.2.docx → Master execution plan (phases 1–4)
│   ├── AI_Sales_OS_Deep_Analysis.md           → 12-section system analysis (v4.1)
│   ├── AI_Sales_OS_Comprehensive_Audit.docx   → Comprehensive audit report
│   ├── AI_Sales_OS_Revenue_Gap_Analysis.docx  → Revenue gap analysis
│   ├── MUHIDE_Brand_Identity_Guide.md         → Brand guidelines
│   ├── GITHUB_SETUP_GUIDE.md                  → GitHub Actions setup instructions
│   ├── Phase 1 - Notion Setup/  → Notion database setup documentation
│   ├── Phase 2 - Data Import/   → Data import strategy and guides
│   ├── Phase 3 - Apollo API Pull/ → Apollo API integration documentation
│   └── System Architecture/     → Technical architecture + field mapping + assessment docs
│
├── .claude/skills/              → 12 Claude Skills for AI Sales OS operations
├── .github/workflows/           → daily_sync.yml (CI/CD — 2-job pipeline: Job1 Sync/Score + Job2 Action/Track + weekly calibration)
├── 🚀 START HERE/               → Entry docs: QUICK_START, SYSTEM_OVERVIEW, PROJECT_MAP
├── 🗂️ ARCHIVED/                 → Superseded scripts, old docs, old presentations
└── .gitignore
```

---

## Active Scripts

| Script | Purpose | Status |
|--------|---------|--------|
| `daily_sync.py` | Apollo → Notion sync engine (v2.3, 3 modes, local timestamp filter, seniority normalization, safe booleans, Apollo signals + AI fields) | **ACTIVE** |
| `lead_score.py` | Lead Score calculator (0-100) + Lead Tier writer (HOT/WARM/COLD) | **ACTIVE** |
| `constants.py` | Unified field names, score thresholds, SLA hours, seniority normalization map | **ACTIVE** |
| `notion_helpers.py` | Shared Notion API utilities (create, update, preload, rate limiter) | **ACTIVE** |
| `auto_tasks.py` | Action Engine — creates SLA-based tasks for Action Ready contacts | **ACTIVE** |
| `action_ready_updater.py` | Evaluates 5 conditions to set Action Ready checkbox | **ACTIVE** |
| `health_check.py` | Post-pipeline health validator (checks stats files for anomalies) | **ACTIVE** |
| `job_postings_enricher.py` | Intent proxy — uses Apollo Job Postings API for intent scoring | **ACTIVE (v4.0)** |
| `auto_sequence.py` | Auto-enrolls Action Ready contacts into Apollo Sequences | **ACTIVE (v4.0)** |
| `analytics_tracker.py` | Pulls Apollo Analytics, syncs engagement data back to Notion | **ACTIVE (v4.0)** |
| `score_calibrator.py` | Self-learning weight adjustment based on actual outcomes | **ACTIVE (v4.0)** |
| `morning_brief.py` | Daily intelligence report (urgent calls, tasks, replies, stats) | **ACTIVE (v4.0)** |
| `meeting_tracker.py` | Notion-native meeting sync; updates Contact (Meeting Booked, Stage, Outreach Status) | **ACTIVE (v4.1)** |
| `meeting_analyzer.py` | Claude AI analysis of meeting notes → key takeaways, sentiment, next steps | **ACTIVE (v4.1) — requires ANTHROPIC_API_KEY** |
| `opportunity_manager.py` | Positive meetings → Opportunities; stage advancement; stale deal detection (14 days) | **ACTIVE (v4.1)** |
| `dashboard_generator.py` | Pulls live Notion Contacts + Companies data → aggregates by account → injects into Sales_Dashboard_Accounts.html via regex template injection | **ACTIVE (v4.2)** |
| `doc_sync_checker.py` | Validates documentation vs codebase state — catches drift after development | **ACTIVE (v4.1)** |
| `webhook_server.py` | Apollo webhook receiver | **ACTIVE** |
| `verify_links.py` | Contact-company link verifier | **ACTIVE** |

Superseded scripts (still in CODE folder but replaced by daily_sync.py):
- `sync_companies.py`, `sync_contacts.py`, `apollo_sync_scheduler.py`, `initial_load_from_csv.py`

---

## daily_sync.py — Sync Engine v2.3

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
- **Local Timestamp Filter (v4.2):** After Apollo fetch, a client-side filter drops any record whose `updated_at` is before the requested `since` datetime. Fixes issue where Apollo's date-only API filter was returning all 44,877 contacts on every incremental run, causing 4-5 hour runtimes instead of minutes.
- **Apollo Signals (v4.3):** Contacts sync now pulls Intent Strength, Job Change Event/Date, and AI Decision from `typed_custom_fields`. Companies sync now pulls Headcount Growth (6/12/24 month) and AI Qualification Status/Detail from `typed_custom_fields`.

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

## job_postings_enricher.py — Intent Proxy (v4.0)

Uses Apollo's Job Postings API as a proxy for Intent Score. Companies that are actively hiring in relevant roles = higher buying intent.

### Scoring Components (0-100)
- **Job Volume (0-40):** Number of open positions
- **Recency (0-20):** How recently jobs were posted
- **Relevance (0-25):** Keywords matching our solution areas (insurance, risk, compliance, finance, etc.)
- **Growth Signals (0-15):** Hiring across multiple departments

Writes `Job Postings Intent` to Companies DB, then propagates to linked Contacts' `Primary Intent Score`. Uses 7-day cache to avoid redundant API calls.

### Commands

```bash
python job_postings_enricher.py                    # enrich all HOT/WARM companies
python job_postings_enricher.py --dry-run          # preview without writing
python job_postings_enricher.py --limit 20         # limit to first N companies
python job_postings_enricher.py --tier HOT         # only HOT companies
python job_postings_enricher.py --no-cache         # ignore 7-day cache
```

---

## auto_sequence.py — Auto Sequence Enrollment (v4.0)

Automatically enrolls Action Ready contacts into Apollo Sequences based on Lead Tier + Role category. Round-robins between senders.

### Sequence Mapping

Maps (Tier, Role) → specific Apollo sequence. Role detection uses seniority + title keywords to classify contacts as: CEO, CFO, Sales, Legal, or General.

### Sender Round-Robin

Alternates between `ragheed` and `ibrahim` email accounts (2 accounts each: joinmuhide.com + ratlfintech.com/muhide.com).

### Safety

- Skips contacts already "In Sequence"
- Skips DNC and blocked outreach statuses
- Updates Notion `Outreach Status → "In Sequence"` after enrollment
- Default limit of 50 per run in pipeline

### Commands

```bash
python auto_sequence.py                     # enroll all eligible contacts
python auto_sequence.py --dry-run           # preview without enrolling
python auto_sequence.py --limit 10          # limit to first N
python auto_sequence.py --tier HOT          # only HOT contacts
python auto_sequence.py --sender ragheed    # force specific sender
```

---

## analytics_tracker.py — Analytics & Engagement Sync (v4.0)

Pulls Apollo Analytics data and syncs engagement signals back to Notion contacts. Closes the feedback loop by bringing real engagement data into the CRM.

### What It Does

1. **Engagement Sync:** Checks contacts in active outreach (In Sequence, Sent, Opened) and updates Notion booleans (Replied, Email Opened, Email Sent) from Apollo data
2. **Analytics Report:** Generates performance reports broken down by seniority, company size, and weekly trends

### Commands

```bash
python analytics_tracker.py                    # full sync + report
python analytics_tracker.py --dry-run          # preview without writing
python analytics_tracker.py --days 7           # last N days
python analytics_tracker.py --export           # save report to file
python analytics_tracker.py --skip-sync        # report only, no Notion writes
```

---

## score_calibrator.py — Self-Learning Weights (v4.0)

Analyzes actual engagement outcomes and recommends weight adjustments for lead_score.py. The feedback loop: Score → Action → Outcome → Calibrate → Better Score.

### Safety Rails

- `MAX_WEIGHT_CHANGE = 0.10` per cycle (no sudden jumps)
- `MIN_WEIGHT = 0.05` (no component goes to zero)
- `MIN_EMAILS_FOR_CALIBRATION = 100` (need enough data)
- Saves full history in `calibration_history.json`
- Never auto-applies unless `--apply` flag is explicitly used

### Commands

```bash
python score_calibrator.py                  # analyze + recommend (no changes)
python score_calibrator.py --apply          # apply recommended weights
python score_calibrator.py --days 90        # analyze last 90 days
python score_calibrator.py --export         # save analysis to file
```

**IMPORTANT:** Weekly pipeline runs calibrator in review-only mode (no --apply). Manual review required before applying.

---

## morning_brief.py — Daily Intelligence Report (v4.0)

Generates a daily morning brief with everything a sales rep needs to know.

### Sections

1. **Urgent Calls:** HOT leads not yet contacted
2. **Today's Tasks:** Due today + overdue
3. **Recent Replies:** Contacts that responded
4. **Pipeline Summary:** HOT/WARM/COLD counts
5. **Email Performance:** Last 7 days from Apollo Analytics

### Commands

```bash
python morning_brief.py                 # generate today's brief (stdout)
python morning_brief.py --output file   # save to markdown file
python morning_brief.py --days 1        # look back N days for activity
```

---

## constants.py — Unified Constants

Single source of truth for all field names, score thresholds, SLA hours, and seniority normalization. Changing a field name here changes it across all scripts that import from constants.

Key exports: `FIELD_*` constants, `SCORE_HOT`/`SCORE_WARM`, `SLA_*_HOURS`, `SENIORITY_NORMALIZE`, `OUTREACH_BLOCKED`

---

## Notion Schema

### Companies Database

Key fields: Name, Domain, Industry, Employee Count, Apollo Account ID (primary key), Website, Phone, Country, City, Annual Revenue, Headcount Growth 6M/12M/24M, AI Qualification Status (Qualified/Disqualified/Possible Fit), AI Qualification Detail

### Contacts Database

Key fields: Name, Email, Title, Seniority, Lead Score (number 0-100), Lead Tier (HOT/WARM/COLD select), Action Ready (checkbox), Intent Score, Intent Strength, Outreach Status, Stage, Do Not Call, Email Sent/Opened/Bounced, Replied, Meeting Booked, Demoed, Last Contacted, Contact Responded, First Contact Attempt, Opportunity Created, Job Change Event, Job Change Date, AI Decision, Email Open Count, Emails Sent Count, Emails Replied Count, Apollo Contact ID (primary key), Company (relation to Companies)

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

### Why 2 Jobs?
The pipeline was exceeding GitHub's 6-hour per-job limit. Splitting into 2 sequential jobs gives each its own 6-hour clock — total capacity: ~9 hours.

### Job 1: `sync-and-score` — timeout 5h 50min
1. Checkout repository
2. Setup Python 3.11 with pip cache
3. Install dependencies
4. `daily_sync.py --mode incremental --hours 26` (sync)
5. `job_postings_enricher.py --limit 50` (intent proxy, continue-on-error)
6. `lead_score.py` (recalculate scores + write Lead Tier)
7. `action_ready_updater.py` (evaluate Action Ready for scored contacts)
8. Upload sync stats as artifact → passed to Job 2

### Job 2: `action-and-track` — timeout 3h (runs after Job 1)
1. Checkout + Python setup + Install dependencies
2. Download sync stats from Job 1
3. `auto_tasks.py` (create tasks for Action Ready contacts, continue-on-error)
4. `auto_sequence.py --limit 50` (enroll contacts in sequences, continue-on-error)
5. `meeting_tracker.py --days 7` (sync meetings, update contact stage)
6. `meeting_analyzer.py --limit 10` (AI meeting intelligence, requires ANTHROPIC_API_KEY)
7. `opportunity_manager.py` (meetings → opportunities + stale deal detection)
8. `analytics_tracker.py --days 7` (sync engagement data, continue-on-error)
9. `health_check.py` (validate pipeline run)
10. `morning_brief.py --output file` (generate daily report, continue-on-error)
11. `dashboard_generator.py` (regenerate Sales_Dashboard_Accounts.html from live Notion data, continue-on-error)
12. Commit updated `Sales_Dashboard_Accounts.html` back to repo (auto-commit by github-actions bot)
13. Upload all logs as artifacts (30-day retention), including `dashboard_generator.log` + `dashboard_stats.json`
14. Notify on failure

**Weekly Job (Sundays):** `score_calibrator.py --days 30 --export` — runs after Job 2, review-only, no auto-apply.

**Required Secrets:** `APOLLO_API_KEY`, `NOTION_API_KEY`, `NOTION_DATABASE_ID_CONTACTS`, `NOTION_DATABASE_ID_COMPANIES`, `NOTION_DATABASE_ID_TASKS`, `NOTION_DATABASE_ID_MEETINGS`, `NOTION_DATABASE_ID_OPPORTUNITIES`, `ANTHROPIC_API_KEY` (optional)

**Manual trigger:** Available from GitHub UI with mode selection (incremental / backfill_week / backfill_month / full), plus toggles for `run_lead_score`, `run_action_engine`, `run_sequences`.

**Cost:** Free. GitHub Actions free tier = 2,000 min/month. Daily run ≈ 30 min × 30 = 900 min/month.

---

## Execution Plan (4 Phases)

### Phase 1: ACTIVATE — COMPLETE ✓
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
- [x] Updated `daily_sync.yml` — 23-step pipeline with Action Engine + Health Check
- [x] Built 12 Claude Skills for AI Sales OS operations (evaluated at 100% pass rate)
- [ ] First run: `action_ready_updater.py` then `auto_tasks.py --dry-run` to validate
- [ ] Create Notion task views for sales workflow
- **Gate:** Tasks must generate correctly before Phase 3

### Phase 3: ENRICH — COMPLETE ✓
- [x] Job Postings signal (`job_postings_enricher.py` — active, 50/run limit)
- [x] Auto Sequence enrollment (`auto_sequence.py` — HOT/WARM × 5 roles × 2 senders)
- [x] Analytics tracking (`analytics_tracker.py` — engagement sync from Apollo)
- [x] Score Calibrator (`score_calibrator.py` — weekly review-only mode)
- [ ] Job Change detection (build from `people_match` + compare) — deferred to Phase 4
- [ ] Lead Score v2.0 — HOLD until intent/engagement signals > 50% coverage

### Phase 3.5: MEET — COMPLETE ✓ (March 2026)
- [x] `meeting_tracker.py` — Notion-native meeting sync, dual mode (Notion + Google Calendar)
- [x] `meeting_analyzer.py` — Claude AI meeting intelligence (requires ANTHROPIC_API_KEY in GitHub Secrets)
- [x] `opportunity_manager.py` — Meeting → Opportunity pipeline + stale deal detection
- [x] `doc_sync_checker.py` — Documentation drift validator
- [x] GitHub Actions updated to 23-step pipeline (meeting tracker, analyzer, opportunity manager added)
- [x] constants.py expanded with MEETINGS + OPPORTUNITIES field definitions
- [ ] ANTHROPIC_API_KEY confirmed in GitHub Secrets — **must verify**
- [ ] First real meeting logged in Meetings DB — **activate the loop**
- **Architecture assessment:** `Meeting_Call_Intelligence_Architecture_Assessment.md`

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
12. **2-Job Pipeline** — Split daily_sync.yml into Job 1 (Sync/Score, 5h 50min) and Job 2 (Action/Track, 3h) to bypass GitHub Actions' 6-hour per-job limit. Stats passed via artifacts.
13. **Local Timestamp Filter** — Apollo's `contact_updated_at_range` API filter uses day-granularity and was returning all 44,877 contacts even on incremental runs. Fixed in `_fetch_with_date_filter()` with a post-fetch client-side filter using exact `updated_at >= since` comparison. Incremental runs now complete in minutes, not hours.
14. **Apollo Signals in Sync (v4.3)** — Intent Strength, Job Change Event/Date, Headcount Growth (6/12/24M), and Apollo AI fields (AI Decision, AI Qualification Status/Detail) are now extracted directly from contact/account responses during daily_sync.py. No separate enrichment scripts needed — signals flow with the regular sync.
15. **Apollo AI Custom Field IDs** — Apollo's AI generates typed_custom_fields with fixed IDs: Contact Decision (`6913a64c52c2780001146ce9`), Account ICP Analysis (`6913a64c52c2780001146cfd`), Account Research (`6913a64c52c2780001146d0e`), Account Qualification (`6913a64c52c2780001146d22`). IDs are stored in constants.py for maintainability.

---

## Claude Skills (12 Production Skills)

AI Sales OS has 12 specialized Claude Skills in `.claude/skills/`. These are production-grade, evaluated at **100% pass rate** (vs 61.1% without skills).

| Skill | Purpose |
|-------|---------|
| `shared-sales-os-rules` | Foundation rules — system architecture, data constraints, scoring formula, primary key rules |
| `apollo-sync-operator` | Operate, troubleshoot, and improve the Apollo-to-Notion sync pipeline |
| `notion-schema-manager` | Manage Notion database schema, properties, relations, and views |
| `lead-scoring-analyst` | Analyze, calibrate, and improve lead scoring and classification |
| `data-integrity-guardian` | Detect and fix data quality issues (duplicates, missing fields, conflicts) |
| `action-engine-builder` | Build and operate the Action Engine (auto_tasks.py) and Action Ready logic |
| `pipeline-health-monitor` | Monitor daily pipeline health, detect failures, alert on anomalies |
| `meeting-intelligence-summarizer` | Turn meetings into structured CRM updates and follow-up tasks |
| `revenue-loop-tracker` | Track conversion rates, score-to-revenue correlation, feedback loops |
| `apollo-icp-strategist` | Define ICP, segment markets, prioritize accounts |
| `apollo-sequence-builder` | Create outbound sales sequences, email copy, LinkedIn messages |
| `exec-brief-writer` | Write executive summaries, status updates, business cases |

**Eval Benchmark:** `Skills_Eval_Review.html` — interactive viewer with side-by-side comparisons

---

## Documentation Sync Protocol — MANDATORY

**Every time any script is added, modified, or the pipeline changes, Claude MUST immediately update:**

| What Changed | Files to Update |
|---|---|
| New script added | CLAUDE.md (Active Scripts table + Folder Structure) · SYSTEM_OVERVIEW.md · QUICK_START.md |
| Pipeline steps changed | CLAUDE.md (architecture line + GitHub Actions section) · SYSTEM_OVERVIEW.md · QUICK_START.md · Notion Command Center · Notion Autonomous Loop Dashboard |
| New Phase or Phase status change | CLAUDE.md (Execution Plan) · SYSTEM_OVERVIEW.md (Execution Plan table) · Notion Command Center |
| New env variable required | `.env.example` · QUICK_START.md Prerequisites section |
| New key document created | SYSTEM_OVERVIEW.md Key Documents table |

**Validation command (run after any development session):**
```bash
python doc_sync_checker.py --strict --fix-hints
```

This script (`doc_sync_checker.py`) checks script count, pipeline step count, env variables, and phase alignment against the actual codebase. Any drift is flagged before it compounds.

**The rule:** Never finish a development session without running doc_sync_checker.py. If it finds drift, fix it before moving on.

---

