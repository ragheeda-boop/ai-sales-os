"""
Logging manager for AI Sales OS sync.

Provides structured logging:
- Console output (colored)
- File output (JSON lines for audit trail)
- Sync operation tracking
- Performance metrics
"""

import logging
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

from config import (
    LOG_LEVEL,
    SYNC_LOG_FILE,
    AUDIT_LOG_FILE,
    ERROR_LOG_FILE,
    AUDIT_TRAIL_FILE,
)


class ColoredFormatter(logging.Formatter):
    """Colored console formatter for logs."""

    COLORS = {
        "DEBUG": "\033[36m",      # Cyan
        "INFO": "\033[32m",       # Green
        "WARNING": "\033[33m",    # Yellow
        "ERROR": "\033[31m",      # Red
        "CRITICAL": "\033[35m",   # Magenta
    }
    RESET = "\033[0m"

    def format(self, record):
        """Format with colors."""
        if record.levelname in self.COLORS:
            record.levelname = (
                f"{self.COLORS[record.levelname]}"
                f"{record.levelname}{self.RESET}"
            )
        return super().format(record)


class JsonFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record):
        """Format as JSON."""
        data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "module": record.module,
            "function": record.funcName,
            "message": record.getMessage(),
        }
        if record.exc_info:
            data["exception"] = self.formatException(record.exc_info)
        return json.dumps(data)


def setup_logging(log_dir: Optional[Path] = None) -> logging.Logger:
    """
    Setup logging for sync operations.

    Args:
        log_dir: Directory for log files (default: LOG_DIR from config)

    Returns:
        Configured logger instance
    """
    if log_dir is None:
        log_dir = SYNC_LOG_FILE.parent

    log_dir.mkdir(parents=True, exist_ok=True)

    # Root logger
    logger = logging.getLogger("sync")
    logger.setLevel(LOG_LEVEL)

    # Remove existing handlers
    logger.handlers.clear()

    # Console handler (colored)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(
        ColoredFormatter(
            "%(levelname)s - %(name)s - %(message)s"
        )
    )
    logger.addHandler(console_handler)

    # Sync log file
    sync_handler = logging.FileHandler(SYNC_LOG_FILE)
    sync_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
        )
    )
    logger.addHandler(sync_handler)

    # JSON log file
    json_handler = logging.FileHandler(AUDIT_LOG_FILE)
    json_handler.setFormatter(JsonFormatter())
    logger.addHandler(json_handler)

    # Error log file
    error_handler = logging.FileHandler(ERROR_LOG_FILE)
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
        )
    )
    logger.addHandler(error_handler)

    logger.info("Logging initialized")
    return logger


class AuditLogger:
    """Logs audit trail entries (append-only)."""

    def __init__(self, audit_file: Optional[Path] = None):
        """Initialize audit logger."""
        self.audit_file = audit_file or AUDIT_TRAIL_FILE
        self.audit_file.parent.mkdir(parents=True, exist_ok=True)

    def log_entry(self, entry_data: dict) -> None:
        """
        Log an audit trail entry.

        Args:
            entry_data: Dictionary of audit data
        """
        try:
            entry_data["timestamp"] = datetime.utcnow().isoformat()
            with open(self.audit_file, "a") as f:
                f.write(json.dumps(entry_data) + "\n")
        except Exception as e:
            logging.error(f"Error writing audit log: {e}")

    def read_entries(self, limit: int = 100) -> list:
        """Read recent audit entries."""
        entries = []
        try:
            with open(self.audit_file, "r") as f:
                for line in f:
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
            return entries[-limit:]
        except FileNotFoundError:
            return []


def generate_sync_report(actions: list, conflicts: list) -> dict:
    """
    Generate sync report with statistics.

    Args:
        actions: List of sync actions performed
        conflicts: List of conflicts detected

    Returns:
        Dictionary with report data
    """
    report = {
        "timestamp": datetime.utcnow().isoformat(),
        "total_actions": len(actions),
        "total_conflicts": len(conflicts),
        "actions_by_type": {},
        "conflicts_by_type": {},
    }

    for action in actions:
        action_type = str(action.action_type.value)
        report["actions_by_type"][action_type] = (
            report["actions_by_type"].get(action_type, 0) + 1
        )

    for conflict in conflicts:
        conflict_type = str(conflict.conflict_type.value)
        report["conflicts_by_type"][conflict_type] = (
            report["conflicts_by_type"].get(conflict_type, 0) + 1
        )

    return report
