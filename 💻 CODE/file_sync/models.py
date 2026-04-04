"""
Data models for AI Sales OS file synchronization engine.

Defines dataclasses for:
- FileRecord: Individual file state across sources
- Manifest: Collection of all files with metadata
- SyncAction: Sync operation to be performed
- ConflictRecord: File conflicts requiring resolution
- AuditEntry: Immutable audit trail entry
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
import hashlib
import json


class FileType(Enum):
    """Enumeration of file types."""
    FILE = "file"
    DIRECTORY = "directory"
    SYMLINK = "symlink"


class SyncActionType(Enum):
    """Types of sync actions."""
    PUSH = "push"
    PULL = "pull"
    COPY = "copy"
    DELETE = "delete"
    MOVE = "move"
    CONFLICT = "conflict"
    SKIP = "skip"


class ConflictType(Enum):
    """Types of conflicts."""
    TEXT_CONFLICT = "text_conflict"
    BINARY_CONFLICT = "binary_conflict"
    DELETE_CONFLICT = "delete_conflict"
    TRIPLE_CONFLICT = "triple_conflict"
    DUPLICATE = "duplicate"
    PERMISSION_CONFLICT = "permission_conflict"


class ChangeType(Enum):
    """Types of changes between manifests."""
    NEW = "new"
    MODIFIED = "modified"
    DELETED = "deleted"
    MOVED = "moved"
    RENAMED = "renamed"
    UNCHANGED = "unchanged"


@dataclass
class SourceState:
    """State of a file in a specific source (local/drive/github)."""
    exists: bool = False
    path: Optional[str] = None
    last_modified: Optional[datetime] = None
    hash: Optional[str] = None
    size: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "exists": self.exists,
            "path": self.path,
            "last_modified": self.last_modified.isoformat() if self.last_modified else None,
            "hash": self.hash,
            "size": self.size,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SourceState":
        """Create from dictionary."""
        if isinstance(data.get("last_modified"), str):
            data["last_modified"] = datetime.fromisoformat(data["last_modified"])
        return cls(**data)


@dataclass
class FileRecord:
    """Record for a single file across all sources."""
    file_id: str  # Deterministic ID (hash of relative_path)
    file_name: str  # Base filename
    relative_path: str  # Path relative to LOCAL_ROOT
    file_type: FileType = FileType.FILE
    extension: str = ""
    classification: str = "unknown"
    source_of_truth: Optional[str] = None
    size_bytes: int = 0
    hash_sha256: Optional[str] = None
    
    # State in each source
    sources: Dict[str, SourceState] = field(default_factory=dict)
    
    # Sync metadata
    status: str = "pending"  # pending, syncing, synced, error, conflict
    sync_decision: Optional[SyncActionType] = None
    conflict_flag: bool = False
    review_required: bool = False
    notes: Optional[str] = None
    last_sync: Optional[datetime] = None

    def __post_init__(self):
        """Initialize default source states if missing."""
        for source in ["local", "drive", "github"]:
            if source not in self.sources:
                self.sources[source] = SourceState()

    def get_latest_source(self) -> Optional[str]:
        """Get the source with the most recent modification."""
        latest_source = None
        latest_time = None
        for source, state in self.sources.items():
            if state.exists and state.last_modified:
                if latest_time is None or state.last_modified > latest_time:
                    latest_source = source
                    latest_time = state.last_modified
        return latest_source

    def has_conflicts(self) -> bool:
        """Check if file has conflicting states across sources."""
        existing_hashes = [
            s.hash for s in self.sources.values()
            if s.exists and s.hash
        ]
        return len(set(existing_hashes)) > 1

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "file_id": self.file_id,
            "file_name": self.file_name,
            "relative_path": self.relative_path,
            "file_type": self.file_type.value,
            "extension": self.extension,
            "classification": self.classification,
            "source_of_truth": self.source_of_truth,
            "size_bytes": self.size_bytes,
            "hash_sha256": self.hash_sha256,
            "sources": {k: v.to_dict() for k, v in self.sources.items()},
            "status": self.status,
            "sync_decision": self.sync_decision.value if self.sync_decision else None,
            "conflict_flag": self.conflict_flag,
            "review_required": self.review_required,
            "notes": self.notes,
            "last_sync": self.last_sync.isoformat() if self.last_sync else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FileRecord":
        """Create from dictionary."""
        data["file_type"] = FileType(data["file_type"])
        if data["sync_decision"]:
            data["sync_decision"] = SyncActionType(data["sync_decision"])
        if isinstance(data.get("last_sync"), str):
            data["last_sync"] = datetime.fromisoformat(data["last_sync"])
        
        sources = {}
        for source, state in data.pop("sources", {}).items():
            sources[source] = SourceState.from_dict(state)
        data["sources"] = sources
        
        return cls(**data)


@dataclass
class Manifest:
    """Manifest containing all files in the sync operation."""
    version: str = "1.0"
    project: str = ""
    generated_at: datetime = field(default_factory=datetime.utcnow)
    total_files: int = 0
    files: Dict[str, FileRecord] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_file(self, file_record: FileRecord) -> None:
        """Add a file record to the manifest."""
        self.files[file_record.relative_path] = file_record
        self.total_files = len(self.files)

    def get_file(self, relative_path: str) -> Optional[FileRecord]:
        """Get a file record by relative path."""
        return self.files.get(relative_path)

    def get_files_by_classification(self, classification: str) -> List[FileRecord]:
        """Get all files of a specific classification."""
        return [f for f in self.files.values() if f.classification == classification]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "version": self.version,
            "project": self.project,
            "generated_at": self.generated_at.isoformat(),
            "total_files": self.total_files,
            "files": {k: v.to_dict() for k, v in self.files.items()},
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Manifest":
        """Create from dictionary."""
        if isinstance(data.get("generated_at"), str):
            data["generated_at"] = datetime.fromisoformat(data["generated_at"])
        
        files = {}
        for path, file_data in data.pop("files", {}).items():
            files[path] = FileRecord.from_dict(file_data)
        data["files"] = files
        
        return cls(**data)


@dataclass
class SyncAction:
    """A sync action to be performed."""
    action_type: SyncActionType
    source: str  # local, drive, or github
    target: str  # local, drive, or github
    file_record: FileRecord
    priority: int = 0
    auto_resolved: bool = False
    reason: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "action_type": self.action_type.value,
            "source": self.source,
            "target": self.target,
            "file_record": self.file_record.to_dict(),
            "priority": self.priority,
            "auto_resolved": self.auto_resolved,
            "reason": self.reason,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class ConflictRecord:
    """A file conflict requiring resolution."""
    file_record: FileRecord
    conflict_type: ConflictType
    sources_involved: List[str]  # e.g., ["local", "drive"]
    resolution: Optional[str] = None
    manual_required: bool = True
    timestamp: datetime = field(default_factory=datetime.utcnow)
    notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "file_record": self.file_record.to_dict(),
            "conflict_type": self.conflict_type.value,
            "sources_involved": self.sources_involved,
            "resolution": self.resolution,
            "manual_required": self.manual_required,
            "timestamp": self.timestamp.isoformat(),
            "notes": self.notes,
        }


@dataclass
class AuditEntry:
    """Immutable audit trail entry."""
    timestamp: datetime
    action: str  # e.g., "push", "pull", "conflict"
    file_path: str
    source: str
    target: str
    change_type: str
    decision: str  # e.g., "auto", "manual", "skipped"
    result: str  # e.g., "success", "failed", "pending"
    conflict: bool = False
    manual_review: bool = False
    hash_before: Optional[str] = None
    hash_after: Optional[str] = None
    user: str = "system"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_json_line(self) -> str:
        """Convert to JSON line for audit trail."""
        data = {
            "timestamp": self.timestamp.isoformat(),
            "action": self.action,
            "file_path": self.file_path,
            "source": self.source,
            "target": self.target,
            "change_type": self.change_type,
            "decision": self.decision,
            "result": self.result,
            "conflict": self.conflict,
            "manual_review": self.manual_review,
            "hash_before": self.hash_before,
            "hash_after": self.hash_after,
            "user": self.user,
            "metadata": self.metadata,
        }
        return json.dumps(data)

    @classmethod
    def from_json_line(cls, line: str) -> "AuditEntry":
        """Create from JSON line."""
        data = json.loads(line)
        if isinstance(data.get("timestamp"), str):
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return cls(**data)
