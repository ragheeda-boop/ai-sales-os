# AI Sales OS File Synchronization Engine

Production-grade file synchronization system for AI Sales OS that coordinates file sync across Local filesystem, Google Drive, and GitHub repository.

## Architecture

```
┌─────────────────┐
│   Local FS      │
└────────┬────────┘
         │
┌────────▼────────────────────────────────────────┐
│  Unified Manifest (relative_path = primary key)  │
│  - File metadata from all sources               │
│  - Source of truth designations                 │
│  - Conflict flags                               │
└────────┬────────────────────────────────────────┘
         │
┌────────▼─────────────────────────────────────────┐
│  Conflict Detection & Resolution                 │
│  - Text conflicts: merge-friendly                │
│  - Delete conflicts: preserve in trash           │
│  - Binary conflicts: manual review               │
│  - Duplicates: governance-based                  │
└────────┬─────────────────────────────────────────┘
         │
┌────────▼──────────────────────────────────────────┐
│  Sync Actions (push/pull/copy/delete/move)        │
│  - Safety checks (MAX_DELETE_PERCENT)             │
│  - Batch operations by destination                │
│  - Auto backups before overwrite                  │
└────────┬──────────────────────────────────────────┘
         │
     ┌───┴───┬─────────────┬─────────────┐
     │       │             │             │
┌────▼──┐ ┌──▼──┐     ┌────▼──────┐ ┌──▼──────┐
│Local  │ │Drive│     │GitHub     │ │Audit   │
│Sync   │ │Sync │     │Sync       │ │Trail   │
└───────┘ └─────┘     └───────────┘ └────────┘
```

## Modules

| Module | Purpose |
|--------|---------|
| `config.py` | Centralized configuration (paths, API keys, rules, thresholds) |
| `models.py` | Data models (FileRecord, Manifest, SyncAction, Conflict, AuditEntry) |
| `classify_files.py` | File classification by category and source of truth |
| `scan_local.py` | Local filesystem scanner (SHA256 hashing, .gitignore respect) |
| `scan_drive.py` | Google Drive scanner (recursive, pagination handling) |
| `scan_github.py` | GitHub scanner (git commands or API) |
| `build_manifest.py` | Merge scanners into unified manifest |
| `compare_manifests.py` | Diff current vs. previous manifest (NEW/MODIFIED/DELETED/MOVED) |
| `detect_conflicts.py` | Conflict detection (text, binary, delete, triple, duplicates) |
| `resolve_conflicts.py` | Conflict resolution (auto by source of truth + manual queue) |
| `sync_to_local.py` | Download from Drive/GitHub to local |
| `sync_to_drive.py` | Upload to Google Drive |
| `sync_to_github.py` | Push to GitHub repository |
| `backup_manager.py` | Backup creation, verification, rotation, restore |
| `logging_manager.py` | Structured logging (console colored + JSON audit trail) |
| `sync_engine.py` | Main orchestrator (CLI + full sync cycle) |

## Usage

### Installation

```bash
cd "/AI Sales OS/💻 CODE/file_sync"
pip install -r requirements.txt
```

### Configuration

Create `.env` file in the sync directory:

```bash
# Local paths
SYNC_LOCAL_ROOT=/path/to/AI Sales OS

# Google Drive
DRIVE_FOLDER_ID=your_folder_id_here
DRIVE_CREDENTIALS_PATH=./credentials.json

# GitHub
GITHUB_REPO=owner/repo
GITHUB_BRANCH=main
GITHUB_TOKEN=your_token_here
GITHUB_USER=your_username

# Logging
SYNC_LOG_LEVEL=INFO
```

### CLI Commands

#### Scan only (no sync)
```bash
python sync_engine.py --mode scan
```
Output: Scans all sources, builds manifest, prints summary.

#### Compare with previous
```bash
python sync_engine.py --mode compare
```
Output: Shows NEW/MODIFIED/DELETED/MOVED files since last run.

#### Full sync (default)
```bash
python sync_engine.py --mode sync
```
Executes: Scan → Compare → Detect Conflicts → Resolve → Execute Actions

