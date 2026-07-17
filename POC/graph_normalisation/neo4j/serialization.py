"""Serialization helpers for Neo4j property-safe values."""
from __future__ import annotations

import json
from typing import Any

from entities.models import CanonicalEntity, EntitySource
from shared.models import Relationship


def entity_properties(entity: CanonicalEntity) -> dict[str, Any]:
    """Convert a canonical entity to Neo4j-safe properties."""
    sources = [source_properties(source) for source in entity.sources]
    return {
        "id": entity.id,
        "canonical_id": entity.id,
        "type": entity.type,
        "aliases": list(entity.aliases),
        "confidence": entity.confidence,
        "repository": _unique(s.get("repository") for s in sources),
        "module": _unique(s.get("module") for s in sources),
        "document": _unique(s.get("document") for s in sources),
        "file_path": _unique(s.get("file_path") for s in sources),
        "version_tag": _unique(s.get("version_tag") for s in sources),
        "source_parser": _unique(s.get("source_parser") for s in sources),
        "provenance": json.dumps(sources, sort_keys=True),
        "properties": json.dumps(entity.properties, sort_keys=True, default=str),
    }


def relationship_properties(rel: Relationship) -> dict[str, Any]:
    """Convert a normalized relationship to Neo4j-safe properties."""
    props = dict(rel.properties)
    props.update({"id": str(rel.id), "type": rel.type, "confidence": rel.confidence})
    return {key: _safe_value(value) for key, value in props.items()}


def source_properties(source: EntitySource) -> dict[str, Any]:
    return {
        "source_parser": source.source_parser,
        "original_name": source.original_name,
        "repository": source.repository,
        "module": source.module,
        "document": source.document,
        "file_path": source.file_path,
        "version_tag": source.version_tag,
        "confidence": source.confidence,
        "entity_id": str(source.entity_ref.id) if source.entity_ref else None,
    }


def _unique(values: Any) -> list[str]:
    return sorted({str(value) for value in values if value is not None and str(value).strip()})


def _safe_value(value: Any) -> Any:
    """Return a value compatible with Neo4j property types."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, list) and all(isinstance(v, (str, int, float, bool)) for v in value):
        return value
    return json.dumps(value, sort_keys=True, default=str)