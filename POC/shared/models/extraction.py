"""Domain model for the output of an extraction pipeline stage.

ExtractionResult aggregates all entities and relationships discovered during
one extraction pass, together with the source that was processed, a status
indicator, and any errors or warnings that arose during extraction.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from .entity import Entity
from .relationship import Relationship
from .source import SourceMetadata


class ExtractionStatus(str, Enum):
    """Lifecycle status of an extraction run."""

    PENDING = "pending"
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"


@dataclass
class ExtractionResult:
    """Output of a single extraction pipeline stage.

    Args:
        source:        Metadata for the source that was processed.
        id:            Unique result identifier; auto-generated when omitted.
        entities:      Entities extracted from the source.
        relationships: Relationships extracted from the source.
        status:        Terminal status of this extraction run.
        errors:        Unrecoverable error messages encountered.
        warnings:      Recoverable warning messages encountered.
        metadata:      Additional extraction-specific key/value attributes.
    """

    source: SourceMetadata
    id: UUID = field(default_factory=uuid4)
    entities: list[Entity] = field(default_factory=list)
    relationships: list[Relationship] = field(default_factory=list)
    status: ExtractionStatus = ExtractionStatus.PENDING
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def has_errors(self) -> bool:
        """Return ``True`` when any errors were recorded."""
        return bool(self.errors)

    @property
    def entity_count(self) -> int:
        """Return the number of extracted entities."""
        return len(self.entities)

    @property
    def relationship_count(self) -> int:
        """Return the number of extracted relationships."""
        return len(self.relationships)
