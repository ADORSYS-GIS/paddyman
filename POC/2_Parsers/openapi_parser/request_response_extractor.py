"""OpenAPI request body and response extractor.

Pure function module — no I/O.  Accepts a parsed OpenAPI document (Python
dict) and returns structured :class:`~openapi_parser.models.RequestBodyMetadata`
and :class:`~openapi_parser.models.ResponseMetadata` records.

Extracts reusable definitions from:
- ``components.requestBodies``
- ``components.responses``

These components can be referenced by operations via ``$ref``.
"""
from __future__ import annotations

import logging
from typing import Any

from openapi_parser.models import RequestBodyMetadata, ResponseMetadata

logger = logging.getLogger(__name__)


def extract_request_bodies(
    raw: dict[str, Any],
    spec_source: str,
) -> list[RequestBodyMetadata]:
    """Extract all request body definitions from components.requestBodies.

    Args:
        raw:        Parsed YAML document (top-level mapping).
        spec_source: File path or repository identifier of the source spec.

    Returns:
        List of :class:`~openapi_parser.models.RequestBodyMetadata`, one per
        named request body in ``components.requestBodies``.  Returns an empty
        list when the section is absent or empty.
    """
    components = raw.get("components")
    if not isinstance(components, dict):
        logger.debug("No 'components' block found in spec from %s", spec_source)
        return []

    request_bodies = components.get("requestBodies")
    if not isinstance(request_bodies, dict):
        logger.debug("No 'requestBodies' in components from %s", spec_source)
        return []

    results: list[RequestBodyMetadata] = []
    for name, body_def in request_bodies.items():
        if not isinstance(body_def, dict):
            continue
        results.append(_build_request_body(str(name), body_def, spec_source))

    logger.debug(
        "Extracted %d request body definition(s) from %s", len(results), spec_source
    )
    return results


def extract_responses(
    raw: dict[str, Any],
    spec_source: str,
) -> list[ResponseMetadata]:
    """Extract all response definitions from components.responses.

    Args:
        raw:        Parsed YAML document (top-level mapping).
        spec_source: File path or repository identifier of the source spec.

    Returns:
        List of :class:`~openapi_parser.models.ResponseMetadata`, one per
        named response in ``components.responses``.  Returns an empty list
        when the section is absent or empty.
    """
    components = raw.get("components")
    if not isinstance(components, dict):
        logger.debug("No 'components' block found in spec from %s", spec_source)
        return []

    responses = components.get("responses")
    if not isinstance(responses, dict):
        logger.debug("No 'responses' in components from %s", spec_source)
        return []

    results: list[ResponseMetadata] = []
    for name, response_def in responses.items():
        if not isinstance(response_def, dict):
            continue
        results.append(_build_response(str(name), response_def, spec_source))

    logger.debug(
        "Extracted %d response definition(s) from %s", len(results), spec_source
    )
    return results


def _build_request_body(
    name: str,
    body_def: dict[str, Any],
    spec_source: str,
) -> RequestBodyMetadata:
    """Build a single :class:`RequestBodyMetadata` from raw component data."""
    required = bool(body_def.get("required", False))
    description = body_def.get("description") or None
    
    content_types: list[str] = []
    schema_ref: str | None = None
    schema_type: str | None = None
    
    content = body_def.get("content")
    if isinstance(content, dict):
        content_types = list(content.keys())
        # Extract schema info from first content type
        for media_type_obj in content.values():
            if isinstance(media_type_obj, dict):
                schema = media_type_obj.get("schema")
                if isinstance(schema, dict):
                    schema_ref = schema.get("$ref") or None
                    if not schema_ref:
                        schema_type = schema.get("type") or None
                break
    
    return RequestBodyMetadata(
        name=name,
        spec_source=spec_source,
        required=required,
        description=description,
        content_types=content_types,
        schema_ref=schema_ref,
        schema_type=schema_type,
    )


def _build_response(
    name: str,
    response_def: dict[str, Any],
    spec_source: str,
) -> ResponseMetadata:
    """Build a single :class:`ResponseMetadata` from raw component data."""
    description = response_def.get("description", "")
    
    # Try to extract HTTP status from name if it follows convention
    # e.g., "CREATED_201_PaymentInitiation" -> "201"
    http_status: str | None = None
    parts = name.split("_")
    for part in parts:
        if part.isdigit() and len(part) == 3:
            http_status = part
            break
    
    content_types: list[str] = []
    schema_ref: str | None = None
    schema_type: str | None = None
    headers: dict[str, Any] = {}
    
    content = response_def.get("content")
    if isinstance(content, dict):
        content_types = list(content.keys())
        # Extract schema info from first content type
        for media_type_obj in content.values():
            if isinstance(media_type_obj, dict):
                schema = media_type_obj.get("schema")
                if isinstance(schema, dict):
                    schema_ref = schema.get("$ref") or None
                    if not schema_ref:
                        schema_type = schema.get("type") or None
                break
    
    headers_raw = response_def.get("headers")
    if isinstance(headers_raw, dict):
        headers = dict(headers_raw)
    
    return ResponseMetadata(
        name=name,
        spec_source=spec_source,
        description=description,
        http_status=http_status,
        content_types=content_types,
        schema_ref=schema_ref,
        schema_type=schema_type,
        headers=headers,
    )