#### Dry run
```bash
python sync_engine.py --mode sync --dry-run
```
Shows what would happen without making changes.

#### Report mode
```bash
python sync_engine.py --mode report
```
Shows report of last sync without re-scanning.

#### With specific source
```bash
python sync_engine.py --source local --mode sync
```
Only sync from specified source.

## Data Models

### FileRecord
Individual file state across all sources:
- `relative_path` (primary key)
- `file_id`, `file_name`, `extension`, `classification`
- `sources`: dict of local/drive/github SourceState
- `source_of_truth`: designated authoritative source
- `conflict_flag`, `review_required`, `status`
- `hash_sha256` for comparison

### Manifest
Collection of all files with metadata:
- `version`, `project`, `generated_at`
- `total_files`, `files` dict keyed by relative_path
- `metadata` with project info

### SyncAction
Operation to execute:
- `action_type`: PUSH/PULL/COPY/DELETE/MOVE/CONFLICT
- `source`, `target`: direction of sync
- `file_record`: reference to FileRecord
- `auto_resolved`, `reason`: explanation

### ConflictRecord
Conflict requiring resolution:
- `conflict_type`: TEXT/BINARY/DELETE/TRIPLE/DUPLICATE
- `sources_involved`: list of conflicting sources
- `resolution`: proposed solution
- `manual_required`: if can't auto-resolve

### AuditEntry
Immutable audit trail entry:
- `timestamp`, `action`, `file_path`
- `source`, `target`, `change_type`
- `decision`, `result`
- `hash_before`, `hash_after`

## File Classification

Files are classified by category, determining sync rules and source of truth:

| Category | Extensions | Source of Truth | Sync To | Purpose |
|----------|-----------|-----------------|---------|---------|
| `code` | `.py`, `.js`, `.ts`, `.json`, `.yaml` | GitHub | GitHub, Local, Drive | Code is version-controlled |
| `documentation_md` | `.md`, `.txt`, `.rst` | GitHub | GitHub, Local, Drive | Docs are versioned |
| `documentation_office` | `.docx`, `.doc`, `.odt` | Drive | Drive, Local | Office docs on Drive |
| `presentation` | `.pptx`, `.ppt`, `.odp` | Drive | Drive, Local | Presentations on Drive |
| `spreadsheet_csv` | `.csv`, `.tsv` | GitHub | GitHub, Local, Drive | CSV data versioned |
| `spreadsheet_office` | `.xlsx`, `.xls`, `.ods` | Drive | Drive, Local | Excel on Drive |
| `data_json` | `.json`, `.jsonl`, `.parquet` | GitHub | GitHub, Local, Drive | Data versioned |
| `media_small` | `.png`, `.jpg`, `.svg`, `.pdf` | GitHub | GitHub, Local, Drive | Small media in all places |
| `media_large` | `.mp4`, `.mp3`, `.mov` | Drive | Drive, Local | Large files on Drive |
| `archive` | `.zip`, `.tar`, `.gz`, `.rar` | Drive | Drive, Local | Archives on Drive |
| `config_template` | `.env.example`, `.gitignore` | GitHub | GitHub, Local | Config templates versioned |
| `secret` | `.env`, `.key`, `.pem` | Local | Local Only | Secrets stay local |
| `log` | `.log` | Local | Local Only | Logs stay local |

## Conflict Resolution

### Text Conflicts (auto-resolvable)
- File modified in 2+ sources with different content
- Uses git merge for local+github conflicts
- Falls back to source-of-truth selection
- Manual review if merge produces conflicts

### Delete Conflicts (manual queue)
- File deleted in one source, exists in others
- Preserves all copies in `.sync/conflicts/`
- Moves deleted files to `.sync/.trash/`
- Manual review to decide which version wins

### Binary Conflicts (manual queue)
- Binary files modified in multiple sources
- Cannot auto-merge
- Stages all versions in `.sync/conflicts/`
- Manual selection required

### Duplicate Files (auto-resolvable)
- Same content (hash match) in different paths
- Keeps version in source-of-truth location
- Deletes duplicates in non-authoritative sources
- Logs decision for audit trail

