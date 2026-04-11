"""
GitHub repository scanner for AI Sales OS sync.

Scans GitHub repository and generates FileRecords.
- Uses git commands (git ls-tree, git log) or GitHub API
- Gets file metadata and SHA hashes
- Respects .gitignore
- Maps repo structure to relative paths
"""

import subprocess
import logging
from typing import List, Optional
from datetime import datetime
from pathlib import Path

from models import FileRecord, FileType, SourceState
from classify_files import FileClassifier
from config import GITHUB_REPO, GITHUB_BRANCH, GITHUB_TOKEN, LOCAL_ROOT

logger = logging.getLogger(__name__)


class GitHubScanner:
    """Scans GitHub repository for files to sync."""

    def __init__(
        self,
        repo: Optional[str] = None,
        branch: Optional[str] = None,
        token: Optional[str] = None,
    ):
        """
        Initialize GitHub scanner.

        Args:
            repo: Repository in format 'owner/repo'
            branch: Branch to scan (default: main)
            token: GitHub API token for authentication
        """
        self.repo = repo or GITHUB_REPO
        self.branch = branch or GITHUB_BRANCH
        self.token = token or GITHUB_TOKEN
        self.repo_path = LOCAL_ROOT / ".git"

    def _run_git_command(self, *args: str) -> str:
        """Run a git command and return output."""
        try:
            result = subprocess.run(
                ["git"] + list(args),
                cwd=LOCAL_ROOT,
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode != 0:
                logger.warning(f"Git command failed: {' '.join(args)}")
                return ""
            return result.stdout
        except Exception as e:
            logger.error(f"Error running git command: {e}")
            return ""

    def scan_local_git(self) -> List[FileRecord]:
        """
        Scan files from local git repository.

        Uses git ls-tree and git log to get files and their metadata.
        """
        if not (LOCAL_ROOT / ".git").exists():
            logger.error("Not a git repository")
            return []

        files = []

        try:
            # Get list of files tracked by git
            output = self._run_git_command(
                "ls-tree", "-r", "--name-only", self.branch
            )

            if not output:
                logger.warning("No files found in git repository")
                return []

            file_paths = output.strip().split("\n")

            for relative_path in file_paths:
                if not relative_path:
                    continue

                file_path = LOCAL_ROOT / relative_path

                # Skip if file doesn't exist locally
                if not file_path.exists():
                    continue

                try:
                    # Get file size
                    size = file_path.stat().st_size

                    # Get file hash from git
                    hash_output = self._run_git_command(
                        "hash-object", str(file_path)
                    )
                    file_hash = hash_output.strip() if hash_output else ""

                    # Get last commit info
                    log_output = self._run_git_command(
                        "log", "-1", "--format=%ai", "--", relative_path
                    )
                    mtime = None
                    if log_output:
                        try:
                            mtime = datetime.fromisoformat(
                                log_output.strip().replace(" ", "T").split("+")[0]
                            )
                        except ValueError:
                            mtime = None

                    # Classify file
                    file_name = Path(relative_path).name
                    extension = (
                        f".{file_name.rsplit('.', 1)[1].lower()}"
                        if "." in file_name
                        else ""
                    )

                    classification, source_of_truth = (
                        FileClassifier.classify_file(
                            file_name, extension, relative_path
                        )
                    )

                    # Create FileRecord
                    file_record = FileRecord(
                        file_id=file_hash or relative_path,
                        file_name=file_name,
                        relative_path=relative_path.replace("\\", "/"),
                        file_type=FileType.FILE,
                        extension=extension,
                        classification=classification,
                        source_of_truth=source_of_truth,
                        size_bytes=size,
                        hash_sha256=file_hash,
                    )

                    # Set GitHub source state
                    file_record.sources["github"] = SourceState(
                        exists=True,
                        path=relative_path,
                        last_modified=mtime,
                        hash=file_hash,
                        size=size,
                        metadata={
                            "repo": self.repo,
                            "branch": self.branch,
                        },
                    )

                    files.append(file_record)

                except (OSError, IOError) as e:
                    logger.error(f"Error processing {relative_path}: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error scanning git repository: {e}")

        return files

    def scan(self) -> List[FileRecord]:
        """
        Scan GitHub repository.

        Prefers local git repository if available, falls back to API.
        """
        logger.info(f"Scanning GitHub repository: {self.repo} (branch: {self.branch})")

        files = self.scan_local_git()
        logger.info(f"Scanned {len(files)} files from GitHub repository")
        return files
