"""Build HAS_TYPE relationships from Parameter entities to declared parameter types."""
from __future__ import annotations

from typing import Any

from java_parser.type_parsing_helpers import parse_type_declaration


def _build_type_entity_index(
    all_entities: list[dict[str, Any]],
) -> dict[str, str]:
    """Build index from simple type name to UUID for fast lookup."""
    index: dict[str, str] = {}
    for entity in all_entities:
        if entity.get("type") in ("Class", "Interface", "Enum", "JavaType"):
            name = entity.get("name", "")
            entity_uuid = entity.get("uuid")
            if name and entity_uuid:
                index[name] = entity_uuid
    return index


def _normalize_parameter_type(type_name: str) -> tuple[str, bool]:
    """Normalize parameter type for parsing and detect varargs form."""
    cleaned = type_name.strip()
    is_varargs = cleaned.endswith("...")
    if is_varargs:
        cleaned = f"{cleaned[:-3].strip()}[]"
    return cleaned, is_varargs


def build_parameter_has_type_relationships(
    parameter_entities: list[dict[str, Any]],
    all_entities: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Create HAS_TYPE relationships from parameters to their declared types."""
    type_index = _build_type_entity_index(all_entities)
    relationships: list[dict[str, Any]] = []

    for parameter in parameter_entities:
        if parameter.get("type") != "Parameter":
            continue

        parameter_uuid = parameter.get("uuid")
        parameter_name = parameter.get("name", "")
        parameter_type = parameter.get("parameter_type", "")
        entity_vararg = bool(parameter.get("is_vararg", False))

        if not parameter_uuid or not parameter_type:
            continue

        parse_ready_type, type_vararg = _normalize_parameter_type(parameter_type)
        base_type, is_collection, is_generic, generic_args = parse_type_declaration(
            parse_ready_type
        )
        is_varargs = entity_vararg or type_vararg
        if is_varargs:
            is_collection = True

        target_uuid = type_index.get(base_type)
        display_type = f"{base_type}..." if is_varargs else parameter_type

        rel: dict[str, Any] = {
            "type": "HAS_TYPE",
            "source": parameter_uuid,
            "target": target_uuid or base_type,
            "properties": {
                "parameter_name": parameter_name,
                "type_name": display_type,
                "base_type": base_type,
                "is_collection": is_collection,
                "is_generic": is_generic,
                "is_varargs": is_varargs,
            },
        }

        if generic_args:
            rel["properties"]["generic_arguments"] = generic_args
        if target_uuid is None:
            rel["properties"]["target_resolved"] = False

        relationships.append(rel)

    return relationships
