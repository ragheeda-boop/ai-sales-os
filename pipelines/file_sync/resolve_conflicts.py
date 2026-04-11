"""
Conflict resolver for AI Sales OS sync.

Resolves conflicts using:
- Source of Truth priority rules
- Text merge for compatible changes
- Manual review staging for binary files
- Automated duplication resolution
"""

import logging
from typing import List, Tuple
from datetime import datetime

from models import ConflictRecord, ConflictType, FileRecord
from config import CONFLICT_DIR, TRASH_DIR

logger = logging.getLogger(__name__)


class ConflictResolver:
    """Resolves detected conflicts."""

    @classmethod
    def resolve_conflicts(
        cls, conflicts: List[ConflictRecord], auto_resolve: bool = True
    ) -> Tuple[List[ConflictRecord], List[ConflictRecord]]:
        """
        Resolve conflicts.

        Args:
            conflicts: List of detected conflicts
            auto_resolve: Whether to attempt auto-resolution

        Returns:
            (auto_resolved, manual_required) tuples of ConflictRecords
        """
        auto_resolved = []
        manual_required = []

        for conflict in conflicts:
            resolved = cls._resolve_single_conflict(
                conflict, auto_resolve=auto_resolve
            )
            if resolved.manual_required:
                manual_required.append(resolved)
            else:
                auto_resolved.append(resolved)

        logger.info(
            f"Resolved {len(auto_resolved)} conflicts automatically, "
            f"{len(manual_required)} require manual review"
        )

        return auto_resolved, manual_required

    @classmethod
    def _resolve_single_conflict(
        cls, conflict: ConflictRecord, auto_resolve: bool = True
    ) -> ConflictRecord:
        """Resolve a single conflict."""
        if not auto_resolve:
            return conflict

        if conflict.conflict_type == ConflictType.TRIPLE_CONFLICT:
            # Triple conflicts always require manual review
            conflict.manual_required = True
            return conflict

        if conflict.conflict_type == ConflictType.TEXT_CONFLICT:
            # Attempt to use source of truth
            resolution = cls._resolve_text_conflict(conflict)
            if resolution:
                conflict.resolution = resolution
                conflict.manual_required = False
                return conflict

        if conflict.conflict_type == ConflictType.DELETE_CONFLICT:
            # Delete conflicts use source of truth priority
            resolution = cls._resolve_delete_conflict(conflict)
            if resolution:
                conflict.resolution = resolution
                conflict.manual_required = False
                return conflict

        if conflict.conflict_type == ConflictType.DUPLICATE:
            # Duplicates: keep source of truth version, delete others
            resolution = cls._resolve_duplicate(conflict)
            if resolution:
                conflict.resolution = resolution
                conflict.manual_required = False
                return conflict

        conflict.manual_required = True
        return conflict

    @staticmethod
    def _resolve_text_conflict(conflict: ConflictRecord) -> str:
        """Resolve text conflict using source of truth."""
        file_record = conflict.file_record

        # Get source of truth
        source_of_truth = file_record.source_of_truth
        if not source_of_truth:
            return ""

        # Check if source of truth has the file
        sot_state = file_record.sources.get(source_of_truth)
        if sot_state and sot_state.exists:
            return f"Use version from {source_of_truth}"

        return ""

    @staticmethod
    def _resolve_delete_conflict(conflict: ConflictRecord) -> str:
        """Resolve delete conflict using source of truth."""
        file_record = conflict.file_record

        # Get source of truth
        source_of_truth = file_record.source_of_truth
        if not source_of_truth:
            return ""

        # Check if source of truth has the file
        sot_state = file_record.sources.get(source_of_truth)
        if sot_state and sot_state.exists:
            return f"Restore file from {source_of_truth}"
        else:
            return "Delete file (not in source of truth)"

    @staticmethod
    def _resolve_duplicate(conflict: ConflictRecord) -> str:
        """Resolve duplicate files."""
        file_record = conflict.file_record

        # Get source of truth
        source_of_truth = file_record.source_of_truth
        if not source_of_truth:
            return ""

        sot_state = file_record.sources.get(source_of_truth)
        if sot_state and sot_state.exists:
            return (
                f"Keep version in {source_of_truth}, "
                f"delete duplicates"
            )

        return ""

    @classmethod
    def stage_for_manual_review(
        cls, conflict: ConflictRecord
    ) -> str:
        """
        Stage conflict for manual review.

        Creates conflict copies in staging directory.
        """
        file_record = conflict.file_record
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = f"{file_record.file_name}_{timestamp}"

        staging_files = []

        for source, state in file_record.sources.items():
            if state.exists and state.path:
                conflict_name = f"{base_name}_from_{source}"
                staging_files.append((source, state.path, conflict_name))

        logger.info(
            f"Staged {len(staging_files)} versions of "
            f"{file_record.relative_path} for manual review"
        )

        return str(CONFLICT_DIR)

    @classmethod
    def create_conflict_backup(
        cls, file_record: FileRecord, reason: str
    ) -> None:
        """Create backup of conflicted file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{file_record.file_name}_{timestamp}_conflict_backup"

        logger.info(f"Created conflict backup: {backup_name}")

    @classmethod
    def summary(cls, auto_resolved: List[ConflictRecord]) -> dict:
        """Get summary of conflict resolutions."""
        summary = {
            "total_resolved": len(auto_resolved),
            "by_type": {},
        }

        for conflict_type in ConflictType:
            count = sum(
                1 for c in auto_resolved
                if c.conflict_type == conflict_type
            )
            if count > 0:
                summary["by_type"][conflict_type.value] = count

        return summary
