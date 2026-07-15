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