### Triple Conflicts (manual queue)
- All 3 sources (local, drive, github) have different content
- Always manual review
- Stages all 3 versions
- Manual decision required

## Safety Features

### Pre-flight Checks
- Verifies `.git` directory exists before github sync
- Confirms Google Drive credentials available
- Checks write permissions to local paths
- Validates manifest integrity

### Thresholds
- `MAX_DELETE_PERCENT = 10%`: Refuse if >10% would be deleted (corruption check)
- `MAX_MODIFY_PERCENT = 50%`: Refuse if >50% would be modified
- `MAX_AUTO_SYNC_SIZE_MB = 100`: Confirm manually for large files
- `MAX_AUTO_RESOLVE_CONFLICTS = 5`: Manual review if >5 auto-resolves needed

### Rollback Support
- Auto-backup before any overwrite
- Keep last 30 backups (rotated automatically)
- Backup verification on creation
- Restore command available

### Audit Trail
- Append-only JSON lines log (`.sync/audit_trail.jsonl`)
- Every action logged: timestamp, user, source, target, decision, result
- Hash before/after for verification
- Permanent record for compliance

## Logging

### Console Output (Colored)
```
INFO - sync - Scanning all sources...
DEBUG - sync.scan_local - Processing file: config.py
WARNING - sync.detect_conflicts - 2 conflicts detected
ERROR - sync.sync_to_github - Failed to push: permission denied
```

### File Output
- **sync.log**: All messages (text format)
- **audit.log**: JSON-formatted structured logs
- **errors.log**: Errors only (append-only)
- **audit_trail.jsonl**: Immutable audit trail (one JSON object per line)

## Integration with AI Sales OS

This sync engine is designed to keep three systems in sync:

1. **Local Filesystem**: Developer's machine (source of truth for code)
2. **Google Drive**: Shared team documents and presentations
3. **GitHub**: Version-controlled code and documentation

### Typical Workflow

1. Developer makes changes locally
2. `sync_engine.py --mode scan` detects changes
3. `sync_engine.py --mode compare` shows diffs
4. `sync_engine.py --mode sync` executes:
   - Push code changes to GitHub
   - Upload presentations to Drive
   - Merge conflicts (auto or manual)
5. Team members pull updated files via Drive/GitHub

### GitHub Actions Integration

Planned CI/CD integration to run sync daily:
```yaml
- name: Sync files
  run: |
    cd 'AI Sales OS/💻 CODE/file_sync'
    python sync_engine.py --mode sync --force
```

## Performance

- **Scanning**: ~2-5 minutes for 10K files (depends on network)
- **Local scan**: ~30 seconds (filesystem I/O)
- **Drive scan**: ~2 minutes (API pagination)
- **GitHub scan**: ~1 minute (git commands)
- **Comparison**: Instant (in-memory diff)
- **Conflict detection**: ~1 second
- **Sync actions**: ~5-30 seconds per 100 files

## Troubleshooting

### "No Drive folder configured"
- Set `DRIVE_FOLDER_ID` in `.env`
- Get ID from Drive folder URL: `https://drive.google.com/drive/folders/FOLDER_ID`

### "Credentials not found"
- Download Google Drive API credentials JSON
- Save to path specified in `DRIVE_CREDENTIALS_PATH`

### "Git not found"
- Install git: `apt-get install git` (Linux) or via Homebrew (Mac)
- Or use `--scan-api` to use GitHub API instead

### "Permission denied"
- Check file permissions on local filesystem
- Verify GitHub token has push permission
- Confirm Google Drive token has write permission

### Conflicts not resolving
- Check conflict files in `.sync/conflicts/`
- Run with `--verbose` for detailed logs
- Review `.sync/audit_trail.jsonl` for decision history

## Future Enhancements

- [ ] S3 sync target
- [ ] Notion API integration
- [ ] Incremental sync (only changed files)
- [ ] Parallel workers for large syncs
- [ ] Web UI for conflict resolution
- [ ] Slack notifications on conflicts
- [ ] Advanced merge strategies (3-way text merge)
