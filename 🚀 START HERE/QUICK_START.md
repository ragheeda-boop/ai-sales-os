# Quick Start Guide

## Prerequisites

- Python 3.8+
- Apollo.io API Key
- Notion API Key + Database IDs (Contacts + Companies)

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

## Step 4: Score Leads (30 min)

```bash
# Calculate Lead Score for all contacts
python lead_score.py --force
```

After this runs, check Notion views: HOT LEADS (>=80), WARM LEADS (50-79), COLD LEADS (<50).

## Step 5: Daily Automation

Push code to GitHub, add Secrets, and GitHub Actions will run daily at 7 AM KSA:
1. `daily_sync.py --mode incremental` → sync new records
2. `lead_score.py` → recalculate scores

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
```

## Troubleshooting

**Sync fails mid-run?** Use backfill mode — it resumes from checkpoint.
**API rate limited?** Built-in retry with exponential backoff handles this.
**Duplicate records?** Triple dedup (Apollo ID + Email + seen_ids) prevents this.
