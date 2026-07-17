"""Relationship extractors for DTO and Enum entities."""
from __future__ import annotations

from typing import Any
from uuid import uuid4


def dto_property_relationships(dtos: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Build HAS_PROPERTY relationships from DTOs to property schema entities."""
    relationships: list[dict[str, Any]] = []
    for dto in dtos:
        dto_id = dto.get("id")
        props = dto.get("properties")
        if not dto_id or not isinstance(props, dict):
            continue
        links = props.get("property_links")
        if not isinstance(links, list):
            continue
        for link in links:
            if not isinstance(link, dict):
                continue
            target_id = link.get("target_entity_id")
            if not isinstance(target_id, str) or not target_id:
                continue
            relationships.append(
                {
                    "id": str(uuid4()),
                    "source_entity_id": dto_id,
                    "target_entity_id": target_id,
                    "type": "HAS_PROPERTY",
                    "properties": {
                        "property_name": link.get("property_name"),
                        "required": bool(link.get("required", False)),
                        "nullable": bool(link.get("nullable", False)),
                    },
                    "confidence": 1.0,
                }
            )
    return relationships


def enum_value_relationships(enums: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Build HAS_ENUM_VALUE relationships from enums to enum value entities."""
    relationships: list[dict[str, Any]] = []
    for enum in enums:
        enum_id = enum.get("id")
        props = enum.get("properties")
        if not enum_id or not isinstance(props, dict):
            continue
        links = props.get("value_links")
        if not isinstance(links, list):
            continue
        for link in links:
            if not isinstance(link, dict):
                continue
            target_id = link.get("target_entity_id")
            if not isinstance(target_id, str) or not target_id:
                continue
            relationships.append(
                {
                    "id": str(uuid4()),
                    "source_entity_id": enum_id,
                    "target_entity_id": target_id,
                    "type": "HAS_ENUM_VALUE",
                    "properties": {
                        "value": link.get("value"),
                        "position": link.get("position"),
                    },
                    "confidence": 1.0,
                }
            )
    return relationships
