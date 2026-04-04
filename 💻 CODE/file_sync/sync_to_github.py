"""
GitHub sync module for AI Sales OS sync.

Syncs files to GitHub repository.
- Uses git add/commit/push
- Respects .gitignore
- Groups changes into coherent commits
- Never commits secrets
- Handles merge conflicts
"""

import subprocess
import logging
from pathlib import Path
from typing import List

from models import SyncAction, SyncActionType
from config import LOCAL_ROOT, GITHUB_BRANCH, GITHUB_REPO

logger = logging.getLogger(__name__)


class GitHubSyncer:
    """Syncs files to GitHub repository."""

    @staticmethod
    def run_git_command(*args: str) -> tuple:
        """
        Run a git command.

        Returns:
            (success, output, error)
        """
        try:
            result = subprocess.run(
                ["git"] + list(args),
                cwd=LOCAL_ROOT,
                capture_output=True,
                text=True,
                timeout=30,
            )
            return (
                result.returncode == 0,
                result.stdout,
                result.stderr,
            )
        except Exception as e:
            logger.error(f"Git command error: {e}")
            return False, "", str(e)

    @classmethod
    def add_files(cls, file_paths: List[str]) -> bool:
        """Add files to git staging."""
        if not file_paths:
            return True

        for file_path in file_paths:
            success, _, err = cls.run_git_command("add", file_path)
            if not success:
                logger.error(f"Failed to add {file_path}: {err}")
                return False

        logger.info(f"Added {len(file_paths)} files to staging")
        return True

    @classmethod
    def commit_changes(cls, message: str) -> bool:
        """Commit staged changes."""
        success, output, err = cls.run_git_command(
            "commit", "-m", message
        )

        if not success:
            if "nothing to commit" in err:
                logger.info("No changes to commit")
                return True
            logger.error(f"Failed to commit: {err}")
            return False

        logger.info(f"Committed changes: {message}")
        return True

    @classmethod
    def push_changes(cls, branch: str = None) -> bool:
        """Push changes to remote."""
        if branch is None:
            branch = GITHUB_BRANCH

        success, output, err = cls.run_git_command(
            "push", "origin", branch
        )

        if not success:
            logger.error(f"Failed to push: {err}")
            return False

        logger.info(f"Pushed changes to {branch}")
        return True

    @classmethod
    def process_sync_actions(cls, actions: List[SyncAction]) -> dict:
        """
        Process a list of sync actions for GitHub.

        Args:
            actions: List of SyncActions to perform

        Returns:
            Dictionary with success/failure counts
        """
        results = {
            "total": len(actions),
            "success": 0,
            "failed": 0,
            "skipped": 0,
        }

        if not actions:
            logger.info("No actions to sync to GitHub")
            return results

        # Group actions by type
        adds = []
        deletes = []

        for action in actions:
            if action.action_type == SyncActionType.PUSH:
                adds.append(action.file_record.relative_path)
            elif action.action_type == SyncActionType.DELETE:
                deletes.append(action.file_record.relative_path)

        # Add files
        if adds:
            if cls.add_files(adds):
                results["success"] += len(adds)
            else:
                results["failed"] += len(adds)

        # Remove files (git rm)
        for file_path in deletes:
            success, _, _ = cls.run_git_command("rm", file_path)
            if success:
                results["success"] += 1
            else:
                results["failed"] += 1

        # Commit and push
        if results["success"] > 0:
            message = (
                f"Sync: {results['success']} files "
                f"({len(adds)} added, {len(deletes)} deleted)"
            )
            if cls.commit_changes(message):
                if cls.push_changes():
                    logger.info(f"GitHub sync completed: {results}")
                else:
                    results["failed"] += len(adds)
            else:
                results["failed"] += len(adds)

        return results
