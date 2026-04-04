# AI Sales OS File Sync Engine - START HERE

## What This Is

A production-grade file synchronization engine that keeps three systems in perfect sync:

1. **Local Filesystem** (your development machine)
2. **Google Drive** (team shared documents)
3. **GitHub Repository** (version-controlled code)

## Problem It Solves

- Presentations updated on Drive but not locally?
- Code pushed to GitHub but Drive is stale?
- Multiple sources with different versions of same file?
- Need audit trail of what synced where and when?

**This engine handles it all automatically.**

## How It Works in 30 Seconds

```
┌─────────────┐       ┌──────────────┐       ┌─────────────┐
│   Local     │       │ Google Drive │       │  GitHub     │
│  Filesystem │◄─────►│              │◄─────►│ Repository  │
└─────────────┘       └──────────────┘       └─────────────┘
         │                    │                      │
         └────────────┬───────┴──────────────────────┘
                      │
            ┌─────────▼──────────┐
            │ Unified Manifest   │
            │ (source of truth)  │
            └─────────┬──────────┘
                      │
        ┌─────────────┼──────────────┐
        │             │              │
        ▼             ▼              ▼
    Auto-Sync    Auto-Sync      Auto-Sync
    to Local     to Drive       to GitHub
```

## Quick Start (5 minutes)

### 1. Install
```bash
pip install -r requirements.txt
```

### 2. Configure
```bash
cat > .env << 'EOF'
SYNC_LOCAL_ROOT=/path/to/AI Sales OS
DRIVE_FOLDER_ID=your_folder_id
GITHUB_REPO=owner/repo
GITHUB_TOKEN=your_token
