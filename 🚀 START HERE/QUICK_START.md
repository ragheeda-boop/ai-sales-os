# Quick Start Guide — AI Sales OS v4.0

## Prerequisites

- Python 3.11+
- Apollo.io API Key
- Notion API Key + 5 Database IDs (Contacts, Companies, Tasks, Meetings, Opportunities)
- Anthropic API Key (optional — required only for AI meeting analysis)

## Step 1: Configure (2 min)

```bash
cd "💻 CODE/Phase 3 - Sync"
cp .env.example .env
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
python daily_sync.py --mode full
```

Monitor progress: `tail -f daily_sync.log`

## Step 4: Enrich Companies (30 min)

```bash
# Job postings intent scoring for HOT/WARM companies
python job_postings_enricher.py --limit 50
```

## Step 5: Score Leads (30 min)

```bash
# Calculate Lead Score for all contacts + assign Lead Tier (HOT/WARM/COLD)
python lead_score.py --force
```

After this runs, check Notion views: HOT LEADS (>=80), WARM LEADS (50-79), COLD LEADS (<50).

## Step 6: Set Action Ready Flags (10 min)

```bash
# Evaluate 5 conditions: Score>=50, !DNC, !Bounced, !Churned, has contact method
python action_ready_updater.py
```

Only contacts meeting ALL 5 conditions will be marked Action Ready = True.

## Step 7: Validate Task Creation (5 min)

```bash
# Dry run: show what tasks would be created without writing
python auto_tasks.py --dry-run
```

Review the output. If it looks good, proceed to Step 8.

## Step 8: Create Tasks (10 min)

```bash
# Create actual tasks for Action Ready contacts (HOT=24h call, WARM=48h follow-up)
python auto_tasks.py
```

## Step 9: Enroll in Sequences (10 min)

```bash
# Preview sequence enrollments
python auto_sequence.py --dry-run --limit 10

# If it looks good, enroll
python auto_sequence.py --limit 50
```

## Step 10: Sync Engagement Data (5 min)

```bash
# Pull opens, replies, bounces from Apollo
python analytics_tracker.py --days 7
```

## Step 10.5: Meeting Intelligence — Phase 3.5 (optional)

```bash
# Sync meetings from Notion → update Contact fields
python meeting_tracker.py --days 7

# Analyze meeting notes with AI (requires ANTHROPIC_API_KEY)
python meeting_analyzer.py --limit 10

# Convert positive meetings to opportunities + flag stale deals
python opportunity_manager.py
```

> If you have logged meetings in the Meetings DB, run these 3 scripts to activate the revenue feedback loop.

## Step 11: Health Check (2 min)

```bash
# Validate pipeline run
python health_check.py
```

## Step 12: Morning Brief (1 min)

```bash
# Generate daily intelligence report
python morning_brief.py
```

## Step 13: Daily Automation

Push code to GitHub, add 5 Secrets, and GitHub Actions will run daily at 7 AM KSA:

**16-step pipeline (Phase 3.5 included):**
1. `daily_sync.py --mode incremental --hours 26` → sync new/updated records
2. `job_postings_enricher.py --limit 50` → intent enrichment
3. `lead_score.py` → recalculate scores + write Lead Tier
4. `action_ready_updater.py` → set Action Ready flags
5. `auto_tasks.py` → create SLA-based tasks
6. `auto_sequence.py --limit 50` → enroll in Apollo sequences
7. `analytics_tracker.py --days 7` → sync engagement data
8. `meeting_tracker.py --days 7` → sync meetings, update contact stage *(Phase 3.5)*
9. `meeting_analyzer.py --limit 10` → AI meeting analysis *(Phase 3.5, requires ANTHROPIC_API_KEY)*
10. `opportunity_manager.py` → meetings → opportunities + stale deal detection *(Phase 3.5)*
11. `health_check.py` → validate run
12. `morning_brief.py --output file` → daily report

**GitHub Secrets required:** APOLLO_API_KEY, NOTION_API_KEY, NOTION_DATABASE_ID_CONTACTS, NOTION_DATABASE_ID_COMPANIES, NOTION_DATABASE_ID_TASKS, NOTION_DATABASE_ID_MEETINGS, NOTION_DATABASE_ID_OPPORTUNITIES, ANTHROPIC_API_KEY (optional)

**Weekly (Sundays):** `score_calibrator.py --days 30 --export` → self-learning calibration

## Useful Commands

```bash
# Sync last 7 days
python daily_sync.py --mode incremental --days 7

# Backfill with checkpoint (resumes if interrupted)
python daily_sync.py --mode backfill --days 365

# Score without writing (dry run)
python lead_score.py --dry-run

# Recalculate ALL scores
python lead_score.py --force

# Enrich only HOT companies
python job_postings_enricher.py --tier HOT

# Enroll only HOT contacts in sequences
python auto_sequence.py --tier HOT

# Analytics report without writing
python analytics_tracker.py --skip-sync --export

# Calibration analysis (review only)
python score_calibrator.py --days 90
```

## Troubleshooting

**Sync fails mid-run?** Use backfill mode — it resumes from checkpoint.
**API rate limited?** Built-in retry with exponential backoff handles this.
**Duplicate records?** Triple dedup (Apollo ID + Email + seen_ids) prevents this.
**Sequence enrollment fails?** Check Apollo API key permissions and sequence IDs.
**Calibrator recommends big changes?** Review manually first — never auto-apply without review.

---
**Version:** 4.0 | **Last Updated:** 28 March 2026
