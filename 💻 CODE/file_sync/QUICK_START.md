# File Sync Engine - Quick Start Guide

## 5-Minute Setup

### 1. Install Dependencies
```bash
cd "AI Sales OS/💻 CODE/file_sync"
pip install -r requirements.txt
```

### 2. Create .env File
```bash
cat > .env << 'ENVEOF'
# Local paths
SYNC_LOCAL_ROOT=/full/path/to/AI Sales OS

# Google Drive
DRIVE_FOLDER_ID=your_folder_id_from_url
DRIVE_CREDENTIALS_PATH=./credentials.json

# GitHub
GITHUB_REPO=your_username/your_repo
GITHUB_BRANCH=main
GITHUB_TOKEN=ghp_your_token_here
GITHUB_USER=your_username

# Logging
SYNC_LOG_LEVEL=INFO
ENVEOF
```

**How to get IDs:**

**Drive Folder ID:**
- Open folder in Google Drive
- Copy from URL: `https://drive.google.com/drive/folders/FOLDER_ID_HERE`

**GitHub Token:**
- Go to Settings → Developer Settings → Personal Access Tokens
- Create with `repo` scope
- Copy the token

### 3. First Sync (Dry Run)
```bash
python sync_engine.py --mode scan
```
Output shows files found in each source.

```bash
python sync_engine.py --mode compare
```
Output shows what would change since last run.

### 4. Execute Sync
```bash
# Preview changes
python sync_engine.py --mode sync --dry-run

# Run for real
python sync_engine.py --mode sync
```

## Common Commands

### Scan Only (no changes)
```bash
python sync_engine.py --mode scan
```
Safe read-only operation. Shows file counts.

### Compare with Last Run
```bash
python sync_engine.py --mode compare
```
Shows: NEW files, MODIFIED files, DELETED files

### Full Sync
```bash
python sync_engine.py --mode sync
```
Executes: Scan → Detect → Resolve → Execute

### Sync with Verbosity
```bash
python sync_engine.py --mode sync --verbose
```
Shows detailed debug output.

### Force Mode (skip confirmations)
```bash
python sync_engine.py --mode sync --force
```
No prompts, execute immediately.

### Report Only (no re-scan)
```bash
python sync_engine.py --mode report
```
Uses manifest from last run.

## Monitoring

### Check Logs
```bash
# Real-time sync log
tail -f .sync/logs/sync.log

# Audit trail (JSON)
tail -f .sync/audit_trail.jsonl

# Errors only
tail -f .sync/logs/errors.log
```

### Backup Files
```bash
ls -lh .sync/backups/
```
Latest 30 backups kept automatically.

### Conflicts
```bash
ls -la .sync/conflicts/
```
Files requiring manual review staged here.

## Troubleshooting

### "No folder ID configured"
```bash
# Add to .env:
DRIVE_FOLDER_ID=your_id_here
```

### "Credentials not found"
```bash
# Download from Google Cloud Console
# Save to current directory as: credentials.json
```

### "Git not found"
```bash
# Install git
apt-get install git  # Linux
brew install git     # macOS
```

### "Permission denied (GitHub)"
```bash
# Token needs 'repo' scope
# Regenerate from Settings → Developer Settings
```

### Conflicts Detected
Check `.sync/conflicts/` directory. Files staged there for manual review.

## File Organization

After first sync, your structure looks like:

```
AI Sales OS/
├── 💻 CODE/
│   ├── file_sync/
│   │   ├── config.py
│   │   ├── sync_engine.py
│   │   ├── .sync/                    ← Created by sync
│   │   │   ├── manifest.json         ← Current state
│   │   │   ├── manifest_history/     ← Previous runs
│   │   │   ├── logs/
│   │   │   │   ├── sync.log
│   │   │   │   ├── audit.log
│   │   │   │   └── errors.log
│   │   │   ├── backups/              ← Auto-backups
│   │   │   ├── conflicts/            ← Manual review
│   │   │   ├── .trash/               ← Deleted files
│   │   │   └── audit_trail.jsonl     ← Immutable log
│   │   ├── .env                      ← Your config
│   │   └── [16 core modules]
```

## Daily Workflow

### Morning: Check What Changed
```bash
python sync_engine.py --mode compare
```

### During Day: Make Changes
- Edit code locally
- Upload presentations to Drive
- Commit to GitHub manually (or auto-sync)

### Evening: Sync Everything
```bash
python sync_engine.py --mode sync
```

### Weekly: Review Audit Trail
```bash
tail -100 .sync/audit_trail.jsonl | grep '"conflict"'
```

## Safety Checks

The engine protects you:
- **Before Delete**: Refuses if >10% would be deleted
- **Before Modify**: Confirms if >50% would change
- **Large Files**: Manual approval for >100 MB
- **Backups**: Auto-backup before overwrites
- **Secrets**: Never syncs .env files

## Performance Tips

1. **First run will take longest** (scans all 3 sources)
2. **Incremental runs are much faster** (compare detects changes)
3. **Use --dry-run first** to see what will happen
4. **Check conflicts early** before they accumulate

## GitHub Actions (Optional)

Add to `.github/workflows/sync.yml`:

```yaml
name: Sync Files

on:
  schedule:
    - cron: '0 9 * * *'  # 9 AM daily

jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
        with:
          token: ${{ secrets.GITHUB_TOKEN }}
      
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r 'AI Sales OS/💻 CODE/file_sync/requirements.txt'
      
      - name: Run sync
        env:
          DRIVE_FOLDER_ID: ${{ secrets.DRIVE_FOLDER_ID }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          cd 'AI Sales OS/💻 CODE/file_sync'
          python sync_engine.py --mode sync --force
      
      - name: Commit results
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add -A
          git commit -m "Automated file sync" || true
          git push
```

## Getting Help

1. **Check README.md** for detailed documentation
2. **Run with --verbose** for debug output
3. **Check audit trail** for decision history
4. **Review logs** in `.sync/logs/`
5. **Check conflicts** in `.sync/conflicts/`

---

**Next Steps:**
1. Create `.env` with your IDs
2. Run `python sync_engine.py --mode scan`
3. Review output
4. Run with `--dry-run` to see changes
5. Execute full sync when ready

**Support**: See README.md for full documentation
