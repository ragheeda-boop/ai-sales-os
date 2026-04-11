# Quick Start Guide — AI Sales OS v6.0

## Prerequisites

- Python 3.11+
- Apollo.io API Key
- Notion API Key + 5 Database IDs (Contacts, Companies, Tasks, Meetings, Opportunities)
- Anthropic API Key (optional — required only for AI meeting analysis)

## Step 1: Configure (2 min)

```bash
cd scripts
cp core/.env.example .env
```

Edit `.env` with your credentials:
```
APOLLO_API_KEY=your_apollo_key
NOTION_API_KEY=your_notion_key
NOTION_DATABASE_ID_CONTACTS=your_contacts_db_id
NOTION_DATABASE_ID_COMPANIES=your_companies_db_id
NOTION_DATABASE_ID_TASKS=your_tasks_db_id
NOTION_DATABASE_ID_MEETINGS=your_meetings_db_id
NOTION_DATABASE_ID_OPPORTUNITIES=your_opportunities_db_id
ANTHROPIC_API_KEY=your_anthropic_key   # Optional — for AI meeting analysis
```

## Step 2: Install (1 min)

```bash
pip install -r requirements.txt
```

## Step 3: First Sync (2-4 hours)

```bash
# Full sync — pulls ALL records from Apollo
cd scripts && python core/daily_sync.py --mode full
```

Monitor progress: `tail -f core/daily_sync.log`

## Step 4: Enrich Companies (30 min)

```bash
# Job postings intent scoring for HOT/WARM companies
python enrichment/job_postings_enricher.py --limit 50
```

## Step 5: Score Leads (30 min)

```bash
# Calculate Lead Score for all contacts + assign Lead Tier (HOT/WARM/COLD)
python scoring/lead_score.py --force
```

After this runs, check Notion views: HOT LEADS (>=80), WARM LEADS (50-79), COLD LEADS (<50).

## Step 6: Set Action Ready Flags (10 min)

```bash
# Evaluate 5 conditions: Score>=50, !DNC, !Bounced, !Churned, has contact method
python scoring/action_ready_updater.py
```

Only contacts meeting ALL 5 conditions will be marked Action Ready = True.

## Step 7: Validate Task Creation (5 min)

```bash
# Dry run: show what tasks would be created without writing
python automation/auto_tasks.py --dry-run
```

Review the output. If it looks good, proceed to Step 8.

## Step 8: Create Tasks (10 min)

```bash
# Create actual tasks for Action Ready contacts (HOT=24h call, WARM=48h follow-up)
python automation/auto_tasks.py
```

## Step 9: Enroll in Sequences (10 min)

```bash
# Preview sequence enrollments
python automation/auto_sequence.py --dry-run --limit 10

# If it looks good, enroll
python automation/auto_sequence.py --limit 50
```

## Step 10: Sync Engagement Data (5 min)

```bash
# Pull opens, replies, bounces from Apollo
python enrichment/analytics_tracker.py --days 7
```

## Step 10.5: Meeting Intelligence — Phase 3.5 (optional)

```bash
# Sync meetings from Notion → update Contact fields
python meetings/meeting_tracker.py --days 7

# Analyze meeting notes with AI (requires ANTHROPIC_API_KEY)
python meetings/meeting_analyzer.py --limit 10

# Convert positive meetings to opportunities + flag stale deals
python meetings/opportunity_manager.py
```

> If you have logged meetings in the Meetings DB, run these 3 scripts to activate the revenue feedback loop.

## Step 11: Health Check (2 min)

```bash
# Validate pipeline run
python monitoring/health_check.py
```

## Step 12: Morning Brief (1 min)

```bash
# Generate daily intelligence report
python monitoring/morning_brief.py
```

## Step 13: Daily Automation

Push code to GitHub, add Secrets, and GitHub Actions will run daily at 7 AM KSA.

The pipeline runs as **2 sequential jobs** — each has its own 6-hour limit (total ~9h capacity):

**Job 1 — `sync-and-score` (timeout: 5h 50min):**
1. `core/daily_sync.py --mode incremental --hours 26` → sync new/updated records
2. `enrichment/job_postings_enricher.py --limit 50` → intent enrichment
3. `scoring/lead_score.py` → recalculate scores + write Lead Tier
4. `scoring/action_ready_updater.py` → set Action Ready flags

**Job 2 — `action-and-track` (timeout: 3h, starts after Job 1):**
5. `automation/auto_tasks.py` → create SLA-based tasks
6. `automation/auto_sequence.py --limit 50` → enroll in Apollo sequences
7. `meetings/meeting_tracker.py --days 7` → sync meetings, update contact stage *(Phase 3.5)*
8. `meetings/meeting_analyzer.py --limit 10` → AI meeting analysis *(Phase 3.5, requires ANTHROPIC_API_KEY)*
9. `meetings/opportunity_manager.py` → meetings → opportunities + stale deal detection *(Phase 3.5)*
10. `enrichment/analytics_tracker.py --days 7` → sync engagement data
11. `monitoring/health_check.py` → validate run
12. `monitoring/morning_brief.py --output file` → daily report

**GitHub Secrets required:** APOLLO_API_KEY, NOTION_API_KEY, NOTION_DATABASE_ID_CONTACTS, NOTION_DATABASE_ID_COMPANIES, NOTION_DATABASE_ID_TASKS, NOTION_DATABASE_ID_MEETINGS, NOTION_DATABASE_ID_OPPORTUNITIES, ANTHROPIC_API_KEY (optional)

**Weekly (Sundays):** `scoring/score_calibrator.py --days 30 --export` → self-learning calibration (runs after Job 2)

## Useful Commands

```bash
cd scripts

# Sync last 7 days
python core/daily_sync.py --mode incremental --days 7

# Backfill with checkpoint (resumes if interrupted)
python core/daily_sync.py --mode backfill --days 365

# Score without writing (dry run)
python scoring/lead_score.py --dry-run

# Recalculate ALL scores
python scoring/lead_score.py --force

# Enrich only HOT companies
python enrichment/job_postings_enricher.py --tier HOT

# Enroll only HOT contacts in sequences
python automation/auto_sequence.py --tier HOT

# Analytics report without writing
python enrichment/analytics_tracker.py --skip-sync --export

# Calibration analysis (review only)
python scoring/score_calibrator.py --days 90
```

## Troubleshooting

**Incremental run processing all contacts?** Fixed in v4.2 — local timestamp filter now applied after Apollo fetch. If you see the warning `⚠️ Local timestamp filter removed N contacts`, it means Apollo's API filter was returning records outside the window (normal behavior). The filter corrects this automatically.
**Sync fails mid-run?** Use backfill mode — it resumes from checkpoint.
**API rate l