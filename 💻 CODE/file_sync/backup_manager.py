"""
Backup manager for AI Sales OS sync.

Manages file backups:
- Creates timestamped .tar.gz backups
- Rotates old backups (keeps last 30)
- Verifies backup integrity
- Supports restore operations
"""

import tarfile
import logging
from pathlib import Path
from typing import List, Optional
from datetime import datetime
import os

from config import BACKUP_DIR, LOCAL_ROOT

logger = logging.getLogger(__name__)


class BackupManager:
    """Manages file backups."""

    @staticmethod
    def create_backup(
        files_to_backup: List[Path], backup_dir: Path = None
    ) -> Optional[Path]:
        """
        Create timestamped backup of files.

        Args:
            files_to_backup: List of file paths to backup
            backup_dir: Directory to store backup (default: BACKUP_DIR)

        Returns:
            Path to created backup file, None on error
        """
        if backup_dir is None:
            backup_dir = BACKUP_DIR

        backup_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"backup_{timestamp}.tar.gz"

        try:
            with tarfile.open(backup_path, "w:gz") as tar:
                for file_path in files_to_backup:
                    if file_path.exists():
                        arcname = file_path.relative_to(LOCAL_ROOT)
                        tar.add(str(file_path), arcname=str(arcname))

            backup_size = backup_path.stat().st_size
            logger.info(
                f"Created backup: {backup_path} "
                f"({backup_size / 1024 / 1024:.2f} MB)"
            )

            return backup_path

        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            return None

    @staticmethod
    def verify_backup(backup_path: Path) -> bool:
        """
        Verify backup integrity.

        Args:
            backup_path: Path to backup file

        Returns:
            True if valid, False otherwise
        """
        try:
            with tarfile.open(backup_path, "r:gz") as tar:
                tar.getmembers()
            logger.info(f"Backup verified: {backup_path}")
            return True
        except Exception as e:
            logger.error(f"Backup verification failed: {e}")
            return False

    @staticmethod
    def restore_from_backup(
        backup_path: Path, target_dir: Path
    ) -> bool:
        """
        Restore files from backup.

        Args:
            backup_path: Path to backup file
            target_dir: Target directory for restore

        Returns:
            True if successful, False otherwise
        """
        try:
            target_dir.mkdir(parents=True, exist_ok=True)

            with tarfile.open(backup_path, "r:gz") as tar:
                tar.extractall(path=target_dir)

            logger.info(f"Restored from backup to {target_dir}")
            return True

        except Exception as e:
            logger.error(f"Error restoring from backup: {e}")
            return False

    @staticmethod
    def list_backups(backup_dir: Path = None) -> List[Path]:
        """
        List available backups.

        Args:
            backup_dir: Backup directory (default: BACKUP_DIR)

        Returns:
            List of backup files, sorted by date (newest first)
        """
        if backup_dir is None:
            backup_dir = BACKUP_DIR

        if not backup_dir.exists():
            return []

        backups = sorted(
            backup_dir.glob("backup_*.tar.gz"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )

        return backups

    @classmethod
    def rotate_backups(
        cls, backup_dir: Path = None, keep: int = 30
    ) -> int:
        """
        Rotate backups, keeping only the most recent.

        Args:
            backup_dir: Backup directory (default: BACKUP_DIR)
            keep: Number of backups to keep (default: 30)

        Returns:
            Number of backups deleted
        """
        if backup_dir is None:
            backup_dir = BACKUP_DIR

        backups = cls.list_backups(backup_dir)
        deleted = 0

        for backup_path in backups[keep:]:
            try:
                backup_path.unlink()
                deleted += 1
                logger.info(f"Deleted old backup: {backup_path}")
            except Exception as e:
                logger.error(f"Error deleting backup: {e}")

        if deleted > 0:
            logger.info(f"Rotated backups: deleted {deleted}")

        return deleted

    @classmethod
    def get_latest_backup(cls, backup_dir: Path = None) -> Optional[Path]:
        """
        Get the most recent backup.

        Args:
            backup_dir: Backup directory (default: BACKUP_DIR)

        Returns:
            Path to latest backup, None if no backups exist
        """
        backups = cls.list_backups(backup_dir)
        return backups[0] if backups else None

    @staticmethod
    def get_backup_info(backup_path: Path) -> dict:
        """
        Get information about a backup.

        Args:
            backup_path: Path to backup file

        Returns:
            Dictionary with backup info
        """
        try:
            stat = backup_path.stat()
            with tarfile.open(backup_path, "r:gz") as tar:
                members = tar.getmembers()

            return {
                "path": str(backup_path),
                "size": stat.st_size,
                "created": datetime.fromtimestamp(stat.st_mtime),
                "files": len(members),
                "verified": True,
            }
        except Exception as e:
            logger.error(f"Error getting backup info: {e}")
            return {}
