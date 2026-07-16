"""Build DEFINES relationships from each API entity to all entities it owns.

Each API entity owns every entity extracted from the same specification file,
identified by matching `source_file` values.  Entities that store their
source_file inside a nested `properties` dict (e.g. Operation) are also
handled transparently.
"""
from __future__ import annotations

from typing import Any
from uuid import uuid4

# Entity types linked from API via DEFINES
_DEFINES_TYPES = frozenset({
    "Endpoint",
    "Schema",
    "DTO",
    "Enum",
    "SecurityScheme",
    "RequestBody",
    "Response",
    "Parameter",
    "Operation",
})


def _source_file(entity: dict[str, Any]) -> str | None:
    """Extract source_file from top-level or nested properties dict."""
    sf = entity.get("source_file")
    if sf:
        return str(sf)
    props = entity.get("properties")
    if isinstance(props, dict):
        sf = props.get("source_file")
        if sf:
            return str(sf)
    return None


class ApiRelationshipBuilder:
    """Build DEFINES relationships from API entities to their owned entities."""

    def build(self, entities: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Return DEFINES relationships for all API entities in *entities*."""
        api_by_source: dict[str, dict[str, Any]] = {}
        for entity in entities:
            if entity.get("type") == "API":
                sf = _source_file(entity)
                if sf:
                    api_by_source[sf] = entity

        if not api_by_source:
            return []

        relationships: list[dict[str, Any]] = []
        for entity in entities:
            entity_type = entity.get("type")
            if entity_type not in _DEFINES_TYPES:
                continue
            entity_id = entity.get("id")
            if not entity_id:
                continue
            sf = _source_file(entity)
            if not sf:
                continue
            api = api_by_source.get(sf)
            if not api:
                continue
            relationships.append({
                "id": str(uuid4()),
                "source_entity_id": api["id"],
                "target_entity_id": entity_id,
                "type": "DEFINES",
                "properties": {
                    "entity_type": entity_type,
                    "api_title": api.get("name"),
                },
                "confidence": 1.0,
            })
        return relationships
