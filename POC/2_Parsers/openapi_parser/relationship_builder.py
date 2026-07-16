"""Build relationships between OpenAPI entities.

Pure transformation module — converts entity dictionaries into relationship
records for the ``NormalizedJson.relationships`` field.
"""
from __future__ import annotations

import logging
from typing import Any
from uuid import uuid4

logger = logging.getLogger(__name__)


def _import_extractors():
    """Lazy import of relationship extractors."""
    from openapi_parser import relationship_extractors
    return relationship_extractors


def build_openapi_relationships(entities: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Build all relationships between OpenAPI entities."""
    endpoints = [e for e in entities if e.get("type") == "Endpoint"]
    schemas = [e for e in entities if e.get("type") == "Schema"]
    parameters = [e for e in entities if e.get("type") == "Parameter"]
    security_schemes = [e for e in entities if e.get("type") == "SecurityScheme"]
    
    schema_index = _build_schema_index(schemas)
    param_index = _build_parameter_index(parameters)
    security_index = _build_security_index(security_schemes)
    
    relationships: list[dict[str, Any]] = []
    extractors = _import_extractors()
    
    relationships.extend(_endpoint_parameter_relationships(endpoints, param_index))
    relationships.extend(extractors._schema_reference_relationships(schemas, schema_index))
    relationships.extend(extractors._endpoint_schema_relationships(endpoints, schema_index))
    relationships.extend(extractors._security_relationships(endpoints, security_index))
    
    logger.debug("Built %d relationships from %d entities", len(relationships), len(entities))
    return relationships


def extract_schema_name_from_ref(ref: str) -> str | None:
    """Extract schema name from $ref path."""
    if not ref or not isinstance(ref, str):
        return None
    if "#/components/schemas/" in ref:
        return ref.split("#/components/schemas/")[-1]
    if "#/" in ref:
        return ref.split("/")[-1]
    return None


def _build_schema_index(schemas: list[dict[str, Any]]) -> dict[str, str]:
    """Build name-to-entity-id index for schemas."""
    return {s["name"]: s["id"] for s in schemas if s.get("name") and s.get("id")}


def _build_parameter_index(parameters: list[dict[str, Any]]) -> dict[str, str]:
    """Build name-to-entity-id index for parameters."""
    index: dict[str, str] = {}
    for param in parameters:
        name = param.get("name")
        entity_id = param.get("id")
        if name and entity_id:
            location = param.get("in", "")
            index[f"{name}:{location}"] = entity_id
    return index


def _build_security_index(security_schemes: list[dict[str, Any]]) -> dict[str, str]:
    """Build name-to-entity-id index for security schemes."""
    return {s["name"]: s["id"] for s in security_schemes if s.get("name") and s.get("id")}


def _endpoint_parameter_relationships(
    endpoints: list[dict[str, Any]], param_index: dict[str, str]
) -> list[dict[str, Any]]:
    """Extract HAS_PARAMETER relationships from endpoints to parameters."""
    relationships: list[dict[str, Any]] = []
    
    for endpoint in endpoints:
        endpoint_id = endpoint.get("id")
        if not endpoint_id:
            continue
        
        params = endpoint.get("parameters", [])
        if not isinstance(params, list):
            continue
        
        for param in params:
            if not isinstance(param, dict):
                continue
            
            param_name = param.get("name")
            param_location = param.get("location", "")
            if not param_name:
                continue
            
            key = f"{param_name}:{param_location}"
            param_id = param_index.get(key)
            
            if param_id:
                relationships.append({
                    "id": str(uuid4()),
                    "source_entity_id": endpoint_id,
                    "target_entity_id": param_id,
                    "type": "HAS_PARAMETER",
                    "properties": {"parameter_name": param_name, "location": param_location},
                    "confidence": 1.0
                })
    
    return relationships

