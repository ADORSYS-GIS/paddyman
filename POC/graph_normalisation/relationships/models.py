"""Internal models for relationship normalisation."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class RawRelationship:
    """Source relationship adapted from parser or extractor output."""

    source: str
    target: str
    relationship_type: str
    source_parser: str
    repository: str | None = None
    module: str | None = None
    document: str | None = None
    file_path: str | None = None
    version_tag: str | None = None
    confidence: float = 1.0
    provenance: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.source.strip():
            raise ValueError("RawRelationship.source must not be empty")
        if not self.target.strip():
            raise ValueError("RawRelationship.target must not be empty")
        if not self.relationship_type.strip():
            raise ValueError("RawRelationship.relationship_type must not be empty")
        if not self.source_parser.strip():
            raise ValueError("RawRelationship.source_parser must not be empty")
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError("RawRelationship.confidence must be in [0.0, 1.0]")