"""
Local filesystem scanner for AI Sales OS sync.

Scans the local filesystem and generates FileRecords for each file.
- Computes SHA256 hashes
- Respects .gitignore patterns
- Skips cache/temp directories
- Captures file metadata (size, modification time)
"""

import os
import hashlib
from pathlib import Path
from typing import List, Optional
from datetime import datetime
import logging

from models import FileRecord, FileType, SourceState
from classify_files import FileClassifier
from config import IGNORE_PATTERNS, SKIP_DIRS, LOCAL_ROOT

logger = logging.getLogger(__name__)


class LocalScanner:
    """Scans local filesystem for files to sync."""

    @staticmethod
    def compute_hash(file_path: Path, chunk_size: int = 8192) -> str:
        """Compute SHA256 hash of a file."""
        sha256 = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                while chunk := f.read(chunk_size):
                    sha256.update(chunk)
            return sha256.hexdigest()
        except (IOError, OSError) as e:
            logger.error(f"Failed to hash {file_path}: {e}")
            return ""

    @staticmethod
    def should_skip(relative_path: str) -> bool:
        """Check if path should be skipped."""
        parts = Path(relative_path).parts
        for part in parts:
            if part in SKIP_DIRS or part.startswith("."):
                return True

        # Check against ignore patterns
        for pattern in IGNORE_PATTERNS:
            if pattern.endswith("/"):
                pattern = pattern[:-1]
            if pattern in relative_path or relative_path.startswith(pattern):
                return True

        return False

    @classmethod
    def scan_directory(
        cls, root_path: Optional[Path] = None
    ) -> List[FileRecord]:
        """
        Scan local filesystem and return list of FileRecords.

        Args:
            root_path: Root directory to scan. Defaults to LOCAL_ROOT.

        Returns:
            List of FileRecord objects for all non-ignored files.
        """
        if root_path is None:
            root_path = LOCAL_ROOT

        root_path = Path(root_path).resolve()
        files = []

        logger.info(f"Scanning local filesystem: {root_path}")

        for dirpath, dirnames, filenames in os.walk(root_path, topdown=True):
            # Skip directories
            dirnames[:] = [
                d for d in dirnames
                if d not in SKIP_DIRS and not d.startswith(".")
            ]

            current_dir = Path(dirpath)

            for filename in filenames:
                file_path = current_dir / filename
                relative_path = file_path.relative_to(root_path)
                relative_path_str = str(relative_path).replace("\\", "/")

                # Skip if matches ignore patterns
                if cls.should_skip(relative_path_str):
                    continue

                try:
                    # Get file info
                    stat = file_path.stat()
                    size = stat.st_size
                    mtime = datetime.fromtimestamp(stat.st_mtime)

                    # Compute hash
                    file_hash = cls.compute_hash(file_path)

                    # Classify file
                    extension = file_path.suffix.lower()
                    classification, source_of_truth = (
                        FileClassifier.classify_file(
                            filename, extension, relative_path_str
                        )
                    )

                    # Create FileRecord
                    file_record = FileRecord(
                        file_id=hashlib.md5(
                            relative_path_str.encode()
                        ).hexdigest(),
                        file_name=filename,
                        relative_path=relative_path_str,
                        file_type=FileType.FILE,
                        extension=extension,
                        classification=classification,
                        source_of_truth=source_of_truth,
                        size_bytes=size,
                        hash_sha256=file_hash,
                    )

                    # Set local source state
                    file_record.sources["local"] = SourceState(
                        exists=True,
                        path=str(file_path),
                        last_modified=mtime,
                        hash=file_hash,
                        size=size,
                    )

                    files.append(file_record)

                except (IOError, OSError) as e:
                    logger.error(f"Error scanning {file_path}: {e}")
                    continue

        logger.info(f"Scanned {len(files)} files from local filesystem")
        return files

    @classmethod
    def scan(cls, root_path: Optional[Path] = None) -> List[FileRecord]:
        """Convenience method for scanning local filesystem."""
        return cls.scan_directory(root_path)
