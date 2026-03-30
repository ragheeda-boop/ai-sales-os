# GitHub Actions Setup Guide

## What This Does

Runs the daily pipeline automatically at **7:00 AM KSA** every day (10-step flow):
1. Checkout repository
2. Setup Python 3.11
3. Install dependencies
4. `daily_sync.py --mode incremental --hours 26` — sync new/updated records from Apollo
5. `lead_score.py` — recalculate Lead Scores + write Lead Tier
6. `action_ready_updater.py` — evaluate Action Ready checkbox (5 conditions)
7. `auto_tasks.py` — create SLA-based tasks for Action Ready contacts
8. `health_check.py` — validate pipeline results
9. Upload logs as artifacts (30-day retention)
10. Notify on failure

## Step 1: Create Repository

1. Go to https://github.com/new
2. Name: `ai-sales-os` (or any name)
3. Select **Private** (contains API references)
4. Click **Create repository**

## Step 2: Push Code

```bash
cd "AI Sales OS"
git init
git add .
git commit -m "AI Sales OS v3.0 — Sync + Score pipeline"
git remote add origin https://github.com/YOUR_USERNAME/ai-sales-os.git
git push -u origin main
```

Note: `.env` and sensitive files are excluded by `.gitignore`.

## Step 3: Add Secrets

Go to **Settings > Secrets and variables > Actions** and add:

| Secret Name | Value |
|---|---|
| `APOLLO_API_KEY` | Your Apollo API key |
| `NOTION_API_KEY` | Your Notion API key |
| `NOTION_DATABASE_ID_CONTACTS` | Your Contacts database ID |
| `NOTION_DATABASE_ID_COMPANIES` | Your Companies database ID |
| `NOTION_DATABASE_ID_TASKS` | Your Tasks database ID |

## Step 4: Enable Actions

1. Go to **Actions** tab
2. Click **I understand my workflows, go ahead and enable them**

## Step 5: Test

1. Go to **Actions > Apollo > Notion Daily Pipeline**
2. Click **Run workflow**
3. Select sync mode:
   - `incremental` — last 26 hours (default daily)
   - `backfill_week` — last 7 days with checkpoint
   - `backfill_month` — last 30 days with checkpoint
   - `full` — complete rebuild (slow, first-time only)
4. Select toggles:
   - `run_lead_score` — recalculate scores + Lead Tier
   - `run_action_engine` — create tasks for Action Ready contacts
5. Click **Run workflow**

## Daily Schedule

After setup, the pipeline runs **automatically** every day:
- 7:00 AM KSA (04:00 UTC)
- Syncs new/updated contacts and companies
- Recalculates Lead Scores + writes Lead Tier
- Evaluates Action Ready for all scored contacts
- Creates SLA-based tasks (HOT = 24h call, WARM = 48h follow-up)
- Validates pipeline health
- Uploads logs as downloadable artifacts
- Notifies on failure

## Cost

```
GitHub Actions Free Tier: 2,000 min/month
Daily run estimate:       ~15 min/day x 30 = 450 min/month
Remaining:                1,550 min/month (no cost)
```

## Monitoring

- **Actions tab** — see each run status
- **Artifacts** — download sync and score logs
- **Email notifications** — Settings > Notifications > Actions
