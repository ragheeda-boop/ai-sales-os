# AI Sales OS — CLAUDE.md

## Identity & Role

You are the **RevOps Architect & Data Pipeline Operator** for AI Sales OS.
This is a production-grade Sales Operating System, not a hobby project.

**System:** Apollo.io → Python Engine → Notion CRM → GitHub Actions → Odoo (future)
**Owner:** Ragheed
**Version:** 7.0 | April 2026 | Modular Architecture + Company-Centric Operating Model + Phase 3.5 Complete + Decision Layer (Company Priority Scorer) + 7 scripts archived + Safe Execution Order + Stage Conflict Guards + Freshness Guard + Enrichment Layer v5.3 + **Score Calibrator: v1.5 weights fixed**

---

## System Architecture

```
Apollo.io (Data)  ──►  Python Engine (8 modules)  ──►  Notion (CRM Hub)  ──►  GitHub Actions (Daily + Weekly)
  45,086 contacts         Core / Scoring /               7 Databases            7:00 AM KSA
  15,407 companies        Automation / Governance /      HOT/WARM/COLD          2-job pipeline + weekly calibration
                          Enrichment / Meetings /        Live Sales Dashboard   Sales_Dashboard_Accounts.html
                          Monitoring / Webhooks          Primary/Supporting Owners + Company Priority Score
                          (29 active + 1 admin-only)    Company Stage Machine + Decision Layer
Additional Pipelines: pipelines/muqawil/ (contractors) + pipelines/engineering_offices/ (ministry offices) + pipelines/file_sync/
```

**Company-Centric Model (v5.0):** Company = Primary Entity. ONE task per company. ONE opportunity per company. Primary Owner = most contacts. Company Stage state machine: Prospect → Outreach → Engaged → Meeting → Opportunity → Customer → Churned → Archived.

**Autonomous Sales Loop:** Score → Task → Auto-Sequence → Track Results → Outcome → Meet → Analyze → Opportunity → Calibrate → Better Score

**Key design decision:** NO middleware. No n8n, no Make.com, no Zapier. Pure Python + GitHub Actions = full control, zero cost.

---

## Folder Structure

```
AI Sales OS/
├── CLAUDE.md                    → AI instructions & system reference (this file)
├── README.md                    → Project overview
│
├── assets/                      → Brand assets
│   └── Muhide.png               → Brand logo
│
├── dashboards/                  → Live dashboard reports (active + archived)
│   ├── active/
│   │   └── Sales_Dashboard_Accounts.html      → Account-based Sales Dashboard (auto-regenerated daily)
│   └── archived/                              → Historical dashboards (8 HTML files)
│       ├── AI_Sales_OS_Live_Dashboard.html
│       ├── AI_Sales_OS_MindMap.html
│       ├── AI_Sales_OS_Test_Report.html
│       ├── Companies_DB_Revenue_Engine_Analysis.html
│       ├── Company_Centric_Enforcement_Plan.html
│       ├── Full_System_Revenue_Engine_Analysis.html
│       ├── Sales_Dashboard_Accounts_view.html
│       └── تقرير_الاكتتابات_السعودية_2026.html
│
├── scripts/                     → Core application (21 active scripts + 1 new, 8 modules)
│   │   NOTE: All logs write to their own module subdir (e.g. scripts/core/daily_sync.log,
│   │         scripts/scoring/lead_score.log) — NEVER to the root or scripts/ root.
│   ├── core/
│   │   ├── constants.py              → Unified field names & thresholds (single source of truth)
│   │   ├── notion_helpers.py         → Shared Notion API utilities
│   │   ├── daily_sync.py             → Main sync engine v5.1 (3 modes + local timestamp filter + Company-Centric)
│   │   ├── doc_sync_checker.py       → Documentation drift validator [v4.1]
│   │   └── ai_sales_actions_parser.py → Parses Apollo AI Sales Actions typed_custom_field (Decision #26)
│   ├── scoring/
│   │   ├── lead_score.py             → Lead scoring engine v1.5 (writes Score + Tier + Sort Score)
│   │   ├── score_calibrator.py       → Self-learning weight adjustment (weekly review-only)
│   │   ├── action_ready_updater.py   → Computes Action Ready checkbox (5 conditions)
│   │   └── company_priority_scorer.py → Company Priority Score (Decision Layer v7.0) — Decision Layer v7.0
│   ├── automation/
│   │   ├── auto_tasks.py             → Action Engine v2.0 — SLA-based company-centric task creator
│   │   ├── auto_sequence.py          → Auto-enroll contacts in Apollo Sequences
│   │   ├── outcome_tracker.py        → Task → Contact outcome loop (v1.0)
│   │   └── lead_inbox_mover.py       → v0.2 — Move Qualified Lead Inbox → real Company+Contact records
│   ├── governance/
│   │   ├── ingestion_gate.py         → Ingestion gate — validates companies/contacts before entry [v6.0]
│   │   ├── data_governor.py          → Data governance enforcer — audit + archive unqualified records [v6.1]
│   │   ├── audit_ownership.py        → Audit ownership gaps across all Notion DBs
│   │   └── full_reset_notion.py      → ⚠️ DANGER: Full Notion DB wipe — run only in dev/staging NEVER production
│   ├── enrichment/
│   │   ├── job_postings_enricher.py       → Intent proxy from Apollo Job Postings
│   │   ├── muhide_strategic_analysis.py   → AI engine — scores all companies vs MUHIDE ICP (Fit Score + Priority)
│   │   ├── analytics_tracker.py           → Apollo Analytics → Notion engagement sync
│   │   ├── ai_sales_actions_enricher.py   → Parses + writes Apollo AI Sales Actions sub-fields to Companies DB (now in pipeline v7.0)
│   │   └── reply_intelligence.py          → Reply Intelligence Engine — classifies replied contacts (Status/Reason/Probability/Action)
│   ├── meetings/
│   │   ├── meeting_tracker.py        → Meeting sync + Contact stage update [Phase 3.5]
│   │   ├── meeting_analyzer.py       → AI meeting intelligence via Claude API [Phase 3.5]
│   │   └── opportunity_manager.py    → Meetings → Opportunities + stale deal detection [Phase 3.5]
│   ├── monitoring/
│   │   ├── health_check.py           → Pipeline health validator
│   │   ├── morning_brief.py          → Daily intelligence report generator
│   │   └── dashboard_generator.py    → Pulls live Notion data → regenerates Sales_Dashboard_Accounts.html [v4.2]
│   ├── webhooks/
│   │   ├── webhook_server.py         → Apollo webhook receiver (logs → scripts/webhooks/logs/)
│   │   └── verify_links.py           → Contact-company link verifier
│   ├── .env                          → API credentials (NEVER commit)
│   ├── .env.example                  → Credential template
│   └── requirements.txt              → Python dependencies
│
├── pipelines/                   → Specialized data pipelines (separate from main workflow)
│   ├── muqawil/                 → Contractors data pipeline (14,089 records, 80.7% completeness)
│   │   ├── muqawil_scraper.py   → Web scraper for contractor data
│   │   ├── requirements.txt     → Pipeline-specific dependencies
│   │   ├── pipeline/            → Processing scripts (21 files)
│   │   ├── output/              → Pipeline output: cleaned_contractors.json, muqawil_contractors.csv/xlsx
│   │   └── output_test/         → Test output directory
│   ├── engineering_offices/     → Ministry engineering offices pipeline (inactive — all zeros in last_activity_stats.json)
│   └── file_sync/               → Tri-directional sync engine (Local ↔ Drive ↔ GitHub)
│       ├── sync_engine.py       → Master orchestrator
│       ├── scan_local.py / scan_drive.py / scan_github.py → Source scanners
│       ├── sync_to_drive.py / sync_to_github.py / sync_to_local.py → Target writers
│       ├── build_manifest.py    → Unified manifest builder
│       ├── detect_conflicts.py / resolve_conflicts.py → Conflict handling
│       ├── backup_manager.py    → Pre-sync backups
│       └── 00_START_HERE.md     → Setup & usage guide
│
├── presentations/               → All presentation files
│   ├── english/
│   │   └── AI_Sales_OS_Presentation.pptx       → Main English technical deck (v4.1)
│   ├── arabic/
│   │   ├── عرض_تقديمي_AI_Sales_OS_v4.1.pptx   → Arabic v4.1 (latest)
│   │   └── عرض_تقديمي_v2.pptx                 → Arabic v2 overview
│   └── ceo_pitch/
│       ├── AI_Sales_OS_CEO_Pitch_v2.pptx       → Executive pitch deck (Arabic)
│       └── MUHIDE_Executive_Deck.pptx          → MUHIDE executive presentation
│
├── data/                        → Operational data
│   ├── imports/                 → Initial data import files (companies + contacts)
│   ├── logs/                    → Sync run logs and runtime stats JSON
│   ├── mapping/                 → Apollo↔Notion field mapping + setup tracker
│   └── snapshots/               → Point-in-time JSON snapshots
│
├── docs/                        → Documentation
│   ├── reports/                 → Generated reports
│   │   ├── EXECUTION_PLAN_v3.2.docx → Master execution plan (phases 1–4)
│   │   ├── AI_Sales_OS_Deep_Analysis.md → 12-section system analysis (v4.1)
│   │   ├── AI_Sales_OS_Comprehensive_Audit.docx → Comprehensive audit report
│   │   ├── AI_Sales_OS_Revenue_Gap_Analysis.docx → Revenue gap analysis
│   │   ├── AI_Sales_OS_المرجع_الشامل_v5.1.docx → Arabic comprehensive reference document (all 16 sections)
│   │   ├── AI_Sales_OS_Audit_CLAUDE_vs_Code_v5.1.docx → Forensic audit: CLAUDE.md vs actual code (40 findings)
│   │   ├── MUHIDE_AI_Sales_OS_Strategic_Report.docx → Combined strategic report: AI Sales OS + MUHIDE market positioning
│   │   └── AI_Sales_OS_دليل_التنفيذ_البرمجي.docx → Arabic developer implementation guide
│   ├── ops/                     → Operational reference docs (moved from root 2026-04-11)
│   │   ├── MANUAL.md            → System operation manual
│   │   ├── RUNBOOK.md           → Production runbook & incident response
│   │   ├── COMMAND_MAP.md       → Quick command reference map
│   │   ├── V2_BLUEPRINT.md      → v2.0 Operator-First blueprint
│   │   ├── FOLDER_REORG.md      → Folder reorganization planning doc
│   │   └── Gate2_Outreach_Playbook.md → Gate #2 outreach execution playbook
│   ├── notion-ops/              → Notion workspace setup and operator pages
│   │   ├── lead_inbox/          → Lead Inbox page structure
│   │   ├── today_page/          → اليوم page structure
│   │   ├── sidebar.md           → Notion sidebar layout
│   │   └── sidebar_live.md      → Live sidebar configuration
│   ├── architecture/            → Technical architecture documentation
│   │   ├── System Architecture/ → Technical architecture + field mapping + assessment docs
│   │   ├── MUHIDE_Brand_Identity_Guide.md → Brand guidelines
│   │   └── GITHUB_SETUP_GUIDE.md → GitHub Actions setup instructions
│   ├── setup/                   → Setup and migration guides
│   │   ├── Phase 1 - Notion Setup/ → Notion database setup documentation
│   │   ├── Phase 2 - Data Import/ → Data import strategy and guides
│   │   └── Phase 3 - Apollo API Pull/ → Apollo API integration documentation
│   └── muhide/                  → MUHIDE-specific documentation
│
├── commands/                    → CLI command reference (6 shell scripts)
│   ├── 00_README.md             → Command guide & recommended daily sequence
│   ├── 01_project_full_pipeline.sh → Full project pipeline commands (Sync→Score→Action→Monitor)
│   ├── 02_governance.sh         → Governance & data quality commands
│   ├── 03_scoring.sh            → Scoring & classification commands
│   ├── 04_cleanup.sh            → Cleanup & maintenance commands
│   ├── 05_muqawil_pipeline.sh   → Muqawil contractors pipeline commands
│   └── 06_engineering_offices.sh → Engineering offices pipeline commands
│
├── .claude/skills/              → 12 Claude Skills for AI Sales OS operations
├── .github/workflows/           → daily_sync.yml (CI/CD — 2-job pipeline: Job1 Sync/Score + Job2 Action/Track + weekly calibration)
├── archive/                     → Superseded scripts, old docs, old presentations
└── .gitignore
```

