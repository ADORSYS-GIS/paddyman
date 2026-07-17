from shared.models.openapi import Endpoint
from openapi_parser.models import EndpointMetadata
from openapi_parser.models import ParameterMetadata
from typing import Any
from uuid import uuid5, NAMESPACE_URL

from openapi_parser.request_body_entity_builder import build_request_body_match_key
from openapi_parser.response_entity_builder import build_response_match_key


def build_endpoint_entity(endpoint: EndpointMetadata) -> dict[str, Any]:
    """Convert an EndpointMetadata record to a normalized entity dict.

    The function uses the canonical `Endpoint` model to derive a stable id
    and provenance, but emits the historical IR dict shape expected by
    downstream code and tests.
    """
    ep_model = Endpoint.create(path=endpoint.path, method=endpoint.method, spec_source=endpoint.spec_source)

    # Compute request/response match keys when inline payloads are present
    rb_match = build_request_body_match_key(endpoint.request_body) if getattr(endpoint, "request_body", None) else None
    response_match_keys: dict[str, str] = {}
    response_refs: dict[str, str] = {}
    if isinstance(getattr(endpoint, "responses", None), dict):
        for status, resp in endpoint.responses.items():
            key = build_response_match_key(resp, str(status))
            if key:
                response_match_keys[str(status)] = key
            if isinstance(resp, dict) and isinstance(resp.get("$ref"), str):
                response_refs[str(status)] = resp.get("$ref")

    # Convert inline parameter metadata to simple dicts expected by tests
    params_list: list[dict[str, Any]] = []
    if isinstance(getattr(endpoint, "parameters", None), list):
        for p in endpoint.parameters:
            try:
                params_list.append({
                    "name": getattr(p, "name", None),
                    "location": getattr(p, "location", None),
                    "required": bool(getattr(p, "required", False)),
                    "description": getattr(p, "description", None),
                    "schema_type": getattr(p, "schema_type", None),
                    "schema_ref": getattr(p, "schema_ref", None),
                    "format": getattr(p, "format", None),
                    "deprecated": bool(getattr(p, "deprecated", False)),
                    "example": getattr(p, "example", None),
                })
            except Exception:
                continue

    result: dict[str, Any] = {
        "id": str(ep_model.id),
        "type": "Endpoint",
        "name": ep_model.name,
        "source": f"openapi_parser:{endpoint.spec_source}:{endpoint.method.upper()}:{endpoint.path}",
        "api_title": getattr(endpoint, "api_title", None),
        "source_file": getattr(endpoint, "spec_source", None),
        "path": getattr(endpoint, "path", None),
        "method": getattr(endpoint, "method", None),
        "parameters": params_list,
        "request_body_ref": (endpoint.request_body.get("$ref") if isinstance(endpoint.request_body, dict) else None),
        "request_body_match_key": rb_match,
        "request_body_required": bool(getattr(endpoint, "request_body", {}).get("required", False)) if isinstance(getattr(endpoint, "request_body", None), dict) else False,
        "response_match_keys": response_match_keys,
        "response_refs": response_refs,
        "provenance": ep_model.provenance.model_dump() if hasattr(ep_model.provenance, "model_dump") else (ep_model.provenance.dict() if hasattr(ep_model.provenance, "dict") else {}),
    }

    return result


def build_parameter_entity(param: ParameterMetadata) -> dict[str, Any]:
    """Convert a ParameterMetadata record to a normalized Parameter entity dict.

    This builder produces a flat dict with top-level fields expected by
    downstream relationship builders and unit tests.
    """
    stable = f"{param.spec_source}:{param.location}:{param.name}"
    source = f"openapi_parser:{stable}"
    return {
        "id": str(uuid5(NAMESPACE_URL, f"openapi-parameter:{stable}")),
        "type": "Parameter",
        "name": param.name,
        "in": param.location,
        "required": bool(param.required),
        "schema_type": param.schema_type if hasattr(param, "schema_type") else None,
        "schema_ref": param.schema_ref if hasattr(param, "schema_ref") else None,
        "description": param.description if hasattr(param, "description") else None,
        "enum_values": list(param.enum_values) if getattr(param, "enum_values", None) else [],
        "format": getattr(param, "format", None),
        "deprecated": bool(getattr(param, "deprecated", False)),
        "example": getattr(param, "example", None),
        "source": source,
        "source_file": getattr(param, "spec_source", None),
        "source_location": f"#/components/parameters/{param.name}",
    }
