"""Build RETURNS relationships from Method entities to their declared return types."""
from __future__ import annotations

from typing import Any
from uuid import NAMESPACE_URL, uuid5

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


def _ensure_void_type_entity(all_entities: list[dict[str, Any]]) -> dict[str, Any]:
    """Return existing singleton void type entity or create a new one."""
    for entity in all_entities:
        if entity.get("type") == "JavaType" and entity.get("name") == "void":
            return entity

    void_entity = {
        "type": "JavaType",
        "name": "void",
        "qualified_name": "void",
        "uuid": str(uuid5(NAMESPACE_URL, "java-type:void")),
        "is_primitive": True,
        "source": "java_parser:synthetic:type:void",
    }
    all_entities.append(void_entity)
    return void_entity


def build_returns_relationships(
    method_entities: list[dict[str, Any]],
    all_entities: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Create RETURNS relationships from methods to their return type entities."""
    relationships: list[dict[str, Any]] = []
    type_index = _build_type_entity_index(all_entities)

    for method_entity in method_entities:
        if method_entity.get("type") != "Method":
            continue

        method_uuid = method_entity.get("uuid")
        method_name = method_entity.get("name", "")
        return_type = method_entity.get("return_type")

        if not method_uuid or not return_type:
            continue

        if return_type == "void":
            void_entity = _ensure_void_type_entity(all_entities)
            relationships.append(
                {
                    "type": "RETURNS",
                    "source": method_uuid,
                    "target": void_entity["uuid"],
                    "properties": {
                        "method_name": method_name,
                        "return_type": "void",
                        "base_type": "void",
                        "is_collection": False,
                        "is_generic": False,
                        "is_void": True,
                    },
                }
            )
            continue

        base_type, is_collection, is_generic, generic_args = parse_type_declaration(
            return_type
        )
        target_uuid = type_index.get(base_type)

        rel: dict[str, Any] = {
            "type": "RETURNS",
            "source": method_uuid,
            "target": target_uuid or base_type,
            "properties": {
                "method_name": method_name,
                "return_type": return_type,
                "base_type": base_type,
                "is_collection": is_collection,
                "is_generic": is_generic,
                "is_void": False,
            },
        }

        if generic_args:
            rel["properties"]["generic_arguments"] = generic_args
        if target_uuid is None:
            rel["properties"]["target_resolved"] = False

        relationships.append(rel)

    return relationships
