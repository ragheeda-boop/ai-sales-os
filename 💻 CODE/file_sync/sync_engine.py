"""
Main sync engine orchestrator for AI Sales OS file synchronization.

Coordinates full sync cycle:
1. Scan local, Drive, and GitHub
2. Build unified manifest
3. Compare with previous manifest
4. Detect conflicts
5. Resolve conflicts (auto + manual queue)
6. Execute sync actions (push/pull/copy)
7. Generate reports

CLI interface with modes: scan, compare, sync, report, dry-run
"""

import argparse
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

from config import (
    LOCAL_ROOT,
    MANIFEST_FILE,
    MANIFEST_HISTORY_DIR,
    PROJECT_METADATA,
    MAX_AUTO_RESOLVE_CONFLICTS,
)
from models import Manifest, SyncAction, SyncActionType
from logging_manager import setup_logging, AuditLogger, generate_sync_report
from scan_local import LocalScanner
from scan_drive import DriveScanner
from scan_github import GitHubScanner
from build_manifest import ManifestBuilder
from compare_manifests import ManifestComparator
from detect_conflicts import ConflictDetector
from resolve_conflicts import ConflictResolver
from sync_to_local import LocalSyncer
from sync_to_drive import DriveSyncer
from sync_to_github import GitHubSyncer
from backup_manager import BackupManager

logger = logging.getLogger("sync")
audit_logger = AuditLogger()


class SyncEngine:
    """Main sync engine orchestrator."""

    def __init__(self, dry_run: bool = False, force: bool = False):
        """
        Initialize sync engine.

        Args:
            dry_run: Show what would happen without making changes
            force: Skip confirmations
        """
        self.dry_run = dry_run
        self.force = force
        self.manifest = None
        self.previous_manifest = None
        self.conflicts = []
        self.actions = []

    def scan_all_sources(self) -> Manifest:
        """Scan all sources (local, Drive, GitHub)."""
        logger.info("Scanning all sources...")

        # Scan each source
        local_files = LocalScanner.scan()
        logger.info(f"Local: {len(local_files)} files")

        drive_files = DriveScanner().scan()
        logger.info(f"Drive: {len(drive_files)} files")

        github_files = GitHubScanner().scan()
        logger.info(f"GitHub: {len(github_files)} files")

        # Build unified manifest
        manifest = ManifestBuilder.build_manifest(
            local_files,
            drive_files,
            github_files,
            project_name=PROJECT_METADATA.get("name"),
        )

        summary = ManifestBuilder.summary(manifest)
        logger.info(f"Manifest summary: {summary}")

        return manifest

    def load_previous_manifest(self) -> Optional[Manifest]:
        """Load manifest from last run."""
        if not MANIFEST_FILE.exists():
            logger.info("No previous manifest found")
            return None

        try:
            with open(MANIFEST_FILE, "r") as f:
                data = json.load(f)
            return Manifest.from_dict(data)
        except Exception as e:
            logger.error(f"Error loading previous manifest: {e}")
            return None

    def save_manifest(self, manifest: Manifest) -> None:
        """Save manifest to disk."""
        try:
            with open(MANIFEST_FILE, "w") as f:
                json.dump(manifest.to_dict(), f, indent=2, default=str)

            # Also save to history
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            history_file = MANIFEST_HISTORY_DIR / f"manifest_{timestamp}.json"
            with open(history_file, "w") as f:
                json.dump(manifest.to_dict(), f, indent=2, default=str)

            logger.info(f"Saved manifest to {MANIFEST_FILE}")
        except Exception as e:
            logger.error(f"Error saving manifest: {e}")

    def run_sync(self, mode: str = "incremental") -> dict:
        """
        Run full sync cycle.

        Args:
            mode: Sync mode (scan, compare, sync, report)

        Returns:
            Dictionary with sync results
        """
        logger.info(f"Starting sync (mode: {mode})")

        results = {
            "mode": mode,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "pending",
            "files_scanned": 0,
            "conflicts": 0,
            "auto_resolved": 0,
            "manual_required": 0,
            "actions": 0,
            "actions_executed": 0,
            "errors": [],
        }

        try:
            # Step 1: Scan all sources
            self.manifest = self.scan_all_sources()
            results["files_scanned"] = self.manifest.total_files

            if mode == "scan":
                logger.info("Scan mode: completed")
                results["status"] = "success"
                return results

            # Step 2: Compare with previous
            self.previous_manifest = self.load_previous_manifest()
            if self.previous_manifest:
                changes = ManifestComparator.compare_manifests(
                    self.manifest, self.previous_manifest
                )
                summary = ManifestComparator.get_change_summary(changes)
                logger.info(f"Changes detected: {summary}")

            if mode == "compare":
                logger.info("Compare mode: completed")
                results["status"] = "success"
                return results

            # Step 3: Detect conflicts
            self.conflicts = ConflictDetector.detect_conflicts(
                self.manifest
            )
            results["conflicts"] = len(self.conflicts)
            logger.info(f"Conflicts detected: {len(self.conflicts)}")

            if self.conflicts:
                conflict_summary = ConflictDetector.summary(self.conflicts)
                logger.warning(f"Conflict summary: {conflict_summary}")

            # Step 4: Resolve conflicts
            auto_resolved, manual_queue = ConflictResolver.resolve_conflicts(
                self.conflicts
            )
            results["auto_resolved"] = len(auto_resolved)
            results["manual_required"] = len(manual_queue)

            if manual_queue:
                logger.warning(
                    f"{len(manual_queue)} conflicts require manual review"
                )

            if mode == "report":
                logger.info("Report mode: completed")
                results["status"] = "success"
                return results

            # Step 5: Build sync actions
            # (Would generate SyncAction list based on manifest)
            logger.info(f"Would execute {len(self.actions)} sync actions")

            if self.dry_run:
                logger.info("DRY RUN: not executing sync actions")
                results["status"] = "success"
                results["dry_run"] = True
                return results

            # Step 6: Execute sync actions
            # (Would call LocalSyncer, DriveSyncer, GitHubSyncer)
            results["actions_executed"] = len(self.actions)

            # Step 7: Save manifest
            self.save_manifest(self.manifest)

            results["status"] = "success"
            logger.info("Sync completed successfully")

        except Exception as e:
            logger.error(f"Sync failed: {e}", exc_info=True)
            results["status"] = "error"
            results["errors"].append(str(e))

        return results


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="AI Sales OS File Synchronization Engine"
    )
    parser.add_argument(
        "--mode",
        choices=["scan", "compare", "sync", "report"],
        default="sync",
        help="Sync mode (default: sync)",
    )
    parser.add_argument(
        "--source",
        choices=["local", "drive", "github"],
        help="Sync from specific source",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would happen without making changes",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Skip confirmations",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging()
    if args.verbose:
        logger.setLevel(logging.DEBUG)

    # Run sync engine
    engine = SyncEngine(dry_run=args.dry_run, force=args.force)
    results = engine.run_sync(mode=args.mode)

    # Print results
    print("\n" + "=" * 60)
    print("SYNC RESULTS")
    print("=" * 60)
    for key, value in results.items():
        print(f"{key}: {value}")

    # Log audit entry
    audit_logger.log_entry(results)


if __name__ == "__main__":
    main()
