"""
File classification engine for AI Sales OS sync.

Classifies files by:
- Extension
- Filename patterns
- Relative path
- Content inspection (for edge cases)

Determines:
- File category (code, documentation, presentation, etc.)
- Source of truth (which system owns authoritative copy)
- Sync rules (should sync to github, drive, local)
"""

import re
import mimetypes
from pathlib import Path
from typing import Tuple, Optional
from config import (
    EXTENSION_CATEGORIES,
    SOURCE_OF_TRUTH_PRIORITY,
    SYNC_TO_GITHUB,
    SYNC_TO_DRIVE,
    SYNC_TO_LOCAL,
)


class FileClassifier:
    """Classifies files and determines sync rules."""

    SECRET_PATTERNS = [
        r"^\.env",
        r"_secret",
        r"_private",
        r"credentials",
        r"\.key$",
        r"\.pem$",
        r"\.p12$",
        r"api[_-]?key",
        r"access[_-]?token",
        r"oauth[_-]?token",
        r"password",
    ]

    BINARY_EXTENSIONS = {
        ".pdf",
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".webp",
        ".svg",
        ".ico",
        ".mp4",
        ".mov",
        ".avi",
        ".mp3",
        ".wav",
        ".m4a",
        ".zip",
        ".tar",
        ".gz",
        ".rar",
        ".7z",
        ".exe",
        ".dll",
        ".so",
        ".bin",
        ".pyc",
        ".o",
        ".a",
        ".jar",
        ".class",
        ".whl",
        ".xlsx",
        ".xls",
        ".docx",
        ".doc",
        ".pptx",
        ".ppt",
        ".odt",
        ".ods",
        ".odp",
        ".sqlite",
        ".db",
    }

    @classmethod
    def is_secret(cls, filename: str) -> bool:
        """Check if file contains secrets."""
        filename_lower = filename.lower()
        for pattern in cls.SECRET_PATTERNS:
            if re.search(pattern, filename_lower):
                return True
        return False

    @classmethod
    def is_binary(cls, extension: str) -> bool:
        """Check if file is binary based on extension."""
        return extension.lower() in cls.BINARY_EXTENSIONS

    @classmethod
    def classify_file(
        cls, filename: str, extension: str, relative_path: str
    ) -> Tuple[str, Optional[str]]:
        """
        Classify a file and determine its source of truth.

        Returns:
            (classification, source_of_truth)
        """
        # Check for secrets first
        if cls.is_secret(filename):
            return "secret", "local"

        # Normalize extension
        ext = extension.lower() if extension else ""
        if not ext.startswith("."):
            ext = f".{ext}"

        # Get category from extension
        category = EXTENSION_CATEGORIES.get(ext, "unknown")

        # Determine source of truth
        source_of_truth = None
        if category in SOURCE_OF_TRUTH_PRIORITY:
            sources = SOURCE_OF_TRUTH_PRIORITY[category]
            source_of_truth = sources[0] if sources else None

        return category, source_of_truth

    @classmethod
    def get_category(cls, extension: str) -> str:
        """Get file category from extension."""
        ext = extension.lower() if extension else ""
        if not ext.startswith("."):
            ext = f".{ext}"
        return EXTENSION_CATEGORIES.get(ext, "unknown")

    @classmethod
    def should_sync_to_github(cls, classification: str) -> bool:
        """Check if category should sync to GitHub."""
        return classification in SYNC_TO_GITHUB

    @classmethod
    def should_sync_to_drive(cls, classification: str) -> bool:
        """Check if category should sync to Google Drive."""
        return classification in SYNC_TO_DRIVE

    @classmethod
    def should_sync_to_local(cls, classification: str) -> bool:
        """Check if category should sync to local."""
        return classification in SYNC_TO_LOCAL

    @classmethod
    def get_sync_targets(cls, classification: str) -> list:
        """Get all targets where file should sync."""
        targets = []
        if cls.should_sync_to_github(classification):
            targets.append("github")
        if cls.should_sync_to_drive(classification):
            targets.append("drive")
        if cls.should_sync_to_local(classification):
            targets.append("local")
        return targets

    @classmethod
    def get_mime_type(cls, filename: str) -> Optional[str]:
        """Get MIME type for file."""
        mime_type, _ = mimetypes.guess_type(filename)
        return mime_type

    @classmethod
    def infer_from_content(
        cls, content: bytes, filename: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Attempt to infer file type from content.

        Returns:
            (is_binary, inferred_type)
        """
        # Check for common binary signatures
        if content.startswith(b"\x89PNG"):
            return True, "image/png"
        if content.startswith(b"\xff\xd8\xff"):
            return True, "image/jpeg"
        if content.startswith(b"GIF8"):
            return True, "image/gif"
        if content.startswith(b"PK\x03\x04"):
            return True, "application/zip"
        if content.startswith(b"%PDF"):
            return True, "application/pdf"
        if content.startswith(b"\x1f\x8b"):
            return True, "application/gzip"

        # Check for null bytes (indicator of binary)
        if b"\x00" in content[:8192]:
            return True, None

        return False, "text/plain"
