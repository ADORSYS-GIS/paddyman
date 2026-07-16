"""OpenAPI endpoint extractor (Chunk 3.2).

Pure function module — no I/O.  Accepts a parsed OpenAPI document (Python
dict) and returns structured :class:`~openapi_parser.models.EndpointMetadata`
records, one per HTTP operation found in the ``paths`` block.

Intentionally excluded:
- schema / model extraction
- ``$ref`` resolution
- API relationship analysis
"""
from __future__ import annotations

import logging
from typing import Any

from openapi_parser.models import EndpointMetadata, ParameterMetadata

logger = logging.getLogger(__name__)

#: HTTP methods recognised by this extractor (OpenAPI 3.x + Swagger 2 set).
_HTTP_METHODS: frozenset[str] = frozenset(
    {"get", "post", "put", "patch", "delete", "options", "head"}
)


def extract_endpoints(
    raw: dict[str, Any],
    api_title: str,
    spec_source: str,
) -> list[EndpointMetadata]:
    """Extract all HTTP operations from a parsed OpenAPI document.

    Args:
        raw:        Parsed YAML document (top-level mapping).
        api_title:  Human-readable API title (from ``info.title``).
        spec_source: File path or repository identifier of the source spec.

    Returns:
        List of :class:`~openapi_parser.models.EndpointMetadata`, one per
        ``(path, method)`` pair.  Returns an empty list when ``paths`` is
        absent or empty.
    """
    paths = raw.get("paths")
    if not isinstance(paths, dict):
        logger.debug("No 'paths' block found in spec from %s", spec_source)
        return []

    results: list[EndpointMetadata] = []
    for api_path, path_item in paths.items():
        if not isinstance(path_item, dict):
            continue
        for method, operation in path_item.items():
            if method.lower() not in _HTTP_METHODS:
                continue  # skip non-operation keys (parameters, summary, …)
            if not isinstance(operation, dict):
                continue
            results.append(
                _build_endpoint(str(api_path), method, operation, api_title, spec_source)
            )

    logger.debug(
        "Extracted %d endpoint(s) from %s", len(results), spec_source
    )
    return results


def _build_endpoint(
    api_path: str,
    method: str,
    operation: dict[str, Any],
    api_title: str,
    spec_source: str,
) -> EndpointMetadata:
    """Build a single :class:`EndpointMetadata` from raw operation data."""
    tags_raw = operation.get("tags")
    tags: list[str] = (
        [str(t) for t in tags_raw if t is not None]
        if isinstance(tags_raw, list)
        else []
    )

    params_raw = operation.get("parameters")
    parameters: list[ParameterMetadata] = []
    if isinstance(params_raw, list):
        for p in params_raw:
            if not isinstance(p, dict):
                continue
            schema = p.get("schema") or {}
            parameters.append(ParameterMetadata(
                name=str(p.get("name", "")),
                location=str(p.get("in", "")),
                required=bool(p.get("required", False)),
                description=p.get("description") or None,
                schema_type=schema.get("type") or None,
                schema_ref=schema.get("$ref") or p.get("$ref") or None,
                format=schema.get("format") or None,
                deprecated=bool(p.get("deprecated", False)),
                example=p.get("example"),
            ))

    request_body_raw = operation.get("requestBody")
    request_body = dict(request_body_raw) if isinstance(request_body_raw, dict) else None

    responses_raw = operation.get("responses")
    responses: dict[str, Any] = dict(responses_raw) if isinstance(responses_raw, dict) else {}

    return EndpointMetadata(
        type="endpoint",
        method=method.upper(),
        path=api_path,
        api_title=api_title,
        spec_source=spec_source,
        operation_id=operation.get("operationId") or None,
        summary=operation.get("summary") or None,
        description=operation.get("description") or None,
        tags=tags,
        parameters=parameters,
        request_body=request_body,
        responses=responses,
    )
