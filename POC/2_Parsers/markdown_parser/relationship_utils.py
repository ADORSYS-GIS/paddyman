"""Relationship utility functions.

Common utilities for creating and managing relationships between entities.
"""
from __future__ import annotations

from typing import Any
from uuid import uuid4


def create_relationship(
    source_id: str,
    target_id: str,
    rel_type: str,
    properties: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create a relationship dict.

    Args:
        source_id:  Source entity ID.
        target_id:  Target entity ID.
        rel_type:   Relationship type.
        properties: Optional relationship properties.

    Returns:
        Relationship dict.
    """
    return {
        "id": str(uuid4()),
        "source_entity_id": source_id,
        "target_entity_id": target_id,
        "type": rel_type,
        "properties": properties or {},
        "confidence": 1.0,
    }


def is_in_range(line: int, start: int, end: int) -> bool:
    """Check if a line number is within a range (inclusive).

    Args:
        line:  Line number to check.
        start: Range start (inclusive).
        end:   Range end (inclusive).

    Returns:
        True if line is in range.
    """
    return start <= line <= end
