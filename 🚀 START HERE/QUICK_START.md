# Quick Start Guide — AI Sales OS v4.0

## Prerequisites

- Python 3.11+
- Apollo.io API Key
- Notion API Key + 3 Database IDs (Contacts, Companies, Tasks)

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

**14-step pipeline:**
1. `daily_sync.py --mode incremental --hours 26` → sync new/updated records
2. `job_postings_enricher.py --limit 50` → intent enrichment
3. `lead_score.py` → recalculate scores + write Lead Tier
4. `action_ready_updater.py` → set Action Ready flags
5. `auto_tasks.py` → create SLA-based tasks
6. `auto_sequence.py --limit 50` → enroll in Apollo sequences
7. `analytics_tracker.py --days 7` → sync engagement data
8. `health_check.py` → validate run
9. `morning_brief.py --output file` → daily report

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
