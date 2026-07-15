"""Build normalized endpoint and parameter entity dicts.

Pure transformation - converts EndpointMetadata and ParameterMetadata
records into flat entity dictionaries.
"""
from __future__ import annotations

from typing import Any
from uuid import uuid4

from openapi_parser.models import EndpointMetadata, ParameterMetadata


def build_endpoint_entity(endpoint: EndpointMetadata) -> dict[str, Any]:
    """Convert an EndpointMetadata record to a normalized entity dict."""
    request_body_ref: str | None = None
    if isinstance(endpoint.request_body, dict):
        request_body_ref = endpoint.request_body.get("$ref") or None
    
    response_refs: dict[str, str] = {}
    if isinstance(endpoint.responses, dict):
        for status_code, response_def in endpoint.responses.items():
            if isinstance(response_def, dict):
                ref = response_def.get("$ref")
                if ref:
                    response_refs[str(status_code)] = ref
    
    return {
        "id": str(uuid4()),
        "type": "Endpoint",
        "path": endpoint.path,
        "method": endpoint.method,
        "operation_id": endpoint.operation_id,
        "summary": endpoint.summary,
        "description": endpoint.description,
        "tags": endpoint.tags,
        "parameters": [_parameter_to_dict(p) for p in endpoint.parameters],
        "request_body": endpoint.request_body,
        "request_body_ref": request_body_ref,
        "responses": endpoint.responses,
        "response_refs": response_refs,
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
