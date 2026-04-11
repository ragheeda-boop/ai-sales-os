"""
Manifest comparator for AI Sales OS sync.

Compares current and previous manifests to detect changes.
- Detects: new, modified, deleted, moved, renamed files
- Tracks change history
- Generates change report
"""

import logging
from typing import List, Dict, Tuple
from dataclasses import dataclass

from models import FileRecord, Manifest, ChangeType

logger = logging.getLogger(__name__)


@dataclass
class Change:
    """Represents a change between manifests."""
    relative_path: str
    change_type: ChangeType
    file_record: FileRecord
    old_path: str = ""
    old_hash: str = ""
    new_hash: str = ""


class ManifestComparator:
    """Compares two manifests to detect changes."""

    @staticmethod
    def compare_manifests(
        current: Manifest, previous: Manifest
    ) -> List[Change]:
        """
        Compare two manifests and detect changes.

        Args:
            current: Current manifest
            previous: Previous manifest (from last run)

        Returns:
            List of Change objects
        """
        changes = []

        # Track which files from previous have been matched
        matched_previous = set()

        # Check current files for new and modified
        for path, current_file in current.files.items():
            if path in previous.files:
                # File exists in both
                prev_file = previous.files[path]
                matched_previous.add(path)

                if current_file.hash_sha256 != prev_file.hash_sha256:
                    # File was modified
                    changes.append(
                        Change(
                            relative_path=path,
                            change_type=ChangeType.MODIFIED,
                            file_record=current_file,
                            old_hash=prev_file.hash_sha256 or "",
                            new_hash=current_file.hash_sha256 or "",
                        )
                    )
                else:
                    # File unchanged
                    changes.append(
                        Change(
                            relative_path=path,
                            change_type=ChangeType.UNCHANGED,
                            file_record=current_file,
                        )
                    )
            else:
                # New file (check if it's a rename/move)
                renamed_from = ManifestComparator._find_renamed_file(
                    current_file, previous
                )
                if renamed_from:
                    changes.append(
                        Change(
                            relative_path=path,
                            change_type=ChangeType.RENAMED,
                            file_record=current_file,
                            old_path=renamed_from,
                        )
                    )
                    matched_previous.add(renamed_from)
                else:
                    # Truly new file
                    changes.append(
                        Change(
                            relative_path=path,
                            change_type=ChangeType.NEW,
                            file_record=current_file,
                        )
                    )

        # Check for deleted files
        for path, prev_file in previous.files.items():
            if path not in matched_previous:
                changes.append(
                    Change(
                        relative_path=path,
                        change_type=ChangeType.DELETED,
                        file_record=prev_file,
                    )
                )

        return changes

    @staticmethod
    def _find_renamed_file(
        current_file: FileRecord, previous: Manifest
    ) -> str:
        """
        Find if file was renamed (same hash, different path).

        Returns:
            Old path if renamed, empty string otherwise.
        """
        if not current_file.hash_sha256:
            return ""

        for path, prev_file in previous.files.items():
            if (
                prev_file.hash_sha256 == current_file.hash_sha256
                and path != current_file.relative_path
            ):
                return path

        return ""

    @classmethod
    def get_change_summary(cls, changes: List[Change]) -> Dict[str, int]:
        """Get summary of changes by type."""
        summary = {
            "new": sum(1 for c in changes if c.change_type == ChangeType.NEW),
            "modified": sum(
                1 for c in changes if c.change_type == ChangeType.MODIFIED
            ),
            "deleted": sum(
                1 for c in changes if c.change_type == ChangeType.DELETED
            ),
            "renamed": sum(
                1 for c in changes if c.change_type == ChangeType.RENAMED
            ),
            "unchanged": sum(
                1 for c in changes if c.change_type == ChangeType.UNCHANGED
            ),
        }
        return summary

    @classmethod
    def filter_by_type(
        cls, changes: List[Change], change_type: ChangeType
    ) -> List[Change]:
        """Filter changes by type."""
        return [c for c in changes if c.change_type == change_type]

    @classmethod
    def generate_report(cls, changes: List[Change]) -> str:
        """Generate human-readable change report."""
        summary = cls.get_change_summary(changes)

        report = "Manifest Change Report\n"
        report += "=" * 50 + "\n\n"

        for change_type in ChangeType:
            count = sum(
                1 for c in changes if c.change_type == change_type
            )
            if count > 0:
                report += f"{change_type.value.upper()}: {count}\n"

        if summary["new"] > 0:
            report += "\nNew Files:\n"
            for c in cls.filter_by_type(changes, ChangeType.NEW):
                report += f"  + {c.relative_path}\n"

        if summary["modified"] > 0:
            report += "\nModified Files:\n"
            for c in cls.filter_by_type(changes, ChangeType.MODIFIED):
                report += f"  ~ {c.relative_path}\n"

        if summary["deleted"] > 0:
            report += "\nDeleted Files:\n"
            for c in cls.filter_by_type(changes, ChangeType.DELETED):
                report += f"  - {c.relative_path}\n"

        if summary["renamed"] > 0:
            report += "\nRenamed Files:\n"
            for c in cls.filter_by_type(changes, ChangeType.RENAMED):
                report += f"  → {c.old_path} → {c.relative_path}\n"

        return report
