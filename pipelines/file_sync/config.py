"""
Configuration module for AI Sales OS file synchronization engine.

Provides centralized configuration for:
- Local filesystem roots
- Google Drive folder IDs
- GitHub repository details
- File classification rules (by extension and path)
- Conflict resolution strategies
- Safety thresholds
- Paths for manifests, logs, backups
- .env loading support
"""

import os
from pathlib import Path
from typing import Dict, List, Set
from dotenv import load_dotenv

# Load .env file if present
load_dotenv()

# ============================================================================
# FILESYSTEM PATHS
# ============================================================================

# Root directory for local sync operations
LOCAL_ROOT = Path(os.getenv("SYNC_LOCAL_ROOT", "."))

# Directory where manifests, logs, and audit trails are stored
SYNC_DATA_DIR = LOCAL_ROOT / ".sync"
SYNC_DATA_DIR.mkdir(exist_ok=True)

# Manifest file paths
MANIFEST_FILE = SYNC_DATA_DIR / "manifest.json"
MANIFEST_HISTORY_DIR = SYNC_DATA_DIR / "manifest_history"
MANIFEST_HISTORY_DIR.mkdir(exist_ok=True)

# Log file paths
LOG_DIR = SYNC_DATA_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

# Backup directory
BACKUP_DIR = SYNC_DATA_DIR / "backups"
BACKUP_DIR.mkdir(exist_ok=True)

# Conflict staging directory
CONFLICT_DIR = SYNC_DATA_DIR / "conflicts"
CONFLICT_DIR.mkdir(exist_ok=True)

# Trash directory for safely deleted files
TRASH_DIR = SYNC_DATA_DIR / ".trash"
TRASH_DIR.mkdir(exist_ok=True)

# ============================================================================
# GOOGLE DRIVE CONFIGURATION
# ============================================================================

DRIVE_FOLDER_ID = os.getenv("DRIVE_FOLDER_ID", "")
DRIVE_CREDENTIALS_PATH = os.getenv(
    "DRIVE_CREDENTIALS_PATH",
    str(LOCAL_ROOT / "credentials.json")
)
DRIVE_TOKEN_PATH = SYNC_DATA_DIR / "drive_token.pickle"

# ============================================================================
# GITHUB CONFIGURATION
# ============================================================================

GITHUB_REPO = os.getenv("GITHUB_REPO", "")
GITHUB_BRANCH = os.getenv("GITHUB_BRANCH", "main")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
GITHUB_USER = os.getenv("GITHUB_USER", "")

# ============================================================================
# FILE CLASSIFICATION RULES
# ============================================================================

EXTENSION_CATEGORIES = {
    ".py": "code",
    ".js": "code",
    ".ts": "code",
    ".tsx": "code",
    ".jsx": "code",
    ".java": "code",
    ".go": "code",
    ".rs": "code",
    ".sh": "code",
    ".bash": "code",
    ".yml": "code",
    ".yaml": "code",
    ".json": "code",
    ".xml": "code",
    ".sql": "code",
    ".md": "documentation_md",
    ".txt": "documentation_md",
    ".rst": "documentation_md",
    ".adoc": "documentation_md",
    ".docx": "documentation_office",
    ".doc": "documentation_office",
    ".odt": "documentation_office",
    ".pptx": "presentation",
    ".ppt": "presentation",
    ".odp": "presentation",
    ".xlsx": "spreadsheet_office",
    ".xls": "spreadsheet_office",
    ".csv": "spreadsheet_csv",
    ".tsv": "spreadsheet_csv",
    ".ods": "spreadsheet_office",
    ".jsonl": "data_json",
    ".parquet": "data_json",
    ".sqlite": "data_json",
    ".db": "data_json",
    ".png": "media_small",
    ".jpg": "media_small",
    ".jpeg": "media_small",
    ".gif": "media_small",
    ".svg": "media_small",
    ".ico": "media_small",
    ".webp": "media_small",
    ".mp4": "media_large",
    ".mov": "media_large",
    ".avi": "media_large",
    ".mp3": "media_large",
    ".wav": "media_large",
    ".m4a": "media_large",
    ".pdf": "media_small",
    ".zip": "archive",
    ".tar": "archive",
    ".gz": "archive",
    ".rar": "archive",
    ".7z": "archive",
    ".env": "secret",
    ".env.local": "secret",
    ".env.example": "config_template",
    ".gitignore": "config_template",
    ".gitattributes": "config_template",
    ".editorconfig": "config_template",
    ".prettierrc": "config_template",
    ".eslintrc": "config_template",
    ".pylintrc": "config_template",
    ".log": "log",
}

