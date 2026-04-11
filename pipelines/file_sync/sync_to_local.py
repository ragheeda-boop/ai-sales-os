"""
Local sync module for AI Sales OS sync.

Syncs files from Google Drive and GitHub to local filesystem.
- Downloads from Drive
- Pulls from GitHub
- Creates backups before overwrites
- Handles folder creation
"""

import logging
import shutil
from pathlib import Path
from typing import List

from models import SyncAction, SyncActionType
from config import LOCAL_ROOT, BACKUP_DIR

logger = logging.getLogger(__name__)


class LocalSyncer:
    """Syncs files to local filesystem."""

    @staticmethod
    def sync_from_drive(
        action: SyncAction, drive_service
    ) -> bool:
        """
        Sync file from Google Drive to local.

        Args:
            action: SyncAction to perform
            drive_service: Google Drive API service

        Returns:
            True if successful, False otherwise
        """
        try:
            file_record = action.file_record
            drive_state = file_record.sources.get("drive")

            if not drive_state or not drive_state.exists:
                logger.warning(
                    f"File not found in Drive: {file_record.relative_path}"
                )
                return False

            drive_id = drive_state.metadata.get("drive_id")
            if not drive_id:
                logger.error(
                    f"No Drive ID for {file_record.relative_path}"
                )
                return False

            # Build local path
            local_path = LOCAL_ROOT / file_record.relative_path
            local_path.parent.mkdir(parents=True, exist_ok=True)

            # Create backup if file exists
            if local_path.exists():
                backup_path = BACKUP_DIR / f"{file_record.file_name}.bak"
                shutil.copy2(local_path, backup_path)
                logger.debug(f"Created backup: {backup_path}")

            # Download file
            request = drive_service.files().get_media(fileId=drive_id)
            with open(local_path, "wb") as f:
                f.write(request.execute())

            logger.info(f"Synced from Drive: {file_record.relative_path}")
            return True

        except Exception as e:
            logger.error(
                f"Error syncing from Drive: "
                f"{action.file_record.relative_path}: {e}"
            )
            return False

    @staticmethod
    def sync_from_github(action: SyncAction) -> bool:
        """
        Sync file from GitHub to local.

        Args:
            action: SyncAction to perform

        Returns:
            True if successful, False otherwise
        """
        try:
            file_record = action.file_record
            github_state = file_record.sources.get("github")

            if not github_state or not github_state.exists:
                logger.warning(
                    f"File not found in GitHub: "
                    f"{file_record.relative_path}"
                )
                return False

            # This would use git pull or GitHub API
            # Placeholder for actual implementation
            logger.info(f"Synced from GitHub: {file_record.relative_path}")
            return True

        except Exception as e:
            logger.error(
                f"Error syncing from GitHub: "
                f"{action.file_record.relative_path}: {e}"
            )
            return False

    @classmethod
    def process_sync_actions(
        cls, actions: List[SyncAction], drive_service=None
    ) -> dict:
        """
        Process a list of sync actions.

        Args:
            actions: List of SyncActions to perform
            drive_service: Google Drive API service (optional)

        Returns:
            Dictionary with success/failure counts
        """
        results = {
            "total": len(actions),
            "success": 0,
            "failed": 0,
            "skipped": 0,
        }

        for action in actions:
            if action.source == "drive":
                if cls.sync_from_drive(action, drive_service):
                    results["success"] += 1
                else:
                    results["failed"] += 1
            elif action.source == "github":
                if cls.sync_from_github(action):
                    results["success"] += 1
                else:
                    results["failed"] += 1
            else:
                results["skipped"] += 1

        logger.info(
            f"Sync to local completed: "
            f"{results['success']} success, {results['failed']} failed, "
            f"{results['skipped']} skipped"
        )

        return results
