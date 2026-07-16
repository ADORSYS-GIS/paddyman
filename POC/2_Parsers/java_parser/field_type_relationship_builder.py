"""Build HAS_TYPE relationships from Field entities to their declared types."""
from __future__ import annotations

import logging
from typing import Any

from java_parser.type_parsing_helpers import parse_type_declaration

logger = logging.getLogger(__name__)


def _build_type_entity_index(
    type_entities: list[dict[str, Any]],
) -> dict[str, str]:
    """Build index from simple type name to UUID for fast lookup."""
    index: dict[str, str] = {}
    for entity in type_entities:
        if entity.get("type") in ("Class", "Interface", "Enum"):
            name = entity.get("name", "")
            uuid = entity.get("uuid")
            if name and uuid:
                index[name] = uuid
    return index


def build_has_type_relationships(
    field_entities: list[dict[str, Any]],
    all_entities: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Create HAS_TYPE relationships from fields to their declared types.

    Each Field gets a HAS_TYPE relationship to its type entity (if it exists).
    """
    type_entities = [
        e for e in all_entities if e.get("type") in ("Class", "Interface", "Enum")
    ]
    type_index = _build_type_entity_index(type_entities)
    relationships: list[dict[str, Any]] = []

    for field_entity in field_entities:
        if field_entity.get("type") != "Field":
            continue

        field_uuid = field_entity.get("uuid")
        field_type_str = field_entity.get("field_type", "")
        field_name = field_entity.get("name", "")

        if not field_uuid or not field_type_str:
            continue

        base_type, is_collection, is_generic, generic_args = parse_type_declaration(
            field_type_str
        )
        target_uuid = type_index.get(base_type)

        rel: dict[str, Any] = {
            "type": "HAS_TYPE",
            "source": field_uuid,
            "target": target_uuid or base_type,
            "properties": {
                "field_name": field_name,
                "type_name": field_type_str,
                "base_type": base_type,
                "is_collection": is_collection,
                "is_generic": is_generic,
            },
        }

        if generic_args:
            rel["properties"]["generic_arguments"] = generic_args
        if target_uuid is None:
            rel["properties"]["target_resolved"] = False

        relationships.append(rel)

    return relationships

