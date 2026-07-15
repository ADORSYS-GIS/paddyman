"""Domain model for a directed relationship between two entities.

Relationships are first-class citizens in the knowledge graph.  Each
relationship carries the IDs of its source and target entities, a semantic
type label, an optional properties bag, and a confidence score reflecting
extraction certainty.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID, uuid4


@dataclass
class Relationship:
    """A directed relationship between two entities.

    Args:
        source_entity_id: UUID of the originating entity.
        target_entity_id: UUID of the destination entity.
        type:             Semantic relationship label (e.g. ``"USES"``, ``"EXTENDS"``).
        id:               Stable unique identifier; auto-generated when omitted.
        properties:       Open-ended key/value attributes for this relationship.
        confidence:       Extraction confidence in the range ``[0.0, 1.0]``.
    """

    source_entity_id: UUID
    target_entity_id: UUID
    type: str
    id: UUID = field(default_factory=uuid4)
    properties: dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0

    def __post_init__(self) -> None:
        if not self.type.strip():
            raise ValueError("Relationship.type must not be empty")
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError(
                f"Relationship.confidence must be in [0.0, 1.0], got {self.confidence}"
            )
