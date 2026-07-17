"""Build Operation/Tag relationships for OpenAPI entities."""
from __future__ import annotations

from typing import Any
from uuid import uuid4


def build_operation_relationships(entities: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Build IMPLEMENTS_OPERATION and TAGGED_AS relationships."""
    endpoints = [entity for entity in entities if entity.get("type") == "Endpoint"]
    operations = [entity for entity in entities if entity.get("type") == "Operation"]
    tags = [entity for entity in entities if entity.get("type") == "Tag"]

    operation_index = {
        entity.get("match_key"): entity.get("id")
        for entity in operations
        if entity.get("match_key") and entity.get("id")
    }
    tag_index = {
        entity.get("name"): entity.get("id")
        for entity in tags
        if entity.get("name") and entity.get("id")
    }

    relationships: list[dict[str, Any]] = []
    relationships.extend(_endpoint_operation_relationships(endpoints, operation_index))
    relationships.extend(_operation_tag_relationships(operations, tag_index))
    return relationships


def _endpoint_operation_relationships(
    endpoints: list[dict[str, Any]],
    operation_index: dict[str, str],
) -> list[dict[str, Any]]:
    relationships: list[dict[str, Any]] = []
    for endpoint in endpoints:
        endpoint_id = endpoint.get("id")
        op_key = endpoint.get("operation_match_key")
        op_id = operation_index.get(op_key) if isinstance(op_key, str) else None
        if not endpoint_id or not op_id:
            continue
        relationships.append({
            "id": str(uuid4()),
            "source_entity_id": endpoint_id,
            "target_entity_id": op_id,
            "type": "IMPLEMENTS_OPERATION",
            "properties": {"method": endpoint.get("method"), "path": endpoint.get("path")},
            "confidence": 1.0,
        })
    return relationships


def _operation_tag_relationships(
    operations: list[dict[str, Any]],
    tag_index: dict[str, str],
) -> list[dict[str, Any]]:
    relationships: list[dict[str, Any]] = []
    for operation in operations:
        operation_id = operation.get("id")
        op_props = operation.get("properties")
        tags = op_props.get("tags") if isinstance(op_props, dict) else None
        if not operation_id or not isinstance(tags, list):
            continue
        for tag in tags:
            tag_id = tag_index.get(tag) if isinstance(tag, str) else None
            if not tag_id:
                continue
            relationships.append({
                "id": str(uuid4()),
                "source_entity_id": operation_id,
                "target_entity_id": tag_id,
                "type": "TAGGED_AS",
                "properties": {"tag_name": tag},
                "confidence": 1.0,
            })
    return relationships