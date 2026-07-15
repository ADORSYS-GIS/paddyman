"""Domain model for an extracted or discovered entity.

An Entity is the atomic unit of knowledge produced by a parser.  It carries a
stable identifier, a semantic type, a human-readable name, the source it was
extracted from, and an open-ended properties bag for type-specific attributes.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID, uuid4


@dataclass
class Entity:
    """An extracted or discovered domain entity.

    Args:
        type:       Semantic type label (e.g. ``"Endpoint"``, ``"Schema"``).
        name:       Human-readable name of the entity.
        source:     Identifier of the source this entity was extracted from.
        id:         Stable unique identifier; auto-generated when omitted.
        properties: Open-ended key/value attributes specific to this type.
    """

    type: str
    name: str
    source: str
    id: UUID = field(default_factory=uuid4)
    properties: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.type.strip():
            raise ValueError("Entity.type must not be empty")
        if not self.name.strip():
            raise ValueError("Entity.name must not be empty")
        if not self.source.strip():
            raise ValueError("Entity.source must not be empty")
