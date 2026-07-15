"""Additional relationship extractors for OpenAPI entities."""
from __future__ import annotations

import logging
from typing import Any
from uuid import uuid4

from openapi_parser.relationship_builder import extract_schema_name_from_ref

logger = logging.getLogger(__name__)


def _schema_reference_relationships(
    schemas: list[dict[str, Any]], schema_index: dict[str, str]
) -> list[dict[str, Any]]:
    """Extract REFERENCES_SCHEMA relationships between schemas."""
    relationships: list[dict[str, Any]] = []
    
    for schema in schemas:
        schema_id = schema.get("id")
        if not schema_id:
            continue
        
        schema_ref = schema.get("schema_ref")
        if schema_ref:
            target_name = extract_schema_name_from_ref(schema_ref)
            target_id = schema_index.get(target_name) if target_name else None
            if target_id:
                relationships.append({
                    "id": str(uuid4()),
                    "source_entity_id": schema_id,
                    "target_entity_id": target_id,
                    "type": "REFERENCES_SCHEMA",
                    "properties": {"ref_path": schema_ref},
                    "confidence": 1.0
                })
        
        properties = schema.get("properties", {})
        if isinstance(properties, dict):
            for prop_name, prop_def in properties.items():
                if not isinstance(prop_def, dict):
                    continue
                prop_ref = prop_def.get("$ref")
                if prop_ref:
                    target_name = extract_schema_name_from_ref(prop_ref)
                    target_id = schema_index.get(target_name) if target_name else None
                    if target_id:
                        relationships.append({
                            "id": str(uuid4()),
                            "source_entity_id": schema_id,
                            "target_entity_id": target_id,
                            "type": "REFERENCES_SCHEMA",
                            "properties": {"ref_path": prop_ref, "property_name": prop_name},
                            "confidence": 1.0
                        })
    
    return relationships


def _endpoint_schema_relationships(
    endpoints: list[dict[str, Any]], schema_index: dict[str, str]
) -> list[dict[str, Any]]:
    """Extract ACCEPTS and RETURNS relationships from endpoints to schemas."""
    relationships: list[dict[str, Any]] = []
    
    for endpoint in endpoints:
        endpoint_id = endpoint.get("id")
        if not endpoint_id:
            continue
        
        request_ref = endpoint.get("request_body_ref")
        if request_ref:
            schema_name = extract_schema_name_from_ref(request_ref)
            schema_id = schema_index.get(schema_name) if schema_name else None
            if schema_id:
                relationships.append({
                    "id": str(uuid4()),
                    "source_entity_id": endpoint_id,
                    "target_entity_id": schema_id,
                    "type": "ACCEPTS",
                    "properties": {"ref_path": request_ref},
                    "confidence": 1.0
                })
        
        response_refs = endpoint.get("response_refs", {})
        if isinstance(response_refs, dict):
            for status_code, resp_ref in response_refs.items():
                schema_name = extract_schema_name_from_ref(resp_ref)
                schema_id = schema_index.get(schema_name) if schema_name else None
                if schema_id:
                    relationships.append({
                        "id": str(uuid4()),
                        "source_entity_id": endpoint_id,
                        "target_entity_id": schema_id,
                        "type": "RETURNS",
                        "properties": {"status_code": status_code, "ref_path": resp_ref},
                        "confidence": 1.0
                    })
    
    return relationships


def _security_relationships(
    endpoints: list[dict[str, Any]], security_index: dict[str, str]
) -> list[dict[str, Any]]:
    """Extract REQUIRES_SECURITY relationships from endpoints to security schemes."""
    relationships: list[dict[str, Any]] = []
    
    for endpoint in endpoints:
        endpoint_id = endpoint.get("id")
        if not endpoint_id:
            continue
        
        security = endpoint.get("security", [])
        if not isinstance(security, list):
            continue
        
        for req in security:
            if not isinstance(req, dict):
                continue
            for scheme_name in req.keys():
                scheme_id = security_index.get(scheme_name)
                if scheme_id:
                    relationships.append({
                        "id": str(uuid4()),
                        "source_entity_id": endpoint_id,
                        "target_entity_id": scheme_id,
                        "type": "REQUIRES_SECURITY",
                        "properties": {"scheme_name": scheme_name},
                        "confidence": 1.0
                    })
    
    return relationships

