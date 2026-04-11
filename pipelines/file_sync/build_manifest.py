"""
Manifest builder for AI Sales OS sync.

Merges file lists from local, Drive, and GitHub into a unified manifest.
- Primary key: relative_path
- Detects files in multiple sources
- Handles path normalization
- Assigns deterministic file IDs
"""

import hashlib
import logging
from typing import List, Dict
from pathlib import Path

from models import FileRecord, Manifest
from config import PROJECT_METADATA

logger = logging.getLogger(__name__)


class ManifestBuilder:
    """Builds unified manifest from multiple sources."""

    @staticmethod
    def normalize_path(path: str) -> str:
        """Normalize path to forward slashes."""
        return str(Path(path)).replace("\\", "/").lower()

    @classmethod
    def merge_file_records(
        cls, records: List[FileRecord]
    ) -> Dict[str, FileRecord]:
        """
        Merge file records by relative_path.

        Later records override earlier ones (preference order:
        local > github > drive).
        """
        merged = {}

        for record in records:
            normalized_path = cls.normalize_path(record.relative_path)

            if normalized_path not in merged:
                # New file
                merged[normalized_path] = record
                # Ensure file_id is set deterministically
                if not record.file_id:
                    record.file_id = hashlib.md5(
                        normalized_path.encode()
                    ).hexdigest()
            else:
                # Merge with existing record
                existing = merged[normalized_path]
                for source, state in record.sources.items():
                    if state.exists:
                        existing.sources[source] = state
                        if not existing.source_of_truth:
                            existing.source_of_truth = record.source_of_truth

        return merged

    @classmethod
    def build_manifest(
        cls,
        local_files: List[FileRecord],
        drive_files: List[FileRecord],
        github_files: List[FileRecord],
        project_name: str = "",
    ) -> Manifest:
        """
        Build unified manifest from all sources.

        Args:
            local_files: Files from local filesystem
            drive_files: Files from Google Drive
            github_files: Files from GitHub repository
            project_name: Name of project for manifest metadata

        Returns:
            Unified Manifest object
        """
        logger.info("Building unified manifest")

        # Merge all file records (order determines precedence)
        all_records = github_files + drive_files + local_files
        merged = cls.merge_file_records(all_records)

        # Create manifest
        manifest = Manifest(
            project=project_name or PROJECT_METADATA.get("name", ""),
            total_files=len(merged),
            files=merged,
            metadata=PROJECT_METADATA.copy(),
        )

        logger.info(
            f"Built manifest with {manifest.total_files} files "
            f"({len(local_files)} local, {len(drive_files)} drive, "
            f"{len(github_files)} github)"
        )

        return manifest

    @classmethod
    def get_files_in_multiple_sources(cls, manifest: Manifest) -> List[str]:
        """Get relative paths of files that exist in multiple sources."""
        multi_source = []
        for relative_path, record in manifest.files.items():
            sources_count = sum(
                1 for s in record.sources.values() if s.exists
            )
            if sources_count > 1:
                multi_source.append(relative_path)
        return multi_source

    @classmethod
    def get_single_source_files(cls, manifest: Manifest) -> Dict[str, str]:
        """Get files that exist in only one source."""
        single_source = {}
        for relative_path, record in manifest.files.items():
            sources_count = sum(
                1 for s in record.sources.values() if s.exists
            )
            if sources_count == 1:
                for source, state in record.sources.items():
                    if state.exists:
                        single_source[relative_path] = source
                        break
        return single_source

    @classmethod
    def get_files_by_source(
        cls, manifest: Manifest, source: str
    ) -> List[FileRecord]:
        """Get all files that exist in a specific source."""
        return [
            r for r in manifest.files.values()
            if r.sources.get(source, {}).exists
        ]

    @classmethod
    def summary(cls, manifest: Manifest) -> Dict:
        """Get summary statistics for manifest."""
        total = manifest.total_files
        local_count = sum(
            1 for r in manifest.files.values()
            if r.sources.get("local", {}).exists
        )
        drive_count = sum(
            1 for r in manifest.files.values()
            if r.sources.get("drive", {}).exists
        )
        github_count = sum(
            1 for r in manifest.files.values()
            if r.sources.get("github", {}).exists
        )
        multi_source = len(cls.get_files_in_multiple_sources(manifest))
        conflicts = sum(1 for r in manifest.files.values() if r.conflict_flag)

        return {
            "total_files": total,
            "local": local_count,
            "drive": drive_count,
            "github": github_count,
            "multi_source": multi_source,
            "conflicts": conflicts,
        }
