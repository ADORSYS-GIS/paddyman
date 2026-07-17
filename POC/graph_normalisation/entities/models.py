"""Canonical entity model for the Graph Normalisation stage (Chunk 5.1).

A :class:`CanonicalEntity` is the normalised, source-unified representation
produced from one or more raw :class:`~shared.models.Entity` objects that
refer to the same real-world concept.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from shared.models import Entity


@dataclass
class EntitySource:
    """Provenance record from a single contributing parser or extractor.

    Attributes:
        source_parser:  Parser/extractor identifier (e.g. ``"java_parser"``).
        original_name:  Raw name as it appeared in the source.
        repository:     Repository name, if available.
        module:         Module label, if available.
        document:       Document name, if available.
        file_path:      File path within the repository.
        version_tag:    Version tag (e.g. ``"v1"``).
        confidence:     Extraction confidence in ``[0.0, 1.0]``.
        entity_ref:     Back-reference to the original :class:`~shared.models.Entity`.
    """

    source_parser: str
    original_name: str
    repository: str | None = None
    module: str | None = None
    document: str | None = None
    file_path: str | None = None
    version_tag: str | None = None
    confidence: float = 1.0
    entity_ref: Entity | None = None

    def __post_init__(self) -> None:
        if not self.source_parser.strip():
            raise ValueError("EntitySource.source_parser must not be empty")
        if not self.original_name.strip():
            raise ValueError("EntitySource.original_name must not be empty")
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError(
                f"EntitySource.confidence must be in [0.0, 1.0], got {self.confidence}"
            )


@dataclass
class CanonicalEntity:
    """Normalised entity ready for graph persistence.

    Attributes:
        id:         Deterministic canonical identifier in PascalCase.
        type:       Semantic type label (e.g. ``"domain_entity"``).
        aliases:    All original names that resolved to this entity.
        sources:    Provenance records from every contributing source.
        confidence: Mean confidence across all contributing sources.
        properties: Additional open-ended attributes.
    """

    id: str
    type: str
    aliases: list[str] = field(default_factory=list)
    sources: list[EntitySource] = field(default_factory=list)
    confidence: float = 1.0
    properties: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("CanonicalEntity.id must not be empty")
        if not self.type.strip():
            raise ValueError("CanonicalEntity.type must not be empty")
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError(
                f"CanonicalEntity.confidence must be in [0.0, 1.0], "
                f"got {self.confidence}"
            )

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serialisable representation."""
        return {
            "id": self.id,
            "type": self.type,
            "aliases": list(self.aliases),
            "sources": [
                {
                    "source_parser": s.source_parser,
                    "original_name": s.original_name,
                    "repository": s.repository,
                    "module": s.module,
                    "document": s.document,
                    "file_path": s.file_path,
                    "version_tag": s.version_tag,
                    "confidence": s.confidence,
                    "entity_id": str(s.entity_ref.id) if s.entity_ref else None,
                }
                for s in self.sources
            ],
            "confidence": self.confidence,
            "properties": self.properties,
        }