---

## Active Scripts

| Script | Module | Purpose | Status |
|--------|--------|---------|--------|
| `core/constants.py` | core | Unified field names, score thresholds, SLA hours, seniority normalization map, ICP_INDUSTRY_SCORES, STAGE_INFER_FROM_OUTREACH | **ACTIVE** |
| `core/notion_helpers.py` | core | Shared Notion API utilities (create, update, preload, rate limiter) | **ACTIVE** |
| `core/daily_sync.py` | core | Apollo → Notion sync engine (**v5.3**, Company-Centric: Apollo-First Ownership Priority, Primary/Supporting Owner, Company Metrics, Company Stage derivation, 3 modes, local timestamp filter, seniority normalization, safe booleans, Apollo signals + AI fields, **AI Sales Actions raw block** from typed_custom_fields, **Enrichment Layer** via `organizations/enrich` — fills Industry/Employees/Revenue/Keywords/Technologies) | **ACTIVE** |
| `core/doc_sync_checker.py` | core | Documentation drift validator [v4.1] | **ACTIVE** |
| `scoring/lead_score.py` | scoring | Lead Score v1.5 (0-100) + Lead Tier (HOT/WARM/COLD) + Sort Score — v1.5 adds Industry Fit (15%) + Recency Tiebreaker | **ACTIVE** |
| `scoring/action_ready_updater.py` | scoring | Evaluates 5 conditions to set Action Ready checkbox | **ACTIVE** |
| `scoring/score_calibrator.py` | scoring | Self-learning weight adjustment based on actual outcomes (v1.5 weights fixed) | **ACTIVE (v4.0)** |
| `scoring/company_priority_scorer.py` | scoring | Company Priority Score (Decision Layer v7.0) — computes CPS + Priority Tier + Best Contact + Next Action per company | **ACTIVE (v7.0)** |
| `automation/auto_tasks.py` | automation | Action Engine v2.0 — Company-Centric: ONE task per company per tier (HOT→"Urgent Call", WARM→"Follow-up"), Task Owner from Primary Company Owner, company-level dedup, bulk preload for owners | **ACTIVE** |
| `automation/auto_sequence.py` | automation | Auto-enrolls Action Ready contacts into Apollo Sequences | **ACTIVE (v4.0)** |
| `automation/outcome_tracker.py` | automation | Outcome Tracker v1.0 — closes Task → Contact loop: sets Contact Responded, Last Contacted, Meeting Booked. Filters auto-closed bulk tasks. Idempotent. Requires NOTION_DATABASE_ID_TASKS + NOTION_DATABASE_ID_CONTACTS (no hardcoded fallbacks). | **ACTIVE** |
| `automation/lead_inbox_mover.py` | automation | **v0.2** — Moves Qualified leads from 📥 Lead Inbox into real Company + Contact records. Two modes: `backfill` (retroactive for already-Moved leads missing CRM refs) and `forward` (new Qualified leads). Dedup: Company by Domain → Name, Contact by Email. Writes CRM Company Ref, CRM Contact Ref, CRM Sync State, CRM Synced At back to Lead Inbox. Generic email domains excluded from domain dedup. Pipe-separated multi-person emails are stripped and flagged in Notes. | **ACTIVE (v0.2)** |
| `governance/ingestion_gate.py` | governance | Ingestion Gate v6.0 — validates companies (≥2 of 5 ICP criteria) and contacts (all 4 gates) before entry into Notion; prevents junk data at source | **ACTIVE (v6.0)** |
| `governance/data_governor.py` | governance | Data Governor v6.1 — audits existing Notion records against ingestion gates, archives unqualified, enforces company-contact links and owner assignment, generates data quality report | **ACTIVE (v6.1)** |
| `governance/audit_ownership.py` | governance | Audits ownership gaps across all 5 Notion DBs (Contacts, Companies, Tasks, Meetings, Opportunities) and reports unowned records | **ACTIVE** |
| `enrichment/job_postings_enricher.py` | enrichment | Intent proxy — uses Apollo Job Postings API for intent scoring | **ACTIVE (v4.0)** |
| `enrichment/analytics_tracker.py` | enrichment | Apollo Analytics → Notion engagement sync | **ACTIVE (v4.0)** |
| `enrichment/muhide_strategic_analysis.py` | enrichment | AI engine — scores all companies vs MUHIDE ICP (Fit Score + Priority) | **ACTIVE** |
| `meetings/meeting_tracker.py` | meetings | Meeting sync v2.0 — Company-Centric: auto-links Company from Contact, propagates Company Stage → Meeting, assigns Meeting Owner from Primary Company Owner | **ACTIVE** |
| `meetings/meeting_analyzer.py` | meetings | Claude AI analysis of meeting notes → key takeaways, sentiment, next steps | **ACTIVE (v4.1) — requires ANTHROPIC_API_KEY** |
| `meetings/opportunity_manager.py` | meetings | Opportunity Manager v2.0 — Company-Centric: ONE active opportunity per company, stakeholder tracking, Buying Committee Size, company-level stage advancement, stale deal detection (14 days) | **ACTIVE** |
| `monitoring/health_check.py` | monitoring | Post-pipeline health validator (checks stats files for anomalies) | **ACTIVE** |
| `monitoring/morning_brief.py` | monitoring | Daily intelligence report (urgent calls, tasks, replies, stats) | **ACTIVE (v4.0)** |
| `monitoring/dashboard_generator.py` | monitoring | Pulls live Notion Contacts + Companies data → aggregates by account → injects into Sales_Dashboard_Accounts.html via regex template injection | **ACTIVE (v4.2)** |
| `webhooks/webhook_server.py` | webhooks | Apollo webhook receiver (logs → scripts/webhooks/logs/webhook_events.log) | **ACTIVE** |
| `webhooks/verify_links.py` | webhooks | Contact-company link verifier | **ACTIVE** |
| `core/ai_sales_actions_parser.py` | core | Parses Apollo AI Sales Actions typed_custom_field (Decision #26) — used by ai_sales_actions_enricher | **ACTIVE** |
| `enrichment/ai_sales_actions_enricher.py` | enrichment | Parses AI Sales Actions raw block → writes sub-fields (AI Priority, AI Fit, AI Tone, AI Call Hook) to Companies DB (now in pipeline v7.0) | **ACTIVE — now in pipeline (v7.0)** |
| `enrichment/reply_intelligence.py` | enrichment | Reply Intelligence Engine — classifies replied contacts (Status/Reason/Probability/Action/Confidence), writes 6 AI fields, idempotent, independent layer | **ACTIVE** |
| `governance/full_reset_notion.py` | governance | ⚠️ **DANGER: Full Notion DB wipe** — archives/deletes all records. NEVER run in production. Dev/reset tool only. | **ADMIN ONLY** |

**Log file locations (v6.2 fix):** All scripts now write logs to their own module subdir relative to the script file:
- `scripts/core/daily_sync.log`, `scripts/scoring/lead_score.log`, `scripts/automation/auto_tasks.log`, etc.
- This ensures GitHub Actions artifact upload paths match actual log locations.
- Logs are gitignored via `*.log` pattern.

Superseded scripts (still in archive/ but replaced by core/daily_sync.py):
- `sync_companies.py`, `sync_contacts.py`, `apollo_sync_scheduler.py`, `initial_load_from_csv.py`

---

## core/daily_sync.py — Sync Engine v5.3 (Company-Centric + Enrichment)

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
- **Seniority Normalization:** Uses `SENIORITY_NORMALIZE` dict from core/constants.py to unify "C-Suite"/"C suite"/"c-suite" variants.
- **Safe Boolean Writing:** Only writes engagement checkboxes (Email Sent, Replied, etc.) if Apollo explicitly returns the field — prevents overwriting manual True with False.
- **Rate Limiting:** 5x exponential backoff on 429/500 errors.
- **Parallel Workers:** `MAX_WORKERS = 3` for Notion writes.
- **Local Timestamp Filter (v4.2):** After Apollo fetch, a client-side filter drops any record whose `updated_at` is before the requested `since` datetime. Fixes issue where Apollo's date-only API filter was returning all 44,877 contacts on every incremental run, causing 4-5 hour runtimes instead of minutes.
- **Contact Qualification Filter (v4.4):** After fetching contacts, applies two hard gates before sync: (1) `owner_id` must exist, (2) `emailer_campaign_ids` must be non-empty with at least one non-failed campaign. Contacts that fail either condition are skipped entirely. This ensures only real, owned, outreached contacts enter Notion.
- **Contact Owner Sync (v4.4):** Maps Apollo `owner_id` to display names (Ibrahim/Ragheed/Soha) via `APOLLO_OWNER_MAP` in core/constants.py. Writes to `Contact Owner` field in Notion as **rich_text**. The Notion schema confirms the field type is `text` (rich_text) — code and schema are aligned. Written via `_rt()` helper in core/daily_sync.py.
- **Company Ownership (v5.1 — Apollo-First):** After contact sync, runs `compute_company_ownership(contacts, company_lookup, accounts=accounts)` with priority logic: **(1)** if the Apollo Account has `owner_id` → mapped via `APOLLO_OWNER_MAP` becomes Primary Company Owner and Supporting Owners is cleared (Apollo is authoritative); **(2)** otherwise falls back to v5.0 contact-based logic (owner with most contacts, tie-break: most recent activity → Primary; others → Supporting). Unknown `owner_id` values log a warning and drop to fallback. Writes Primary Company Owner as select, Supporting Owners as rich_text. See Decision #27.
- **Company Metrics (v5.0):** `compute_company_metrics()` writes Active Contacts count, Emailed Contacts count, Engaged Contacts count, Last Engagement Date, and Sales OS Active checkbox per company.
- **Company Stage (v5.0):** `compute_company_stage()` derives stage from contact signals: Meeting Booked → "Meeting", Replied/Opened → "Engaged", Email Sent → "Outreach", else → "Prospect". Respects priority — does NOT overwrite Meeting, Opportunity, Customer, or Churned stages.
- **Apollo Signals (v4.3):** Contacts sync now pulls Intent Strength, Job Change Event/Date, and AI Decision from `typed_custom_fields`. Companies sync now pulls Headcount Growth (6/12/24 month) and AI Qualification Status/Detail from `typed_custom_fields`.
- **Enrichment Layer (v5.3):** After fetching accounts from `accounts/search` (which does NOT return industry, employees, or revenue), calls Apollo's `organizations/enrich` endpoint per-account to fill missing firmographic data. Merges enrichment data (industry, estimated_num_employees→num_employees, annual_revenue, keywords, technology_names→technologies, short_description, annual_revenue_printed→estimated_annual_revenue) into account dicts BEFORE `sync_companies()`. Controlled via `--enrich-mode` flag: `missing` (default, only enrich accounts with empty critical fields), `all` (all accounts with domain), `force` (ignore 30-day cache), `skip` (disable). Rate-limited: 0.3s between requests + exponential backoff on 429/5xx. 30-day disk cache (`enrich_cache.json`) prevents redundant API calls. Per-account failure is non-fatal — logged and skipped. `--enrich-limit N` caps enrichment count per run.
- **Engagement Booleans (v5.3 audit note):** The `bool_fields` block in `format_contact_from_api()` (Email Sent, Replied, etc.) is a dead code path — Apollo `contacts/search` does not include these keys. The actual source for engagement booleans is `enrichment/analytics_tracker.py`. Block retained as defensive safety net.

### Commands

```bash
python core/daily_sync.py --mode incremental --days 7    # last 7 days
python core/daily_sync.py --mode backfill --days 365      # full year with checkpoint
python core/daily_sync.py --mode full                     # everything (2-4 hours)
python core/daily_sync.py                                 # defaults to incremental --hours 24

# Enrichment control
python core/daily_sync.py --mode incremental --enrich-mode missing   # enrich only empty fields (default)
python core/daily_sync.py --mode incremental --enrich-mode all       # enrich all accounts with domain
python core/daily_sync.py --mode incremental --enrich-mode force     # ignore cache, re-enrich everything
python core/daily_sync.py --mode incremental --enrich-mode skip      # skip enrichment entirely
python core/daily_sync.py --mode incremental --enrich-limit 100      # cap at 100 enrichments per run
python core/daily_sync.py --mode incremental --dry-run               # log what would be enriched, no API calls
```

---

## scoring/lead_score.py — Scoring Engine

Now writes **Lead Score** (0-100), **Lead Tier** (HOT/WARM/COLD select), and **Sort Score** in a single update.

### Formula (v1.5 — current calibrated weights)

```
Score = (Intent × 10%) + (Engagement × 10%) + (Company Size × 35%) + (Seniority × 30%) + (Industry Fit × 15%)
Sort Score = (Lead Score × 100) + Recency Bonus (0-100)
```

**v1.5 changes from v1.1:** Added Industry Fit (15%) — MUHIDE ICP alignment. Reduced Size 45%→35%, Seniority 35%→30%.

**Sort Score purpose:** Breaks the 56% ceiling effect (HOT leads all at 100/100). Sort by `Sort Score DESC` in Notion HOT views — untouched leads (never contacted) surface first, recently contacted leads drop to bottom within the same score tier.

**Industry Fit Score:** Defined in `ICP_INDUSTRY_SCORES` in scoring/constants.py. Financial Services/Banking/FinTech = 100, Retail/Entertainment = 15-20, Unknown = 30.

**Why these weights?** Most contacts are cold Apollo data with no outreach history. Intent and Engagement are mostly empty, so giving them high weight would make scores meaninglessly low. Size, Seniority, and Industry are available for nearly all records and provide the best signal right now.

### Future v2.0 weights (activate ONLY when signals data exists)

```
Score = (Intent × 30%) + (Engagement × 25%) + (Signals × 25%) + (Size × 10%) + (Seniority × 10%)
```

**IMPORTANT:** Do NOT switch to v2.0 weights until job postings, job change, and intent trend data are actually populated. Giving 25% weight to empty fields would weaken all scores.

### Lead Classification

**NOTE:** The code implements exactly 3 tiers. WARM-HIGH was removed — the code uses HOT/WARM/COLD only.

| Tier | Score | Task Type | Action | SLA |
|------|-------|-----------|--------|-----|
| **HOT** | ≥ 80 | Urgent Call | Call today — high-value decision makers | 24 hours |
| **WARM** | ≥ 50 | Follow-up | Follow up via email | 48 hours |
| **COLD** | < 50 | — | No action — monitor only | — |

### Expected Calibration Targets

- HOT: 0.5–2% of total contacts
- WARM: 10–20%
- COLD: 80%+ (normal for cold Apollo data — this is expected, not a problem)

### Commands

```bash
python scoring/lead_score.py                # score unscored contacts only
python scoring/lead_score.py --force        # recalculate ALL scores
python scoring/lead_score.py --dry-run      # calculate but don't write
```

---

## automation/auto_tasks.py — Action Engine v2.0 (Company-Centric)

Creates Notion tasks at the **company level** for Action Ready contacts. ONE task per company per tier, not one per contact.

### Priority Rules

| Tier | Min Score | Priority | Task Type | Action | Channel | SLA |
|------|-----------|----------|-----------|--------|---------|-----|
| **HOT** | ≥ 80 | Critical | **Urgent Call** | CALL | Phone | 24 hours |
| **WARM** | ≥ 50 | High | **Follow-up** | FOLLOW-UP | Email | 48 hours |

**IMPORTANT:** HOT uses task_type = "Urgent Call" and WARM uses "Follow-up". These MUST be different so company-level dedup does not block HOT tasks when a WARM task already exists for the same company. (Fixed in C-03.)

### Company-Centric Rules (v5.0)

- **ONE task per company per task type** — contacts are grouped by company, best-scored contact selected as primary
- **Task Owner** = Primary Company Owner (from Companies DB) → fallback to Contact Owner
- **Owner Source** field tracks provenance: "Company Primary" or "Contact Owner"
- **Company context** in task description shows all contacts at the company with scores
- **Company Stage at Creation** recorded for audit trail

### Duplicate Prevention

Before creating a task, checks the Tasks DB for any existing open task (Status ≠ "Completed") linked to the same **company** with the same task type. If one exists, the company is skipped.

### Commands

```bash
python automation/auto_tasks.py                    # create tasks for all Action Ready contacts
python automation/auto_tasks.py --dry-run          # show what would be created
python automation/auto_tasks.py --limit 20         # limit to first N contacts (testing)
python automation/auto_tasks.py --mark-overdue     # only check and log overdue tasks
```

---

## scoring/action_ready_updater.py — Action Ready Evaluator

Evaluates and writes the `Action Ready` checkbox for all scored contacts. A contact is Action Ready ONLY if ALL 5 conditions are met:

1. Lead Score >= 50
2. Do Not Call = False
3. Outreach Status NOT in {Do Not Contact, Bounced, Bad Data}
4. Stage is NOT "Customer" or "Churned"
5. Has at least one contact method (email or phone)

### Commands

```bash
python scoring/action_ready_updater.py              # update all scored contacts
python scoring/action_ready_updater.py --dry-run    # show what would change
```

---

## monitoring/health_check.py — Pipeline Health Validator

Runs after the pipeline to validate results by checking stats JSON files.

### Checks

- **CRITICAL:** Zero records processed (sync may have failed)
- **WARNING:** High duplicate rate (>5%)
- **WARNING:** Failed records in sync
- **WARNING:** Action Engine errors
- **INFO:** Zero tasks created (all contacts may already have open tasks)

### Commands

```bash
python monitoring/health_check.py              # run all checks
python monitoring/health_check.py --strict     # exit 1 on any warning (not just critical)
```

---

## enrichment/job_postings_enricher.py — Intent Proxy (v4.0)

Uses Apollo's Job Postings API as a proxy for Intent Score. Companies that are actively hiring in relevant roles = higher buying intent.

### Scoring Components (0-100)
- **Job Volume (0-40):** Number of open positions
- **Recency (0-20):** How recently jobs were posted
- **Relevance (0-25):** Keywords matching our solution areas (insurance, risk, compliance, finance, etc.)
- **Growth Signals (0-15):** Hiring across multiple departments

Writes `Job Postings Intent` to Companies DB, then propagates to linked Contacts' `Primary Intent Score`. Uses 7-day cache to avoid redundant API calls.

### Commands

```bash
python enrichment/job_postings_enricher.py                    # enrich all HOT/WARM companies
python enrichment/job_postings_enricher.py --dry-run          # preview without writing
python enrichment/job_postings_enricher.py --limit 20         # limit to first N companies
python enrichment/job_postings_enricher.py --tier HOT         # only HOT companies
python enrichment/job_postings_enricher.py --no-cache         # ignore 7-day cache
```

---

## automation/auto_sequence.py — Auto Sequence Enrollment (v4.0)

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
python automation/auto_sequence.py                     # enroll all eligible contacts
python automation/auto_sequence.py --dry-run           # preview without enrolling
python automation/auto_sequence.py --limit 10          # limit to first N
python automation/auto_sequence.py --tier HOT          # only HOT contacts
python automation/auto_sequence.py --sender ragheed    # force specific sender
```

---

## enrichment/analytics_tracker.py — Analytics & Engagement Sync (v4.0)

Pulls Apollo Analytics data and syncs engagement signals back to Notion contacts. Closes the feedback loop by bringing real engagement data into the CRM.

### What It Does

1. **Engagement Sync:** Checks contacts in active outreach (In Sequence, Sent, Opened) and updates Notion booleans (Replied, Email Opened, Email Sent) from Apollo data
2. **Analytics Report:** Generates performance reports broken down by seniority, company size, and weekly trends

### Commands

```bash
python enrichment/analytics_tracker.py                    # full sync + report
python enrichment/analytics_tracker.py --dry-run          # preview without writing
python enrichment/analytics_tracker.py --days 7           # last N days
python enrichment/analytics_tracker.py --export           # save report to file
python enrichment/analytics_tracker.py --skip-sync        # report only, no Notion writes
```

---

## scoring/score_calibrator.py — Self-Learning Weights (v4.0)

Analyzes actual engagement outcomes and recommends weight adjustments for scoring/lead_score.py. The feedback loop: Score → Action → Outcome → Calibrate → Better Score.

### Safety Rails

- `MAX_WEIGHT_CHANGE = 0.10` per cycle (no sudden jumps)
- `MIN_WEIGHT = 0.05` (no component goes to zero)
- `MIN_EMAILS_FOR_CALIBRATION = 100` (need enough data)
- Saves full history in `calibration_history.json`
- Never auto-applies unless `--apply` flag is explicitly used

### Commands

```bash
python scoring/score_calibrator.py                  # analyze + recommend (no changes)
python scoring/score_calibrator.py --apply          # apply recommended weights
python scoring/score_calibrator.py --days 90        # analyze last 90 days
python scoring/score_calibrator.py --export         # save analysis to file
```

**IMPORTANT:** Weekly pipeline runs calibrator in review-only mode (no --apply). Manual review required before applying.

---

## monitoring/morning_brief.py — Daily Intelligence Report (v4.0)

Generates a daily morning brief with everything a sales rep needs to know.

### Sections

1. **Urgent Calls:** HOT leads not yet contacted
2. **Today's Tasks:** Due today + overdue
3. **Recent Replies:** Contacts that responded
4. **Pipeline Summary:** HOT/WARM/COLD counts
5. **Email Performance:** Last 7 days from Apollo Analytics

### Commands

```bash
python monitoring/morning_brief.py                 # generate today's brief (stdout)
python monitoring/morning_brief.py --output file   # save to markdown file
python monitoring/morning_brief.py --days 1        # look back N days for activity
```

---

## core/constants.py — Unified Constants

Single source of truth for all field names, score thresholds, SLA hours, and seniority normalization. Changing a field name here changes it across all scripts that import from core/constants.

Key exports: `FIELD_*` constants, `SCORE_HOT`/`SCORE_WARM`, `SLA_*_HOURS`, `SENIORITY_NORMALIZE`, `OUTREACH_BLOCKED`, `COMPANY_STAGE_*` values, `TEAM_MEMBERS` set, `APOLLO_OWNER_MAP`

**Intent helpers (v6.1 — Decision #28):** `has_real_intent(record) → (bool, [reasons])`, `company_has_real_intent(contacts) → (bool, [reasons])`, `EMAIL_OPEN_COUNT_INTENT_THRESHOLD = 2`, `INTENT_REASON_*` labels, `FIELD_INTERNAL_FORWARD_DETECTED`, `FIELD_REPEATED_ENGAGEMENT_DETECTED`, `FIELD_HAS_INTENT_SIGNAL`.

**Stage conflict guards (v6.1 — Decision #29):** `STAGE_PRIORITY` lattice (Prospect=1 → Archived=8), `STAGE_TERMINAL = {Customer, Churned, Archived}`, `is_stage_regression(current, new) → bool`. Unknown current stage is treated as priority 0 (never blocks forward progress).

**Freshness guard (v6.1 — Decision #29):** `FRESHNESS_MAX_AGE_HOURS = 26`, `FRESHNESS_STATS_FILES = (enrichment/last_analytics_stats.json, automation/last_outcome_stats.json, meetings/last_meeting_tracker_stats.json)`, `check_pipeline_freshness(base_dir, max_age_hours) → {fresh, checked, oldest_age_hours, max_age_hours}`. Used by `data_governor` as Step 0 of `run()` — downgrades enforce→dry-run on stale signals.

---

## Notion Schema

### Companies Database

Key fields: Name, Domain, Industry, Employee Count, Apollo Account ID (primary key), Website, Phone, Country, City, Annual Revenue, Headcount Growth 6M/12M/24M, AI Qualification Status (Qualified/Disqualified/Possible Fit), AI Qualification Detail, Company Owners (multi-select: derived from Contact Owners), **Primary Company Owner** (select: Ibrahim/Ragheed/Soha — owner with most contacts), **Supporting Owners** (rich_text: other owners), **Company Stage** (select: Prospect/Outreach/Engaged/Meeting/Opportunity/Customer/Churned/Archived), **Active Contacts** (number), **Emailed Contacts** (number), **Engaged Contacts** (number), **Last Engagement Date** (date), **Account Engagement Score** (number 0-100), **Buying Committee Strength** (select: Strong/Moderate/Weak), **Company Health** (select: Green/Yellow/Red), **Sales OS Active** (checkbox)

### Contacts Database

Key fields: Name, Email, Title, Seniority, Lead Score (number 0-100), Lead Tier (HOT/WARM/COLD select), Action Ready (checkbox), **Contact Owner** (**text/rich_text** — Notion field type confirmed as `text`. Written by core/daily_sync.py via `_rt()` as plain text: Ibrahim/Ragheed/Soha. Code and schema are aligned — no mismatch.), Intent Score, Intent Strength, Outreach Status, Stage, Do Not Call, Email Sent/Opened/Bounced, Replied, Meeting Booked, Demoed, Last Contacted, Contact Responded, First Contact Attempt, Opportunity Created, Job Change Event, Job Change Date, AI Decision, Email Open Count, Emails Sent Count, Emails Replied Count, Apollo Contact ID (primary key), Company (relation to Companies)

### Tasks Database

Key fields: Task Title (title), Priority (select: Critical/High/Medium/Low), Status (**status type** — NOT select — values: "Not Started"/"In Progress"/"Completed"), Due Date, Start Date, Task Type, Team, Contact (relation), Company (relation), Opportunity (relation), Context, Description, Expected Outcome, Auto Created (checkbox), Automation Type (select), Trigger Rule, Completed At, **Task Owner** (select: Ibrahim/Ragheed/Soha), **Owner Source** (select: Company Primary/Contact Owner/Manual), **Company Stage at Creation** (rich_text)

**IMPORTANT:** Tasks DB Status field is `status` type, not `select`. Use `{"status": {"name": "Not Started"}}` not `{"select": ...}`.

### Opportunities Database (v5.0 Company-Centric)

Key fields: Opportunity Name (title), Stage (**status type**: Discovery/Proposal/Negotiation/Closed Won/Closed Lost), Deal Value, ARR, Probability (select), Expected Close Date, Actual Close Date, Deal Health (select: Green/Yellow/Red), Risk Level, Blockers, Next Action, Notes, Primary Contact (relation), Company (relation), Opportunity Owner (select), Team, Currency, Contract Term, Record Source, Opportunity ID, **Stakeholder Contacts** (rich_text: names of all involved contacts), **Company Owner Snapshot** (rich_text), **Buying Committee Size** (number), **Decision Maker Identified** (checkbox), **Revenue Priority** (select: Tier 1/Tier 2/Tier 3)

### Meetings Database (v5.0 Company-Centric)

Key fields: Meeting Title (title), Meeting Type (select), Scheduled Date, Duration, Outcome (select), Meeting Notes, Key Takeaways, Decision Made, Next Steps, Meeting Link, Number of Attendees, Meeting Organizer, Timezone, Primary Contact (relation), Company (relation), Opportunity (relation), Agenda, **Meeting Owner** (select: Ibrahim/Ragheed/Soha), **Participants** (rich_text), **Outcome Impact** (select: Stage Advance/No Change/Stage Regress), **Next Step Owner** (select: Ibrahim/Ragheed/Soha)

### Lead Inbox Database (v2.0 Operator-First — NEW 2026-04-10)

Live URL: https://www.notion.so/b9ae8e060ca64fc9a7f5d8706e229b59 | Data Source ID: `64aec610-22b2-4444-a8a5-80c238a86633`

Single intake point for all non-Apollo leads. 12 fields: Name (title), Source (select: **6 values** — Manual/Referral/Import/Muqawil/Other/Apollo-reserved; Business Card is handled via Source=Manual + Notes prefix "من معرض/حدث:"), Company Name (rich_text), Email, Phone, Title (rich_text), **Status (status type)** with **fully customized options**: New/Review (In progress)/Qualified/Rejected/Duplicate/Moved (Complete group), Warm Signal (rich_text), Intake Owner (select: Ibrahim/Ragheed/Soha), Intake Date (date), Notes (rich_text), Rejection Reason (select: Not ICP/No Contact Info/Duplicate/Low Quality/Other). State machine: New → Review → Qualified/Rejected/Duplicate → Moved. **5 Arabic views active:** 🆕 جديد (Status=New), 🔍 قيد المراجعة (Status=Review), ✅ جاهز للنقل (Status=Qualified), 🗄️ مؤرشف (Status IN Moved/Rejected/Duplicate), 📋 كل السجلات (grouped by Status). **3 templates:** ➕ Manual, 🤝 Referral (with "من أحاله" body), 💳 Business Card (Source=Manual + Notes prefix). Validation checklist page "✅ 📥 Lead Inbox — Validation Checklist" with 12 tests attached in Notion.

### ⭐ اليوم Page (v2.0 Operator-First — NEW 2026-04-10)

Live URL: https://www.notion.so/33e69eddf30181548db3cbe78bfc7a71

The single page the operator opens each morning. 6 sections: Header/System Status, 📞 اتصل اليوم (linked Tasks: Urgent Call, Due ≤ today), ✉️ تابع اليوم (linked Tasks: Follow-up, Due ≤ today), 💼 الصفقات (linked Opportunities: Stage not Closed), 📥 Inbox Summary (linked Lead Inbox: Status = New), 📝 ملاحظات اليوم (daily toggles). Linked database view blocks must be inserted manually in Notion UI (API cannot create linked view blocks); the page contains HTML comment placeholders with the exact spec for each view.

### Other Databases

Activities, Email Hub — used for execution workflow.

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
6. **No unowned contacts.** Every contact synced MUST have an Apollo owner_id. Contacts without owners are filtered before sync.
7. **No untouched contacts.** Every contact synced MUST have been enrolled in at least one email campaign with a non-failed status. Raw Apollo data with no outreach is not synced.
8. **Company Owners = derived.** Company Owners multi-select is computed from Contact Owners, NOT from Apollo Account owner_id (which is usually null).

---

## GitHub Actions Pipeline (v7.0 — Decision Layer + AI Sales Actions in Pipeline)

**File:** `.github/workflows/daily_sync.yml`
**Schedule:** Daily at 7:00 AM KSA (04:00 UTC)
**Version:** 7.0 (Decision Layer v7.0 — Decision #33 + AI Sales Actions Enricher in pipeline + Company Priority Scorer)

### Why 2 Jobs?
The pipeline was exceeding GitHub's 6-hour per-job limit. Splitting into 2 sequential jobs gives each its own 6-hour clock — total capacity: ~9 hours.

### Safe Execution Order (Decision #29)
All signal-writing scripts (analytics_tracker, outcome_tracker, meeting_tracker, opportunity_manager) must run **before** `lead_score` + `action_ready_updater` so scoring reads fresh engagement and stage data, not yesterday's values.

### Job 1: `sync-and-score` — timeout 5h 50min (Sync → Signals → Decision → Score)
1. Checkout repository
2. Setup Python 3.11 with pip cache
3. Install dependencies
4. `python scripts/core/daily_sync.py --mode incremental --hours 26 --enrich-mode missing` (sync + enrichment; fetches accounts, enriches missing firmographics via `organizations/enrich`, syncs to Notion; `compute_company_stage` guarded by `STAGE_TERMINAL` + `is_stage_regression`)
5. `python scripts/enrichment/ai_sales_actions_enricher.py` (**NEW v7.0** — parses Apollo AI Sales Actions block → writes AI Priority, AI Fit, AI Tone, AI Call Hook to Companies DB, continue-on-error)
6. `python scripts/enrichment/analytics_tracker.py --days 7` (writes `email_open_count`, Replied, Email Opened before scoring reads them, continue-on-error)
7. `python scripts/automation/outcome_tracker.py --execute` (writes Contact Responded, Last Contacted, Meeting Booked, continue-on-error)
8. `python scripts/meetings/meeting_tracker.py --days 7` (Company Stage → Meeting, guarded, continue-on-error)
9. `python scripts/meetings/opportunity_manager.py` (Company Stage → Opportunity, guarded by `STAGE_TERMINAL` + `is_stage_regression`, continue-on-error)
10. `python scripts/enrichment/job_postings_enricher.py --limit 50` (intent proxy, continue-on-error)
11. `python scripts/scoring/lead_score.py` (recalculate scores — reads fresh signals from steps 6–10)
12. `python scripts/scoring/action_ready_updater.py` (evaluate Action Ready)
13. `python scripts/scoring/company_priority_scorer.py` (**NEW v7.0** — Decision Layer: compute CPS + Priority Tier + Best Contact + Next Action per company, continue-on-error)
14. Upload sync stats as artifact → passed to Job 2 (expanded: analytics, outcome, meeting_tracker, opportunity_manager, ai_sales_actions_enricher, company_priority_scorer stats + logs all included so next-day freshness check works)

### Job 2: `action-and-track` — timeout 3h (Action → Sequence → Meet-AI → Health)
1. Checkout + Python setup + Install dependencies
2. Download sync stats from Job 1
3. `python scripts/automation/auto_tasks.py` (create tasks for Action Ready contacts, continue-on-error)
4. `python scripts/automation/auto_sequence.py --limit 50` (enroll contacts in sequences, continue-on-error)
5. `python scripts/meetings/meeting_analyzer.py --limit 10` (AI meeting intelligence, non-blocking — does not feed scoring, requires ANTHROPIC_API_KEY)
6. `python scripts/monitoring/health_check.py` (validate pipeline run)
7. (Frozen Operator-First v2.0) `morning_brief`, `dashboard_generator`, dashboard commit — unchanged
8. Upload all logs as artifacts (30-day retention)
9. Notify on failure

**Updated in v7.0:** AI Sales Actions Enricher now runs in Job 1 Step 5 (before scoring). Company Priority Scorer now runs in Job 1 Step 13 (after Action Ready). Improved decision layer: AI signals feed scoring, scoring feeds decision layer.

**Moved from Job 2 → Job 1:** analytics_tracker, outcome_tracker, meeting_tracker, opportunity_manager. **Removed from Job 2** (no longer run twice). meeting_analyzer stays in Job 2 because it's AI-only and does not feed scoring.

**Weekly Job (Sundays):** `python scripts/scoring/score_calibrator.py --days 30 --export` — runs after Job 2, review-only, no auto-apply.

**Required Secrets:** `APOLLO_API_KEY`, `NOTION_API_KEY`, `NOTION_DATABASE_ID_CONTACTS`, `NOTION_DATABASE_ID_COMPANIES`, `NOTION_DATABASE_ID_TASKS`, `NOTION_DATABASE_ID_MEETINGS`, `NOTION_DATABASE_ID_OPPORTUNITIES`, `ANTHROPIC_API_KEY` (optional)

**Manual trigger:** Available from GitHub UI with mode selection (incremental / backfill_week / backfill_month / full), enrichment mode (missing / all / force / skip), plus toggles for `run_lead_score`, `run_action_engine`, `run_sequences`.

**Cost:** Free. GitHub Actions free tier = 2,000 min/month. Daily run ≈ 30 min × 30 = 900 min/month.

---

## governance/archive_unqualified.py — Contact Archiver (v4.4)

One-time (or periodic) script to archive Notion contacts that don't meet qualification criteria. Reads ALL contacts from Notion Contacts DB, checks for Contact Owner and Email Sent, and sets Stage = "Archived" for those that fail.

### Commands

```bash
python governance/archive_unqualified.py              # archive all unqualified contacts
python governance/archive_unqualified.py --dry-run    # show what would be archived (no changes)
python governance/archive_unqualified.py --limit 50   # limit to first N contacts
```

**IMPORTANT:** Run `--dry-run` first to verify the count before archiving. This operation is reversible (you can un-archive by changing Stage back) but affects many records.

---

## governance/data_governor.py — Data Governor (v6.1)

Enforces data governance rules on ALL existing Notion records. Companion to `governance/ingestion_gate.py` — while the gate blocks bad data at entry, the governor cleans up what already exists.

### What It Does

1. **Step 0 — Freshness Guard (v6.1):** calls `check_pipeline_freshness()` before any audit. If upstream signal stats (`analytics_tracker`, `outcome_tracker`, `meeting_tracker`) are older than 26h or missing, and enforce mode was requested, **auto-downgrades to dry-run** and logs `[Timing Guard] Refusing to archive on possibly-stale engagement data`. Prevents false-positive archival on days where the analytics pipeline failed.
2. Builds per-company real-intent aggregation via `company_has_real_intent()` (Decision #28) — used by the Archive Guard below.
3. Audits companies and contacts against ingestion gate criteria.
4. **Archive Guard (v6.1):** any company/contact with real intent is spared archival even if it has soft failures (no_outreach, no_owner). Hard failures (no_company, no_email) still archive contacts.
5. Archives records that fail (sets Stage = "Archived").
6. Enforces Company-Contact linking (no orphan contacts).
7. Enforces Owner assignment (no unowned companies).
8. Generates a full data quality report including `companies_saved_by_intent` and `contacts_saved_by_intent` counters.
9. Soft-delete only — never hard-deletes active records.

### Commands

```bash
python governance/data_governor.py --dry-run          # audit only, no changes
python governance/data_governor.py --enforce          # apply archival + enforcement
python governance/data_governor.py --report           # generate detailed quality report
python governance/data_governor.py --enforce --limit 100  # limit to first N records
```

---

## governance/ingestion_gate.py — Ingestion Gate (v6.0)

Validates companies and contacts before they enter the system. Prevents junk data at source.

### Company Gate (must pass ≥ 2 of 5 criteria)

1. ICP Match (industry + country + size)
2. Has Senior Contact (C-Suite/VP/Director)
3. Has Intent Signal (email open/reply/meeting)
4. Has Trigger Event (funding/headcount growth/hiring)
5. Has been contacted (email sent / meeting / call)

### Contact Gate (must pass ALL 4)

1. Linked to a company in the system
2. Has valid email
3. Has clear role (Decision Maker / Influencer / End User)
4. Has an owner assigned

### Commands

```bash
python governance/ingestion_gate.py --dry-run           # evaluate without writing (audit mode)
python governance/ingestion_gate.py --mode strict       # apply gate decisions (strict enforcement)
python governance/ingestion_gate.py --enforce           # alias for --mode strict (same effect)
python governance/ingestion_gate.py --mode review       # pass gate+low-data records for review
python governance/ingestion_gate.py --report            # save detailed gate report to JSON
python governance/ingestion_gate.py --limit 50          # limit to first N companies
```

---

## enrichment/muhide_strategic_analysis.py — MUHIDE Strategic Analysis Engine

AI-powered analysis of all companies in Notion against MUHIDE's B2B trade governance and financing value proposition. Uses Claude API to generate a strategic fit assessment for each company.

### Output Fields (written to Companies DB)

| Field | Type | Description |
|-------|------|-------------|
| MUHIDE Strategic Analysis | rich_text | Full AI-generated analysis |
| MUHIDE Fit Score | number (1-100) | Strategic fit score |
| MUHIDE Priority | select (P1/P2/P3) | Outreach priority tier |
| MUHIDE Best Buyer | select | Ideal buyer persona at this company |
| MUHIDE Outreach Angle | rich_text | Recommended first approach/hook |

### Commands

```bash
python enrichment/muhide_strategic_analysis.py            # process all companies
python enrichment/muhide_strategic_analysis.py --dry-run  # preview without writing
python enrichment/muhide_strategic_analysis.py --limit 50 # process first N only
python enrichment/muhide_strategic_analysis.py --resume   # resume from checkpoint
```

Uses `muhide_analysis_checkpoint.json` to resume after interruptions. Requires `ANTHROPIC_API_KEY`.

---

## automation/outcome_tracker.py — Task → Contact Outcome Loop (v1.0)

Closes the feedback loop between completed Tasks and their linked Contacts. For every real completed task (not auto-closed bulk tasks), it updates the contact record to reflect what actually happened.

### What It Does

For each completed task:
1. **Contact Responded** → set to `True`
2. **Last Contacted** → set to the task's `Completed At` date (falls back to `last_edited_time`)
3. **Meeting Booked** → set to `True` if `Call Outcome = "Meeting Scheduled"`

### Key Design Decisions

- **Auto-closed filter** — skips tasks whose `Outcome Notes` contains the string `"auto-closed"` (set by `automation/cleanup_overdue_tasks.py`). This prevents bulk-closed legacy tasks from polluting contact records.
- **Idempotent** — skips contacts that already have `Contact Responded = True` AND `Last Contacted` set, unless `--force` is passed.
- **`Call Outcome` field** — meeting detection uses the `Call Outcome` select field (not keyword heuristics). This requires the sales rep to fill in the outcome field when completing a task.
- **Explicit env var failure** — requires NOTION_API_KEY, NOTION_DATABASE_ID_TASKS, NOTION_DATABASE_ID_CONTACTS. Will raise EnvironmentError immediately if any is missing. No hardcoded fallback IDs.
- **Log rotation** — uses RotatingFileHandler (5 MB per file, 3 backups) rather than timestamped per-run files to prevent unbounded log accumulation.

### Required Env Vars (all MANDATORY — no fallbacks)

```
NOTION_API_KEY
NOTION_DATABASE_ID_TASKS
NOTION_DATABASE_ID_CONTACTS
```

### Commands

```bash
python automation/outcome_tracker.py                              # dry-run (safe, no writes)
python automation/outcome_tracker.py --execute                    # apply changes
python automation/outcome_tracker.py --execute --force            # re-process already-updated contacts
python automation/outcome_tracker.py --execute --limit 20         # test with first 20 tasks
python automation/outcome_tracker.py --execute --include-auto-closed  # include bulk-closed tasks too
```

**IMPORTANT:** Always run dry-run first to confirm counts before `--execute`.

---

## automation/cleanup_overdue_tasks.py — Legacy Task Cleanup

Bulk-completes overdue auto-created tasks from pre-v5.0 contact-level Action Engine. These tasks were never actioned and are superseded by the company-level task model (v5.0). Run once after migrating to v5.0.

### Commands

```bash
python automation/cleanup_overdue_tasks.py --dry-run  # preview only
python automation/cleanup_overdue_tasks.py            # execute cleanup
python automation/cleanup_overdue_tasks.py --limit 100  # limit batch size
```

---

## automation/lead_inbox_mover.py — Lead Inbox → CRM Mover (v0.2)

Moves Qualified leads from the 📥 Lead Inbox into real Company + Contact records in the CRM. This is the bridge between Bootstrap Mode v0.1 (Lead Inbox only) and the main AI Sales OS pipeline.

### Why v0.2 (not v0.1)

v0.1 only flipped `Status = Qualified → Moved` without creating any CRM records — a cosmetic move that faked the upgrade gate. v0.2 actually creates Company and Contact records and writes back the CRM refs, so "Moved" becomes a real state.

### Modes

| Mode | Filter | Purpose |
|------|--------|---------|
| `forward` (default) | `Status = Qualified` | Process newly-qualified leads going forward |
| `backfill` | `Status = Moved AND CRM Company Ref is empty` | Retroactively create CRM records for leads that were "fake-moved" by v0.1 |
| `all` | Both above | Run forward + backfill in one pass |

### Dedup Rules

- **Company:** Domain (exact, case-insensitive, generic domains like gmail/yahoo excluded) → Name (exact match on `Company Name` title, with legal-suffix normalization) → create new
- **Contact:** Email (exact match on Contacts DB `Email` field) → create new
- **Lazy lookup:** No full preload (Contacts DB ≈ 45K). Queries run per-lead with a negative-miss cache to avoid re-querying known-missing keys in the same run.

### Fields Written Back to Lead Inbox

- `CRM Company Ref` (rich_text) — page ID of matched or created Company
- `CRM Contact Ref` (rich_text) — page ID of matched or created Contact
- `CRM Sync State` (select) — Created / Matched / Failed / Skipped
- `CRM Synced At` (date)
- `Status` → `Moved` (only on success in forward mode; backfill leaves Status untouched since it's already Moved)

### Data Quality Guards

- Invalid / pipe-separated multi-person emails (e.g. `a@x.com|b@x.com`) are stripped via regex. Original email is preserved in Notes with a `[v0.2: stripped invalid email 'X' — needs manual split]` tag. Lead falls back to phone if available.
- Missing Name, missing (email AND phone), or missing Intake Owner → lead skipped with failure reason logged.

### Required Env Vars (all mandatory — no fallbacks)

```
NOTION_API_KEY
NOTION_DATABASE_ID_LEAD_INBOX
NOTION_DATABASE_ID_COMPANIES
NOTION_DATABASE_ID_CONTACTS
```

### Commands

```bash
python automation/lead_inbox_mover.py --mode forward               # dry-run forward
python automation/lead_inbox_mover.py --mode forward --execute     # apply
python automation/lead_inbox_mover.py --mode backfill --limit 30   # batched dry-run
python automation/lead_inbox_mover.py --mode all --execute         # run both
python automation/lead_inbox_mover.py --mode backfill --verbose    # full per-lead logs
```

**Runtime:** ~12 sec per lead (lazy dedup queries + Notion rate limit). For large backfills, batch via `--limit 30` to stay under bash call timeouts.

### First Production Run — 2026-04-10 (Gate #1 Complete)

All 119 leads that had been fake-moved by v0.1 were successfully backfilled via 4 batches of `--limit 30 --execute`:

- Companies: **58 created** + **61 matched** (dedup saved us from creating 61 duplicates that already existed from Apollo sync)
- Contacts: **112 created** + **7 matched**
- Failed: **0**

Upgrade Gate #1 ("20+ leads moved from Inbox to CRM") is now met **with real records**, not just cosmetic status flips.

---

## governance/fix_seniority.py — Seniority Normalization Migration (One-Time)

One-time migration script to fix the `Seniority` field in Notion Contacts DB. Queries all contacts with `Seniority = "C suite"` and updates them to `"C-Suite"` to match the normalized value in `SENIORITY_NORMALIZE` (core/constants.py).

### Commands

```bash
python governance/fix_seniority.py              # dry-run — shows what would change
python governance/fix_seniority.py --execute    # apply the migration
python governance/fix_seniority.py --execute --batch-size 25  # custom batch size (default: 50)
```

**Run once only.** After execution, verify with a Notion filter that no `"C suite"` records remain.

---

## governance/audit_ownership.py — Ownership Audit

Audits ownership gaps across all 5 Notion databases (Contacts, Companies, Tasks, Meetings, Opportunities). Reports unowned or mis-assigned records. Useful for validating the v5.0 Company-Centric ownership model.

### Commands

```bash
python governance/audit_ownership.py          # full audit across all DBs
python governance/audit_ownership.py --fix    # auto-assign owners where possible
```

---

## pipelines/file_sync/ — Tri-Directional Sync Engine

A production-grade file synchronization module that keeps three systems in perfect sync: Local Filesystem ↔ Google Drive ↔ GitHub Repository.

### Architecture

```
Local ◄──────────────────────────────────► Google Drive
  │                                               │
  └───────────────────► GitHub ◄──────────────────┘
                           │
                    Unified Manifest
                   (source of truth)
```

### Key Modules

| Module | Purpose |
|--------|---------|
| `build_manifest.py` | Creates unified manifest of all files across all 3 sources |
| `detect_conflicts.py` | Identifies files that differ between sources |
| `sync_to_drive.py` | Pushes local changes to Google Drive |
| `sync_to_github.py` | Commits and pushes changes to GitHub |
| `sync_to_local.py` | Pulls remote changes to local |
| `backup_manager.py` | Creates pre-sync backups |
| `scan_local/drive/github.py` | Source-specific scanners |

See `pipelines/file_sync/00_START_HERE.md` for full setup and usage guide.

---

## Apollo API Endpoints Used

| Endpoint | Purpose | Mode |
|----------|---------|------|
| `contacts/search` | Fetch contacts with filters | All modes |
| `accounts/search` | Fetch companies with filters | All modes |
| `organizations/job_postings` | Job posting signals | Phase 3 (planned) |
| `organizations/enrich` | Company firmographic enrichment (industry, employees, revenue, keywords, technologies) | **Active (v5.3)** — integrated in daily_sync.py |
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
10. **Unified Constants** — All field names in core/constants.py. No hardcoded strings in individual scripts.
11. **Action Ready Gating** — 5-condition check before any task is created. Prevents tasks for DNC, bounced, churned, or contacts without contact methods.
12. **2-Job Pipeline** — Split daily_sync.yml into Job 1 (Sync/Score, 5h 50min) and Job 2 (Action/Track, 3h) to bypass GitHub Actions' 6-hour per-job limit. Stats passed via artifacts.
13. **Local Timestamp Filter** — Apollo's `contact_updated_at_range` API filter uses day-granularity and was returning all 44,877 contacts even on incremental runs. Fixed in `_fetch_with_date_filter()` with a post-fetch client-side filter using exact `updated_at >= since` comparison. Incremental runs now complete in minutes, not hours.
14. **Apollo Signals in Sync (v4.3)** — Intent Strength, Job Change Event/Date, Headcount Growth (6/12/24M), and Apollo AI fields (AI Decision, AI Qualification Status/Detail) are now extracted directly from contact/account responses during core/daily_sync.py. No separate enrichment scripts needed — signals flow with the regular sync.
15. **Apollo AI Custom Field IDs** — Apollo's AI generates typed_custom_fields with fixed IDs: Contact Decision (`6913a64c52c2780001146ce9`), Account ICP Analysis (`6913a64c52c2780001146cfd`), Account Research (`6913a64c52c2780001146d0e`), Account Qualification (`6913a64c52c2780001146d22`). IDs are stored in core/constants.py for maintainability.
16. **Owner & Outreach Gating (v4.4)** — Contacts must have an Apollo `owner_id` AND at least one non-failed email campaign before being synced to Notion. This prevents unowned or untouched contacts from cluttering the CRM. Existing contacts that don't meet criteria are archived (Stage = "Archived") via `governance/archive_unqualified.py`.
17. **Company Owners from Contacts (v4.4)** — Instead of relying on Apollo's Account `owner_id` (which is null for most accounts), Company Owners is derived automatically from Contact Owners. This creates a multi-select field showing all team members who own contacts at that company.
18. **Company-Centric Operating Model (v5.0)** — Company = Primary Operating Entity. All automation operates at the company level: ONE task per company per tier (automation/auto_tasks.py v2.0), ONE active opportunity per company (meetings/opportunity_manager.py v2.0). Primary Company Owner = owner with most contacts (tie-break: most recent activity). Company Stage state machine: Prospect → Outreach → Engaged → Meeting → Opportunity → Customer → Churned → Archived. Higher-priority stages are never overwritten by lower ones.
19. **Company-Level Task Dedup (v5.0)** — Tasks are deduplicated by Company + Task Type, not by Contact. All contacts at a company are listed in the task context. Task Owner cascades: Primary Company Owner → Contact Owner fallback.
20. **Meeting-to-Company Auto-Linking (v5.0)** — meetings/meeting_tracker.py v2.0 auto-resolves Company from Contact's company relation when meetings lack a direct Company link. Propagates Company Stage → "Meeting" (respects priority). Assigns Meeting Owner from Primary Company Owner.
21. **HOT vs WARM Task Type Separation (v5.1 Fix)** — HOT uses task_type = "Urgent Call", WARM uses "Follow-up". These must be distinct because company-level dedup checks by task_type — if both used "Follow-up", a company with an open WARM task would be blocked from receiving a HOT urgent-call task, defeating the priority system.
22. **Bulk Company Owner Preload (v5.1 Fix)** — automation/auto_tasks.py now preloads all company owner data in one query before the task-creation loop. Eliminates N+1 API pattern (was: 1 API call per company; now: 1 query for all companies).
23. **No Hardcoded Notion IDs** — automation/outcome_tracker.py was updated to require env vars explicitly (NOTION_DATABASE_ID_TASKS, NOTION_DATABASE_ID_CONTACTS) rather than using hardcoded fallback IDs. Fails loudly if env vars are missing.
24. **Rotating Log Files** — automation/outcome_tracker.py uses RotatingFileHandler (5 MB, 3 backups) instead of timestamped per-run log files to prevent unbounded accumulation.
25. **Modular Architecture (v6.0)** — Restructured from flat `💻 CODE/Phase 3 - Sync/` to 8-module modular structure: core, scoring, automation, governance, enrichment, meetings, monitoring, webhooks. Each module groups related scripts by function domain, improving maintainability and testability.
26. **AI Sales Actions Sync (2026-04-11)** — Apollo exposes the "AI Sales Actions" directive block (Segment/Fit/Priority/Urgency/Signal/Pain/Target Role/Action/Tone/Call Hook/Email) as a typed_custom_field on accounts, ID `69d979efebf741000dfbce23` (verified via `apollo_mixed_companies_search` on KAFD, stc). `scripts/core/daily_sync.py` now extracts this field in the account transform (same place as AI Qualification Status/Detail) and writes it as rich_text to the Companies DB `AI Sales Actions` property. Safe-write: only writes when non-empty, never blanks existing values. Downstream parser `scripts/core/ai_sales_actions_parser.py` + enricher `scripts/enrichment/ai_sales_actions_enricher.py` consume this field to populate sub-fields (AI Priority, AI Fit, AI Tone, AI Call Hook, etc.). Closes the gap where Notion showed 0 companies with AI Sales Actions populated despite the field being present in Apollo.
27. **Apollo Account Owner Priority (v5.1 — 2026-04-11)** — Reverses Decision #17 for the specific case where the Apollo Account itself has an `owner_id`. New priority in `compute_company_ownership()`: **(1)** Apollo Account `owner_id` (mapped via `APOLLO_OWNER_MAP`) wins directly → becomes Primary Company Owner, Supporting Owners cleared (Apollo is authoritative). **(2)** Only if Apollo owner is missing or unmapped, fall back to v5.0 contact-based derivation (owner with most contacts, tie-break by most recent activity). Why: for accounts that Apollo has explicitly assigned, the human assignment is more authoritative than a statistical head-count of contact owners. Decision #17 still holds as the fallback path. Implementation passes `accounts` (raw Apollo batch) to `compute_company_ownership()` from all three mode runners (`run_incremental`, `run_backfill`, `run_full`); the function builds an `account_id → owner_id` map and iterates over the union of Apollo-owned and contact-owned accounts. Logging: `[Ownership] Using Apollo owner for company X` / `[Ownership] Fallback to contact-based ownership for company Y` / warning on unmapped Apollo `owner_id`. Final stats line reports `apollo=N, fallback=M, unmapped_apollo=U, skipped=S`. No schema changes. No impact on dedup, metrics, stage, contact sync, or downstream task ownership.
28. **Real Intent Definition + Archive Guard (v6.1 — 2026-04-11)** — Broadened the intent signal beyond the old narrow `ENGAGEMENT_SIGNALS = {email_open, replied, meeting_booked, demoed}` set, which produced false negatives (single open = no signal). New definition centralized in `scripts/core/constants.py::has_real_intent(record)` and `company_has_real_intent(contacts)`: `intent = replied OR meeting_booked OR email_open_count >= 2 OR internal_forward_detected OR forward_count > 0 OR unique_openers_count >= 2 OR repeated_engagement_detected`. Returns `(bool, [reasons])` for logging. Accepts both snake_case (Apollo) and Title Case (Notion) keys. **Applied in:** (a) `governance/ingestion_gate.py::_check_engagement()` — renamed criterion to "Intent Signal"; (b) `governance/data_governor.py` — Archive Guard: any company/contact with real intent is spared from archival even if other soft failures exist (hard failures like no_company/no_email still archive contacts); (c) `core/daily_sync.py::compute_company_stage()` — contacts with real intent drive stage → Engaged; (d) `enrichment/analytics_tracker.py` — writes `Internal Forward Detected` and `Repeated Engagement Detected` booleans. Principle: *"repeated opens + internal circulation = meaningful commercial signal; not replying does not mean no interest."* Apollo limitation: no explicit "forwarded" field — `email_open_count >= 2` is the primary proxy, `unique_openers_count` / `forward_count` used when available.
29. **Safe Execution Order + Conflict Guards (v6.1 — 2026-04-11)** — Pipeline ordering was previously making decisions before their data existed: `analytics_tracker` and `outcome_tracker` ran in Job 2 AFTER `lead_score` in Job 1, so every scoring pass read yesterday's engagement data. `data_governor` could archive companies whose fresh signals hadn't landed yet. `daily_sync.compute_company_stage` and `opportunity_manager.update_company_stage_to_opportunity` both wrote Company Stage unconditionally, regressing Customer/Churned stages. **Fixes:** (a) **Reordered `.github/workflows/daily_sync.yml`** — moved `analytics_tracker`, `outcome_tracker`, `meeting_tracker`, `opportunity_manager` from Job 2 into Job 1 BEFORE `lead_score` + `action_ready_updater`. New Job 1 order: daily_sync → analytics_tracker → outcome_tracker → meeting_tracker → opportunity_manager → job_postings_enricher → lead_score → action_ready_updater → upload stats. Job 2 is now: auto_tasks → auto_sequence → meeting_analyzer (AI, non-blocking) → health_check. (b) **Added `STAGE_PRIORITY` lattice + `STAGE_TERMINAL` + `is_stage_regression()` to `core/constants.py`** — priority: Prospect(1) → Outreach(2) → Engaged(3) → Meeting(4) → Opportunity(5) → Customer(6) → Churned(7) → Archived(8). Terminal = {Customer, Churned, Archived}. (c) **Stage Write Guards** — `daily_sync.compute_company_stage()` and `opportunity_manager.update_company_stage_to_opportunity()` now read current stage BEFORE writing, skip if terminal, skip if regression, skip no-ops. `meeting_tracker.update_company_stage_to_meeting()` already had a compatible guard — left untouched. Uniform logging: `[Conflict Guard] Skipping stage write for X: current 'Customer' is terminal` / `[Conflict Guard] Prevented stage regression for X: Meeting → Outreach`. Final stats line in `compute_company_stage`: `N updated, R regressions prevented, T terminal stages preserved`. (d) **Freshness Guard in `data_governor`** — added `check_pipeline_freshness()` + `FRESHNESS_STATS_FILES = (enrichment/last_analytics_stats.json, automation/last_outcome_stats.json, meetings/last_meeting_tracker_stats.json)` + `FRESHNESS_MAX_AGE_HOURS = 26` to `core/constants.py`. `DataGovernor.run()` checks freshness as Step 0. If stats are older than 26h (or missing), enforce mode auto-downgrades to dry-run and logs `[Timing Guard] Refusing to archive on possibly-stale engagement data`. (e) **Artifact upload in Job 1 expanded** to include analytics, outcome, meeting_tracker, and opportunity stats/logs so next day's freshness check has real data. **Single-writer rule** for Company Stage: four writers (daily_sync, meeting_tracker, opportunity_manager, data_governor), all now guarded by `STAGE_TERMINAL` + `is_stage_regression`. No schema changes. First post-deploy run will see stale freshness (by design — no prior stats files); from run 2 onward enforcement resumes normally.

31. **compute_company_stage N+1 GET Fix (v5.2 — 2026-04-12)** — `compute_company_stage()` previously fired one individual `notion_request("GET", /pages/{id})` per company inside the write loop to read the current stage for the conflict guard. After a large full sync (15K company creates + ownership + metrics writes), Notion aggressively rate-limited these GETs, causing the function to hang silently for 55+ minutes with zero progress output. **Fix:** extracted `_preload_company_stages()` helper that runs a single paginated Notion DB query (one scan, ~155 requests for 15K companies) before the loop and returns a `{page_id: stage}` dict. The loop now reads from this in-memory map — O(1) lookup, zero extra API calls. Progress logging added every 200 companies. All guard logic (terminal / regression / no-op) is unchanged. Net result: stage computation drops from 55+ minutes to ~3–5 minutes. No schema changes, no logic changes.

32. **Enrichment Layer via organizations/enrich (v5.3 — 2026-04-13)** — Apollo's `accounts/search` endpoint returns account metadata (name, domain, Apollo ID, typed_custom_fields) but does NOT return firmographic data (industry, num_employees, annual_revenue, keywords, technologies). This caused 0% population for 5 critical company fields in Notion and degraded lead scoring (Size at 35% weight always defaulted to minimum 20/100; Industry Fit at 15% always defaulted to 30/100). **Fix:** Added `enrich_accounts_from_apollo()` function to `core/daily_sync.py` that calls Apollo's `GET /organizations/enrich?domain=X` endpoint per account AFTER `accounts/search` fetch and BEFORE `sync_companies()`. The enrichment response returns the full `organization` object with all firmographic fields. `_merge_enrichment_into_account()` maps enrichment fields to account dict keys (e.g., `estimated_num_employees` → `num_employees`, `technology_names` → `technologies`, `annual_revenue_printed` → `estimated_annual_revenue`), only filling fields that are currently empty. `format_company_from_api()` already maps all these fields correctly to Notion — no changes needed downstream. **Safety:** 30-day disk cache (`enrich_cache.json`) prevents redundant API calls. Per-account failure is non-fatal (logged and skipped). Rate-limited at 0.3s between requests + exponential backoff on 429/5xx. `--enrich-mode` CLI flag controls behavior: `missing` (default — only enrich accounts missing Industry/Employees/Revenue), `all` (all with domain), `force` (ignore cache), `skip` (disable). `--enrich-limit N` caps enrichment count per run. `--dry-run` logs what would be enriched without API calls. SyncStats extended with `enrichment_attempted/success/skipped/failed` counters. GitHub Actions workflow updated to v3.2 with `enrich_mode` manual trigger input. **Scoring impact:** Once firmographic data populates, `lead_score.py::employee_score()` will return actual scores (e.g., 100 for 23K employees vs. 20 default), and `industry_fit_score()` will match against `ICP_INDUSTRY_SCORES` (e.g., 90 for financial_services vs. 30 default). No code changes needed in `lead_score.py` — it already handles the data correctly; the fix was entirely on the data supply side.

30. **Script-Relative Log Paths + Root Cleanup (v6.2 — 2026-04-11)** — All 21 Python scripts that used `logging.FileHandler("name.log")` with CWD-relative paths have been updated to use `os.path.join(os.path.dirname(os.path.abspath(__file__)), "name.log")`. This ensures logs always write to their module subdirectory (`scripts/core/daily_sync.log`, `scripts/scoring/lead_score.log`, etc.) regardless of where Python is invoked from. Previously logs would scatter to the project root when run locally or to `scripts/` root when run via GitHub Actions `working-directory: scripts`, creating mismatch with artifact upload paths. Additionally: (a) 11 empty root log artifacts deleted; (b) 5 scripts/ root log artifacts deleted; (c) 6 operational .md files moved from root to `docs/ops/`; (d) Arabic implementation guide `.docx` moved to `docs/reports/`; (e) `muqawil_pipeline/` and `muqawil_output/` merged into `pipelines/muqawil/output/`; (f) `notion/` directory moved to `docs/notion-ops/`; (g) LibreOffice lock files removed; (h) 7 previously undocumented scripts added to Active Scripts table; (i) `governance/full_reset_notion.py` flagged as ADMIN ONLY with danger warning. No schema changes, no logic changes, no import changes — only log path fix and structural cleanup.

33. **Decision Layer v7.0 (2026-04-14)** — Added `scripts/scoring/company_priority_scorer.py` as the unified Decision Layer v7.0. Computes Company Priority Score (CPS) per company using 5 weighted components: Best Contact Score (25%), Engagement Index (25%), Firmographic Fit (20%), AI Signal Strength (15%), Momentum (15%). Outputs: CPS (0-100), Priority Tier (P1/P2/P3), Best Contact, Next Action, Priority Reason, Action Owner, Action SLA, AI Risk Flag. P1 threshold = 75, P2 = 50. Decision Layer v7.0 replaces the dead ai_decision_engine (dead-code path). Activated `ai_sales_actions_enricher.py` in Job 1 Step 5 (was manual-only, now feeds scoring + decision layer). Archived 7 dead/redundant scripts: ai_decision_engine.py, ai_action_executor.py, ai_sequence_generator.py, call_script_builder.py, cleanup_overdue_tasks.py, archive_unqualified.py, fix_seniority.py. Fixed score_calibrator.py weights from v1.1 (Size 45%, Seniority 35%, ...) to v1.5 (Size 35%, Seniority 30%, Industry Fit 15%, Intent 10%, Engagement 10%). New fields added to constants.py (CPS thresholds, Decision Layer field constants). GitHub Actions workflow updated to v7.0 with new steps.

---

## Module Architecture (v7.0 — Decision Layer Complete)

All 22 active production scripts organized into 8 functional modules under `scripts/`. Each script writes logs to its own module subdirectory.

| Module | Scripts | Domain |
|--------|---------|--------|
| `scripts/core/` | daily_sync.py, constants.py, notion_helpers.py, doc_sync_checker.py, ai_sales_actions_parser.py | Engine |
| `scripts/scoring/` | lead_score.py, score_calibrator.py, action_ready_updater.py, company_priority_scorer.py | Intelligence + Decision |
| `scripts/automation/` | auto_tasks.py, auto_sequence.py, outcome_tracker.py, lead_inbox_mover.py | Execution |
| `scripts/governance/` | ingestion_gate.py, data_governor.py, audit_ownership.py, full_reset_notion.py ⚠️ | Quality |
| `scripts/enrichment/` | job_postings_enricher.py, muhide_strategic_analysis.py, analytics_tracker.py, ai_sales_actions_enricher.py, reply_intelligence.py | Signals |
| `scripts/meetings/` | meeting_tracker.py, meeting_analyzer.py, opportunity_manager.py | Revenue |
| `scripts/monitoring/` | health_check.py, dashboard_generator.py, morning_brief.py | Observability |
| `scripts/webhooks/` | webhook_server.py, verify_links.py | Integration |

**Status:** v7.0 deployed — 7 scripts archived (ai_decision_engine, ai_action_executor, ai_sequence_generator, call_script_builder, cleanup_overdue_tasks, archive_unqualified, fix_seniority). Company Priority Scorer added as unified Decision Layer. GitHub Actions v7.0 deployed.

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
| `action-engine-builder` | Build and operate the Action Engine (automation/auto_tasks.py) and Action Ready logic |
| `pipeline-health-monitor` | Monitor daily pipeline health, detect failures, alert on anomalies |
| `meeting-intelligence-summarizer` | Turn meetings into structured CRM updates and follow-up tasks |
| `revenue-loop-tracker` | Track conversion rates, score-to-revenue correlation, feedback loops |
| `apollo-icp-strategist` | Define ICP, segment markets, prioritize accounts |
| `apollo-sequence-builder` | Create outbound sales sequences, email copy, LinkedIn messages |
| `exec-brief-writer` | Write executive summaries, status updates, business cases |

**Eval Benchmark:** `Skills_Eval_Review.html` — interactive viewer with side-by-side comparisons

---

## Feature Registry — Status Classification

Every feature classified by its actual implementation status.

| Feature | Script | Notion Field | Pipeline Step | Status |
|---------|--------|-------------|---------------|--------|
| Apollo → Notion Sync | scripts/core/daily_sync.py v5.3 | All fields | Job1 Step 1 | ✅ Active |
| Company Enrichment | scripts/core/daily_sync.py v5.3 (enrich layer) | Industry, Employees, Annual Revenue, Keywords, Technologies, Revenue Range, Short Description | Job1 Step 1 (integrated) | ✅ Active (v5.3) |
| Engagement Sync | scripts/enrichment/analytics_tracker.py | Replied, Email Opened | Job1 Step 6 | ✅ Active |
| Outcome Loop | scripts/automation/outcome_tracker.py | Contact Responded, Last Contacted | Job1 Step 7 | ✅ Active |
| Meeting Sync | scripts/meetings/meeting_tracker.py | Meeting Booked, Company Stage | Job1 Step 8 | ✅ Active |
| Meeting → Opportunity | scripts/meetings/opportunity_manager.py | Opportunity, Company Stage | Job1 Step 9 | ✅ Active |
| AI Sales Actions Parsing (pipeline) | scripts/enrichment/ai_sales_actions_enricher.py | AI Priority, AI Fit, AI Tone, AI Call Hook | Job1 Step 5 | ✅ Active (v7.0) |
| Job Postings Intent | scripts/enrichment/job_postings_enricher.py | Job Postings Intent (Company) | Job1 Step 10 | ✅ Active |
| Lead Scoring v1.5 | scripts/scoring/lead_score.py | Lead Score, Lead Tier, Sort Score | Job1 Step 11 | ✅ Active |
| Action Ready Eval | scripts/scoring/action_ready_updater.py | Action Ready checkbox | Job1 Step 12 | ✅ Active |
| Company Priority Score (Decision Layer) | scripts/scoring/company_priority_scorer.py | CPS, Priority Tier, Best Contact, Next Action, Action Owner, Action SLA | Job1 Step 13 | ✅ Active (v7.0) |
| HOT Task (Urgent Call) | scripts/automation/auto_tasks.py | Task Type = "Urgent Call" | Job2 Step 1 | ✅ Active (Fixed C-03) |
| WARM Task (Follow-up) | scripts/automation/auto_tasks.py | Task Type = "Follow-up" | Job2 Step 1 | ✅ Active |
| Apollo Sequence Enrollment | scripts/automation/auto_sequence.py | Outreach Status = "In Sequence" | Job2 Step 2 | ✅ Active |
| Meeting AI Analysis | scripts/meetings/meeting_analyzer.py | Key Takeaways, Next Steps | Job2 Step 3 | ✅ Active (needs ANTHROPIC_API_KEY) |
| Health Check | scripts/monitoring/health_check.py | — (stdout only) | Job2 Step 4 | ✅ Active |
| Morning Brief | scripts/monitoring/morning_brief.py | — (file output) | Job2 Step 5 (frozen v2.0) | ✅ Active |
| Dashboard | scripts/monitoring/dashboard_generator.py | dashboards/active/Sales_Dashboard_Accounts.html | Job2 Step 6 (frozen v2.0) | ✅ Active |
| Ingestion Gate | scripts/governance/ingestion_gate.py | — (pre-sync filter) | Integrated in scripts/core/daily_sync.py | ✅ Active |
| Data Governor | scripts/governance/data_governor.py | Stage = Archived | Manual run | ✅ Active |
| MUHIDE Strategic Analysis | scripts/enrichment/muhide_strategic_analysis.py | MUHIDE Fit Score, Priority | Manual / scheduled | ✅ Active |
| Score Calibration | scripts/scoring/score_calibrator.py | — (review only) | Weekly Sunday | ✅ Active (review-only) |
| Company-Centric Ownership (v5.1 Apollo-First) | scripts/core/daily_sync.py | Primary Company Owner, Supporting Owners | Job1 | ✅ Active |
| Company Stage Machine | scripts/core/daily_sync.py | Company Stage | Job1 | ✅ Active |
| Outcome → Meeting Booked | scripts/automation/outcome_tracker.py | Meeting Booked | Job2 | ✅ Active |
| muqawil_pipeline | pipelines/muqawil/ | — | Not in main workflow | ⚠️ Undocumented / Separate |
| engineering-offices | pipelines/engineering_offices/ | — | Not in main workflow | ⚠️ Inactive (all zeros) |
| Reply Intelligence | scripts/enrichment/reply_intelligence.py | AI Reply Status/Reason/Probability/Action/Confidence/Last Analyzed | Manual / scheduled | ✅ Active |
| Job Change Detection | — | Job Change Event/Date | NOT BUILT | 🔴 Planned (Phase 4) |
| Odoo ERP Integration | — | — | NOT BUILT | 🔴 Planned (Phase 4) |
| Lead Score v2.0 (intent-heavy) | — | — | NOT BUILT | 🔴 On hold (needs signal data) |
| WARM-HIGH Tier | — | — | REMOVED — never existed in code | ❌ Phantom (removed from docs) |
| AI Decision Engine | scripts/archive/ | Contact-level decision | ARCHIVED v7.0 | ⚠️ Archived (replaced by company_priority_scorer) |
| AI Action Executor | scripts/archive/ | Auto execute actions | ARCHIVED v7.0 | ⚠️ Archived (dead code path) |
| AI Sequence Generator | scripts/archive/ | Auto-generate email copy | ARCHIVED v7.0 | ⚠️ Archived (dead code path) |
| Call Script Builder | scripts/archive/ | Auto-generate call scripts | ARCHIVED v7.0 | ⚠️ Archived (dead code path) |
| Cleanup Overdue Tasks | scripts/archive/ | Bulk complete legacy tasks | ARCHIVED v7.0 | ⚠️ Archived (one-time migration complete) |
| Archive Unqualified | scripts/archive/ | Archive unqualified contacts | ARCHIVED v7.0 | ⚠️ Archived (replaced by data_governor) |
| Fix Seniority | scripts/archive/ | One-time seniority migration | ARCHIVED v7.0 | ⚠️ Archived (one-time migration complete) |

---

## Execution Plan (4 Phases)

### Phase 1: ACTIVATE — COMPLETE ✓
- [x] Full Sync running (all 60K+ records)
- [x] Lead Score engine built (v1.1 weights)
- [x] Lead Tier writing (HOT/WARM/COLD alongside score)
- [x] Seniority normalization (scripts/core/constants.py + _normalize_seniority)
- [x] Safe boolean writing (prevents overwriting manual data)
- [x] scripts/core/daily_sync.py v2.1 (added Stage, Outreach Status, engagement booleans, Last Contacted, Departments)
- [ ] Calibration — run `python scripts/scoring/lead_score.py --force` to write Lead Tier for all contacts
- [ ] Push code to GitHub, add `NOTION_DATABASE_ID_TASKS` secret, activate workflow
- **Gate:** Calibration must pass before activating Actions

### Phase 2: ACTION — CODE COMPLETE (pending first run)
- [x] Built `scripts/core/constants.py` — unified field names & thresholds
- [x] Built `scripts/automation/auto_tasks.py` — SLA-based task creator (HOT=24h call, WARM=48h follow-up)
- [x] Built `scripts/scoring/action_ready_updater.py` — 5-condition gating (score, DNC, outreach, stage, contact method)
- [x] Built `scripts/monitoring/health_check.py` — post-pipeline health validator
- [x] Updated `.github/workflows/daily_sync.yml` — 21-step pipeline (2 frozen 2026-04-10 Operator-First v2.0: dashboard_generator, morning_brief) with Action Engine + Health Check
- [x] Built 12 Claude Skills for AI Sales OS operations (evaluated at 100% pass rate)
- [ ] First run: `python scripts/scoring/action_ready_updater.py` then `python scripts/automation/auto_tasks.py --dry-run` to validate
- [ ] Create Notion task views for sales workflow
- **Gate:** Tasks must generate correctly before Phase 3

### Phase 3: ENRICH — COMPLETE ✓
- [x] Job Postings signal (`scripts/enrichment/job_postings_enricher.py` — active, 50/run limit)
- [x] Auto Sequence enrollment (`scripts/automation/auto_sequence.py` — HOT/WARM × 5 roles × 2 senders)
- [x] Analytics tracking (`scripts/enrichment/analytics_tracker.py` — engagement sync from Apollo)
- [x] Score Calibrator (`scripts/scoring/score_calibrator.py` — weekly review-only mode)
- [ ] Job Change detection (build from `people_match` + compare) — deferred to Phase 4
- [ ] Lead Score v2.0 — HOLD until intent/engagement signals > 50% coverage

### Phase 3.5: MEET — COMPLETE ✓ (March 2026)
- [x] `scripts/meetings/meeting_tracker.py` — Notion-native meeting sync, dual mode (Notion + Google Calendar)
- [x] `scripts/meetings/meeting_analyzer.py` — Claude AI meeting intelligence (requires ANTHROPIC_API_KEY in GitHub Secrets)
- [x] `scripts/meetings/opportunity_manager.py` — Meeting → Opportunity pipeline + stale deal detection
- [x] `scripts/core/doc_sync_checker.py` — Documentation drift validator
- [x] GitHub Actions updated to 21-step pipeline (2 frozen 2026-04-10 Operator-First v2.0: dashboard_generator, morning_brief) (meeting tracker, analyzer, opportunity manager added)
- [x] scripts/core/constants.py expanded with MEETINGS + OPPORTUNITIES field definitions
- [ ] ANTHROPIC_API_KEY confirmed in GitHub Secrets — **must verify**
- [ ] First real meeting logged in Meetings DB — **activate the loop**
- **Architecture assessment:** `Meeting_Call_Intelligence_Architecture_Assessment.md`

### Phase 3.7: COMPANY-CENTRIC — CODE COMPLETE (v5.0)
- [x] `scripts/core/constants.py` — 50+ new Company-Centric field constants, Company Stage values, TEAM_MEMBERS set
- [x] `scripts/core/daily_sync.py` **v4.0** — compute_company_ownership(), compute_company_metrics(), compute_company_stage()
- [x] `scripts/core/daily_sync.py` **v5.1 (2026-04-11)** — `compute_company_ownership()` now accepts `accounts` and prioritizes Apollo Account `owner_id` over contact-based derivation (see Decision #27)
- [x] `scripts/automation/auto_tasks.py` v2.0 — ONE task per company per tier, Task Owner from Primary Company Owner
- [x] `scripts/meetings/opportunity_manager.py` v2.0 — ONE opportunity per company, stakeholder tracking, Buying Committee
- [x] `scripts/meetings/meeting_tracker.py` v2.0 — auto-link Company, propagate Company Stage → Meeting, Meeting Owner
- [ ] Add new Notion properties via API (Phase 5 of migration plan)
- [ ] First run: `python scripts/core/daily_sync.py --mode incremental` → verify Company Ownership + Metrics + Stage populate
- [ ] Validate: `python scripts/automation/auto_tasks.py --dry-run` → confirm company-level dedup
- **Gate:** All v5.0 scripts must compile and new Notion fields must exist before first live run

### Phase 4: OPTIMIZE
- [ ] Odoo ERP integration (push qualified opportunities)
- [ ] Revenue pipeline tracking
- [ ] Advanced analytics
- [ ] Full end-to-end automation

---

## Documentation Sync Protocol — MANDATORY

**Every time any script is added, modified, or the pipeline changes, Claude MUST immediately update:**

| What Changed | Files to Update |
|---|---|
| New script added | CLAUDE.md (Active Scripts table + Folder Structure) · README.md (Module Architecture table) |
| Pipeline steps changed | CLAUDE.md (architecture line + GitHub Actions section + Feature Registry pipeline steps) · README.md (GitHub Actions Pipeline section)