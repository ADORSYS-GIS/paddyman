"""Serialization helpers for extraction output artifacts."""
from __future__ import annotations

from typing import Any


def entity_dict(entity: Any) -> dict[str, Any]:
    return {
        "type": getattr(entity, "type", ""),
        "name": getattr(entity, "name", ""),
        "source": getattr(entity, "source", ""),
        "properties": getattr(entity, "properties", {}),
    }


def relationship_dict(rel: Any) -> dict[str, Any]:
    return {
        "type": str(getattr(rel, "type", "")),
        "confidence": getattr(rel, "confidence", None),
        "source_entity_id": str(getattr(rel, "source_entity_id", "")),
        "target_entity_id": str(getattr(rel, "target_entity_id", "")),
    }


def triple_dict(triple: Any) -> dict[str, Any]:
    if isinstance(triple, dict):
        return triple
    return {
        "subject": getattr(triple, "subject", ""),
        "predicate": getattr(triple, "predicate", ""),
        "object": getattr(triple, "object_name", ""),
        "confidence": getattr(triple, "confidence", None),
    }


def embedding_dict(embedding: Any, include_vector: bool) -> dict[str, Any]:
    raw_type = getattr(embedding, "input_type", "")
    input_type = raw_type.value if hasattr(raw_type, "value") else str(raw_type)
    data: dict[str, Any] = {
        "entity": getattr(embedding, "entity", ""),
        "input_type": input_type,
        "dimension": len(getattr(embedding, "vector", [])),
    }
    if include_vector:
        data["vector"] = getattr(embedding, "vector", [])
    return data