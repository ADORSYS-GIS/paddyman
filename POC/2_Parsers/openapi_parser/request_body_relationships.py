"""Relationship extractors for RequestBody entities."""
from __future__ import annotations

from typing import Any
from uuid import uuid4

from openapi_parser.relationship_builder import extract_schema_name_from_ref


def endpoint_request_body_relationships(
    endpoints: list[dict[str, Any]],
    request_body_index: dict[str, str],
) -> list[dict[str, Any]]:
    """Build HAS_REQUEST_BODY relationships from endpoints to request bodies."""
    relationships: list[dict[str, Any]] = []
    for endpoint in endpoints:
        endpoint_id = endpoint.get("id")
        match_key = endpoint.get("request_body_match_key")
        if not endpoint_id or not isinstance(match_key, str):
            continue
        request_body_id = request_body_index.get(match_key)
        if not request_body_id:
            continue
        relationships.append({
            "id": str(uuid4()),
            "source_entity_id": endpoint_id,
            "target_entity_id": request_body_id,
            "type": "HAS_REQUEST_BODY",
            "properties": {
                "endpoint_path": endpoint.get("path"),
                "endpoint_method": endpoint.get("method"),
                "required": bool(endpoint.get("request_body_required", False)),
            },
            "confidence": 1.0,
        })
    return relationships


def request_body_schema_relationships(
    request_bodies: list[dict[str, Any]],
    schema_index: dict[str, str],
) -> list[dict[str, Any]]:
    """Build USES_SCHEMA relationships from request bodies to schema entities."""
    relationships: list[dict[str, Any]] = []
    for request_body in request_bodies:
        request_body_id = request_body.get("id")
        schema_refs = request_body.get("schema_refs")
        if not request_body_id or not isinstance(schema_refs, dict):
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
                "source_entity_id": request_body_id,
                "target_entity_id": schema_id,
                "type": "USES_SCHEMA",
                "properties": {
                    "content_type": str(content_type),
                    "schema_name": schema_name,
                },
                "confidence": 1.0,
            })
    return relationships