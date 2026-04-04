"""
Google Drive scanner for AI Sales OS sync.

Scans Google Drive folder and generates FileRecords.
- Lists files recursively
- Gets file metadata (size, modification time, MD5 hash)
- Handles pagination
- Maps Drive structure to relative paths
"""

import logging
from typing import List, Optional
from datetime import datetime
import pickle
import os

from models import FileRecord, FileType, SourceState
from classify_files import FileClassifier
from config import (
    DRIVE_FOLDER_ID,
    DRIVE_CREDENTIALS_PATH,
    DRIVE_TOKEN_PATH,
    API_TIMEOUT,
    MAX_RETRIES,
)

logger = logging.getLogger(__name__)


class DriveScanner:
    """Scans Google Drive for files to sync."""

    def __init__(self, folder_id: Optional[str] = None):
        """
        Initialize Drive scanner.

        Args:
            folder_id: Google Drive folder ID to scan.
        """
        self.folder_id = folder_id or DRIVE_FOLDER_ID
        self.service = None
        self._authenticate()

    def _authenticate(self) -> None:
        """Authenticate with Google Drive API."""
        try:
            from google.auth.transport.requests import Request
            from google.oauth2.service_account import Credentials
            from googleapiclient.discovery import build

            # For service account (recommended for automation)
            if os.path.exists(DRIVE_CREDENTIALS_PATH):
                credentials = Credentials.from_service_account_file(
                    DRIVE_CREDENTIALS_PATH,
                    scopes=["https://www.googleapis.com/auth/drive"],
                )
            else:
                logger.warning(
                    f"Credentials file not found at {DRIVE_CREDENTIALS_PATH}"
                )
                return

            self.service = build(
                "drive", "v3", credentials=credentials, timeout=API_TIMEOUT
            )
            logger.info("Authenticated with Google Drive API")

        except ImportError:
            logger.error(
                "Google API libraries not installed. "
                "Install with: pip install google-api-python-client"
            )
            self.service = None
        except Exception as e:
            logger.error(f"Failed to authenticate with Google Drive: {e}")
            self.service = None

    def scan_folder(
        self, folder_id: Optional[str] = None, prefix: str = ""
    ) -> List[FileRecord]:
        """
        Recursively scan a Google Drive folder.

        Args:
            folder_id: Folder to scan. Defaults to self.folder_id.
            prefix: Path prefix for relative path calculation.

        Returns:
            List of FileRecord objects.
        """
        if self.service is None:
            logger.error("Drive service not authenticated")
            return []

        if folder_id is None:
            folder_id = self.folder_id

        if not folder_id:
            logger.error("No folder ID specified")
            return []

        files = []
        page_token = None

        try:
            while True:
                # List files in folder
                query = f"'{folder_id}' in parents and trashed=false"
                results = self.service.files().list(
                    q=query,
                    spaces="drive",
                    fields="files(id, name, mimeType, size, modifiedTime, md5Checksum)",
                    pageSize=1000,
                    pageToken=page_token,
                ).execute()

                items = results.get("files", [])

                for item in items:
                    file_id = item["id"]
                    name = item["name"]
                    mime_type = item.get("mimeType", "")
                    size = int(item.get("size", 0))
                    mtime_str = item.get("modifiedTime")
                    file_hash = item.get("md5Checksum", "")

                    # Parse modification time
                    mtime = None
                    if mtime_str:
                        try:
                            mtime = datetime.fromisoformat(
                                mtime_str.replace("Z", "+00:00")
                            )
                        except ValueError:
                            mtime = None

                    # Build relative path
                    if prefix:
                        relative_path = f"{prefix}/{name}"
                    else:
                        relative_path = name

                    # Check if it's a folder
                    if mime_type == "application/vnd.google-apps.folder":
                        # Recursively scan subfolder
                        subfolder_files = self.scan_folder(
                            file_id, relative_path
                        )
                        files.extend(subfolder_files)
                    else:
                        # Classify file
                        extension = ""
                        if "." in name:
                            extension = f".{name.rsplit('.', 1)[1].lower()}"

                        classification, source_of_truth = (
                            FileClassifier.classify_file(
                                name, extension, relative_path
                            )
                        )

                        # Create FileRecord
                        file_record = FileRecord(
                            file_id=file_id,
                            file_name=name,
                            relative_path=relative_path,
                            file_type=FileType.FILE,
                            extension=extension,
                            classification=classification,
                            source_of_truth=source_of_truth,
                            size_bytes=size,
                            hash_sha256=file_hash,
                        )

                        # Set Drive source state
                        file_record.sources["drive"] = SourceState(
                            exists=True,
                            path=relative_path,
                            last_modified=mtime,
                            hash=file_hash,
                            size=size,
                            metadata={
                                "drive_id": file_id,
                                "mime_type": mime_type,
                            },
                        )

                        files.append(file_record)

                page_token = results.get("nextPageToken")
                if not page_token:
                    break

        except Exception as e:
            logger.error(f"Error scanning Google Drive: {e}")

        return files

    def scan(self) -> List[FileRecord]:
        """Convenience method for scanning Google Drive."""
        if not self.folder_id:
            logger.error("No Drive folder ID configured")
            return []

        logger.info(f"Scanning Google Drive folder: {self.folder_id}")
        files = self.scan_folder(self.folder_id)
        logger.info(f"Scanned {len(files)} files from Google Drive")
        return files
