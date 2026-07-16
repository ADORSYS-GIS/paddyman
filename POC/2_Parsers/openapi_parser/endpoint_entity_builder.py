"""Build normalized endpoint and parameter entity dicts.

Pure transformation - converts EndpointMetadata and ParameterMetadata
records into flat entity dictionaries.
"""
from __future__ import annotations

from typing import Any
from uuid import uuid4

from openapi_parser.models import EndpointMetadata, ParameterMetadata
from openapi_parser.request_body_entity_builder import build_request_body_match_key
from openapi_parser.response_entity_builder import build_response_match_key


def build_endpoint_entity(endpoint: EndpointMetadata) -> dict[str, Any]:
    """Convert an EndpointMetadata record to a normalized entity dict."""
    request_body_ref: str | None = None
    request_body_required = False
    if isinstance(endpoint.request_body, dict):
        request_body_ref = endpoint.request_body.get("$ref") or None
        request_body_required = bool(endpoint.request_body.get("required", False))
    request_body_match_key = build_request_body_match_key(endpoint.request_body)
    
    response_refs: dict[str, str] = {}
    response_match_keys: dict[str, str] = {}
    if isinstance(endpoint.responses, dict):
        for status_code, response_def in endpoint.responses.items():
            if isinstance(response_def, dict):
                ref = response_def.get("$ref")
                if ref:
                    response_refs[str(status_code)] = ref
                match_key = build_response_match_key(response_def, str(status_code))
                if isinstance(match_key, str):
                    response_match_keys[str(status_code)] = match_key
    
    return {
        "id": str(uuid4()),
        "type": "Endpoint",
        "path": endpoint.path,
        "method": endpoint.method,
        "parameters": [_parameter_to_dict(p) for p in endpoint.parameters],
        "request_body_ref": request_body_ref,
        "request_body_match_key": request_body_match_key,
        "request_body_required": request_body_required,
        "response_refs": response_refs,
        "response_match_keys": response_match_keys,
        "security_requirements": [],
        "source_file": endpoint.spec_source,
        "api_title": endpoint.api_title,
    }


def _parameter_to_dict(param: ParameterMetadata) -> dict[str, Any]:
    """Convert ParameterMetadata to dict for inline parameters."""
    return {
        "name": param.name,
        "location": param.location,
        "required": param.required,
        "description": param.description,
        "schema_type": param.schema_type,
        "schema_ref": param.schema_ref,
        "format": param.format,
        "deprecated": param.deprecated,
        "example": param.example,
    }


def build_parameter_entity(param: ParameterMetadata) -> dict[str, Any]:
    """Convert a ParameterMetadata record to a normalized entity dict."""
    return {
        "id": str(uuid4()),
        "type": "Parameter",
        "name": param.name,
        "in": param.location,
        "required": param.required,
        "schema_type": param.schema_type,
        "description": param.description,
        "enum_values": param.enum_values,
        "format": param.format,
        "deprecated": param.deprecated,
        "example": param.example,
        "source_file": param.spec_source,
    }
