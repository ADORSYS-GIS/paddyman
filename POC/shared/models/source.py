"""Domain model for source metadata.

SourceMetadata describes the origin of extracted information.  It supports
documents, APIs, databases, and external datasets through a typed
:class:`SourceType` enumeration, and carries an open-ended metadata bag for
source-specific attributes.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import UUID, uuid4
from pathlib import Path


class SourceType(str, Enum):
    """Supported ingestion source categories."""

    DOCUMENT = "document"
    API = "api"
    DATABASE = "database"
    EXTERNAL = "external"


@dataclass
class SourceMetadata:
    """Metadata describing the origin of extracted information.

    Args:
        source_id:   Unique identifier for this source (e.g. filename, API path).
        source_type: Category of the ingestion source.
        location:    Resolvable reference — file path, URL, or connection string.
        id:          Internal record identifier; auto-generated when omitted.
        ingested_at: UTC timestamp of ingestion; defaults to now.
        metadata:    Additional source-specific key/value attributes.
    """

    source_id: str
    source_type: SourceType
    location: str
    id: UUID = field(default_factory=uuid4)
    ingested_at: datetime = field(
        default_factory=lambda: datetime.now(tz=timezone.utc)
    )
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.source_id.strip():
            raise ValueError("SourceMetadata.source_id must not be empty")
        if not self.location.strip():
            raise ValueError("SourceMetadata.location must not be empty")
        if not isinstance(self.source_type, SourceType):
            self.source_type = SourceType(self.source_type)
        # Coerce common serialized representations into proper types
        if isinstance(self.id, str):
            try:
                self.id = UUID(self.id)
            except Exception:
                self.id = uuid4()
        if isinstance(self.ingested_at, str):
            s = self.ingested_at
            # fromisoformat doesn't accept trailing Z for UTC
            if s.endswith("Z"):
                s = s[:-1] + "+00:00"
            try:
                self.ingested_at = datetime.fromisoformat(s)
            except Exception:
                self.ingested_at = datetime.now(tz=timezone.utc)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation of this object."""
        return {
            "source_id": self.source_id,
            "source_type": self.source_type.value if isinstance(self.source_type, SourceType) else str(self.source_type),
            "location": self.location,
            "id": str(self.id),
            "ingested_at": self.ingested_at.isoformat(),
            "metadata": dict(self.metadata or {}),
        }

    @classmethod
    def from_parser_metadata(cls, parser_meta: dict[str, Any]) -> "SourceMetadata":
        """Normalize parser-specific metadata into a SourceMetadata instance.

        The function prefers `relative_path` or `file_path` to compute the
        canonical `source_id`. Parser-specific fields are moved into the
        `metadata` bag. The `source_parser` hint is used to infer
        `source_type` when possible.
        """
        meta = dict(parser_meta or {})
        parser_name = meta.get("source_parser") or meta.get("parser")
        mapping: dict[str, SourceType] = {
            "java_parser": SourceType.DOCUMENT,
            "markdown_parser": SourceType.DOCUMENT,
            "openapi_parser": SourceType.API,
        }
        source_type = mapping.get(str(parser_name), SourceType.DOCUMENT)

        relative = meta.get("relative_path") or meta.get("relative")
        file_path = meta.get("file_path") or meta.get("path") or meta.get("file")
        repository = meta.get("repository") or meta.get("repo")

        if relative and repository:
            source_id = f"{repository}:{relative}"
        elif relative:
            source_id = str(relative)
        elif file_path and repository:
            source_id = f"{repository}:{Path(file_path).name}"
        elif file_path:
            source_id = str(file_path)
        elif repository:
            source_id = str(repository)
        else:
            source_id = str(meta.get("source_id") or meta.get("id") or "unknown")

        location = str(file_path or relative or meta.get("location") or "")

        # Build metadata bag: keep parser-specific attributes only
        excluded = {
            "file",
            "path",
            # keep relative_path in metadata so parsers can assert stability
            # "relative_path",
            # "relative",
            "source_parser",
            "parser",
            "source_id",
            "source_type",
            "location",
            "id",
            "ingested_at",
        }
        metadata = {k: v for k, v in meta.items() if k not in excluded}
        if parser_name:
            metadata.setdefault("source_parser", parser_name)

        # Allow parser-provided stable identifiers/timestamps to be respected
        # by callers who want deterministic output (e.g., writers/tests).
        kwargs: dict[str, Any] = dict(
            source_id=source_id,
            source_type=source_type,
            location=location,
            metadata=metadata,
        )
        if "id" in meta and meta.get("id") is not None:
            kwargs["id"] = meta.get("id")
        if "ingested_at" in meta and meta.get("ingested_at") is not None:
            kwargs["ingested_at"] = meta.get("ingested_at")

        return cls(**kwargs)
