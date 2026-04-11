"""
Conflict detector for AI Sales OS sync.

Detects conflicts when:
- Same file modified in multiple sources
- File deleted in one source but exists in others
- Binary files with different versions
- Duplicate files (same content, different paths)
"""

import logging
from typing import List
from difflib import unified_diff

from models import FileRecord, Manifest, ConflictRecord, ConflictType

logger = logging.getLogger(__name__)


class ConflictDetector:
    """Detects conflicts in manifest."""

    @classmethod
    def detect_conflicts(cls, manifest: Manifest) -> List[ConflictRecord]:
        """
        Detect all conflicts in manifest.

        Args:
            manifest: Manifest to analyze

        Returns:
            List of ConflictRecord objects
        """
        conflicts = []

        for relative_path, file_record in manifest.files.items():
            # Check for triple conflicts (all 3 sources different)
            conflict = cls._check_triple_conflict(file_record)
            if conflict:
                conflicts.append(conflict)
                continue

            # Check for text conflicts
            conflict = cls._check_text_conflict(file_record)
            if conflict:
                conflicts.append(conflict)
                continue

            # Check for delete conflicts
            conflict = cls._check_delete_conflict(file_record)
            if conflict:
                conflicts.append(conflict)
                continue

            # Check for permission conflicts
            conflict = cls._check_permission_conflict(file_record)
            if conflict:
                conflicts.append(conflict)

        # Check for duplicate files
        duplicates = cls._find_duplicate_files(manifest)
        conflicts.extend(duplicates)

        return conflicts

    @staticmethod
    def _check_triple_conflict(file_record: FileRecord) -> ConflictRecord:
        """Check if file has different versions in all 3 sources."""
        sources_with_different_hashes = []
        hashes_set = set()

        for source in ["local", "drive", "github"]:
            state = file_record.sources.get(source)
            if state and state.exists and state.hash:
                sources_with_different_hashes.append(source)
                hashes_set.add(state.hash)

        if len(sources_with_different_hashes) == 3 and len(hashes_set) == 3:
            return ConflictRecord(
                file_record=file_record,
                conflict_type=ConflictType.TRIPLE_CONFLICT,
                sources_involved=sources_with_different_hashes,
                manual_required=True,
                notes="File modified in all three sources with different contents",
            )

        return None

    @staticmethod
    def _check_text_conflict(file_record: FileRecord) -> ConflictRecord:
        """Check for text file conflicts."""
        from classify_files import FileClassifier

        # Only check text files
        if FileClassifier.is_binary(file_record.extension):
            return None

        # Check if file exists with different hashes in 2+ sources
        sources_with_data = [
            (source, state)
            for source, state in file_record.sources.items()
            if state.exists and state.hash
        ]

        if len(sources_with_data) < 2:
            return None

        hashes_set = set(state.hash for _, state in sources_with_data)
        if len(hashes_set) > 1:
            sources_involved = [source for source, _ in sources_with_data]
            return ConflictRecord(
                file_record=file_record,
                conflict_type=ConflictType.TEXT_CONFLICT,
                sources_involved=sources_involved,
                manual_required=True,
                notes="Text file modified in multiple sources",
            )

        return None

    @staticmethod
    def _check_delete_conflict(file_record: FileRecord) -> ConflictRecord:
        """Check for delete conflicts (deleted in one, exists in others)."""
        existing_sources = [
            source
            for source, state in file_record.sources.items()
            if state.exists
        ]
        missing_sources = [
            source
            for source, state in file_record.sources.items()
            if not state.exists
        ]

        if len(existing_sources) > 0 and len(missing_sources) > 0:
            return ConflictRecord(
                file_record=file_record,
                conflict_type=ConflictType.DELETE_CONFLICT,
                sources_involved=existing_sources + missing_sources,
                manual_required=True,
                notes=(
                    f"File deleted in {missing_sources} "
                    f"but still exists in {existing_sources}"
                ),
            )

        return None

    @staticmethod
    def _check_permission_conflict(file_record: FileRecord) -> ConflictRecord:
        """Check for permission conflicts."""
        # This would check if files have different permissions across sources
        # Placeholder for future implementation
        return None

    @staticmethod
    def _find_duplicate_files(manifest: Manifest) -> List[ConflictRecord]:
        """Find duplicate files (same content, different paths)."""
        duplicates = []
        hash_to_files = {}

        # Group files by hash
        for relative_path, file_record in manifest.files.items():
            if file_record.hash_sha256:
                if file_record.hash_sha256 not in hash_to_files:
                    hash_to_files[file_record.hash_sha256] = []
                hash_to_files[file_record.hash_sha256].append(
                    (relative_path, file_record)
                )

        # Find hashes with multiple files
        for file_hash, files in hash_to_files.items():
            if len(files) > 1:
                # Multiple files with same hash = duplicates
                paths = [path for path, _ in files]
                primary_file = files[0][1]

                conflict = ConflictRecord(
                    file_record=primary_file,
                    conflict_type=ConflictType.DUPLICATE,
                    sources_involved=["local", "drive", "github"],
                    manual_required=True,
                    notes=(
                        f"Duplicate file found at: {', '.join(paths)}"
                    ),
                )
                duplicates.append(conflict)

        return duplicates

    @classmethod
    def summary(cls, conflicts: List[ConflictRecord]) -> dict:
        """Get summary of conflicts."""
        summary = {
            "total": len(conflicts),
            "by_type": {},
            "manual_required": sum(
                1 for c in conflicts if c.manual_required
            ),
        }

        for conflict_type in ConflictType:
            count = sum(
                1 for c in conflicts if c.conflict_type == conflict_type
            )
            if count > 0:
                summary["by_type"][conflict_type.value] = count

        return summary
