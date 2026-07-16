"""Relationship extractors for Response entities."""
from __future__ import annotations

from typing import Any
from uuid import uuid4

from openapi_parser.relationship_builder import extract_schema_name_from_ref


def endpoint_response_relationships(
    endpoints: list[dict[str, Any]],
    response_index: dict[str, str],
) -> list[dict[str, Any]]:
    """Build HAS_RESPONSE relationships from endpoints to response entities."""
    relationships: list[dict[str, Any]] = []
    for endpoint in endpoints:
        endpoint_id = endpoint.get("id")
        response_keys = endpoint.get("response_match_keys")
        if not endpoint_id or not isinstance(response_keys, dict):
            continue
        for status_code, match_key in response_keys.items():
            if not isinstance(match_key, str):
                continue
            response_id = response_index.get(match_key)
            if not response_id:
                continue
            relationships.append({
                "id": str(uuid4()),
                "source_entity_id": endpoint_id,
                "target_entity_id": response_id,
                "type": "HAS_RESPONSE",
                "properties": {
                    "endpoint_path": endpoint.get("path"),
                    "endpoint_method": endpoint.get("method"),
                    "status_code": str(status_code),
                },
                "confidence": 1.0,
            })
    return relationships


def response_schema_relationships(
    responses: list[dict[str, Any]],
    schema_index: dict[str, str],
) -> list[dict[str, Any]]:
    """Build USES_SCHEMA relationships from responses to schemas."""
    relationships: list[dict[str, Any]] = []
    for response in responses:
        response_id = response.get("id")
        schema_refs = response.get("schema_refs")
        if not response_id or not isinstance(schema_refs, dict):
            continue
        for content_type, schema_ref in schema_refs.items():
            if not isinstance(schema_ref, str):
                continue
            schema_name = extract_schema_name_from_ref(schema_ref)
            schema_id = schema_index.get(schema_name) if schema_name else None
            if not schema_id:
                continue
            relationships.append({
                "id": str(uuid4()),
                "source_entity_id": response_id,
                "target_entity_id": schema_id,
                "type": "USES_SCHEMA",
                "properties": {"content_type": str(content_type), "schema_name": schema_name},
                "confidence": 1.0,
            })
    return relationships