# Source of Truth priority by category
SOURCE_OF_TRUTH_PRIORITY = {
    "code": ["github", "local", "drive"],
    "documentation_md": ["github", "local", "drive"],
    "documentation_office": ["drive", "local", "github"],
    "presentation": ["drive", "local", "github"],
    "spreadsheet_csv": ["github", "local", "drive"],
    "spreadsheet_office": ["drive", "local", "github"],
    "data_json": ["github", "local", "drive"],
    "media_small": ["github", "local", "drive"],
    "media_large": ["drive", "local", "github"],
    "archive": ["drive", "local", "github"],
    "config_template": ["github", "local", "drive"],
    "secret": ["local"],
    "log": ["local"],
    "cache": ["local"],
}

# ============================================================================
# SYNC RULES BY CATEGORY
# ============================================================================

SYNC_TO_GITHUB = {
    "code",
    "documentation_md",
    "spreadsheet_csv",
    "data_json",
    "config_template",
}

SYNC_TO_DRIVE = {
    "documentation_office",
    "presentation",
    "spreadsheet_office",
    "data_json",
    "media_large",
    "media_small",
    "archive",
    "documentation_md",
}

SYNC_TO_LOCAL = {
    "code",
    "documentation_md",
    "documentation_office",
    "presentation",
    "spreadsheet_csv",
    "spreadsheet_office",
    "data_json",
    "media_small",
    "media_large",
    "archive",
    "config_template",
}

# ============================================================================
# SAFETY THRESHOLDS
# ============================================================================

MAX_DELETE_PERCENT = 10
MAX_MODIFY_PERCENT = 50
MAX_AUTO_SYNC_SIZE_MB = 100
MAX_AUTO_RESOLVE_CONFLICTS = 5

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

LOG_LEVEL = os.getenv("SYNC_LOG_LEVEL", "INFO")
SYNC_LOG_FILE = LOG_DIR / "sync.log"
AUDIT_LOG_FILE = LOG_DIR / "audit.log"
ERROR_LOG_FILE = LOG_DIR / "errors.log"
AUDIT_TRAIL_FILE = SYNC_DATA_DIR / "audit_trail.jsonl"
MANIFEST_HISTORY_LIMIT = 30

# ============================================================================
# PERFORMANCE TUNING
# ============================================================================

MAX_WORKERS = 4
CHUNK_SIZE_MB = 10
API_TIMEOUT = 30
MAX_RETRIES = 3

# ============================================================================
# IGNORE PATTERNS
# ============================================================================

IGNORE_PATTERNS: List[str] = [
    ".git/",
    ".github/",
    "__pycache__/",
    "*.pyc",
    ".pytest_cache/",
    ".mypy_cache/",
    ".venv/",
    "venv/",
    "node_modules/",
    ".next/",
    "dist/",
    "build/",
    ".DS_Store",
    "Thumbs.db",
    "*.swp",
    "*.swo",
    "*~",
    ".idea/",
    ".vscode/",
    ".sync/",
    ".trash/",
]

# ============================================================================
# PROJECT METADATA
# ============================================================================

PROJECT_NAME = "AI Sales OS"
PROJECT_VERSION = "4.3"
SYNC_VERSION = "1.0"

PROJECT_METADATA = {
    "name": PROJECT_NAME,
    "sync_version": SYNC_VERSION,
    "project_version": PROJECT_VERSION,
    "description": "Production-grade file synchronization for AI Sales OS",
}
