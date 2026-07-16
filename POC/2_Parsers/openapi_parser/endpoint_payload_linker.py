"""Attach request/response payload links to endpoint entities."""
from __future__ import annotations

from typing import Any

from openapi_parser.operation_extractor import extract_operation_entities
from openapi_parser.request_body_extractor import extract_request_body_entities
from openapi_parser.response_extractor import extract_response_entities
from openapi_parser.security_requirement_extractor import extract_security_requirements


def link_endpoint_payload_entities(
    entities: list[dict[str, Any]],
    raw: dict[str, Any],
    spec_source: str,
) -> None:
    """Add operation/request/response/security entities and links to endpoints."""
    _link_operations(entities, raw, spec_source)
    _link_request_bodies(entities, raw, spec_source)
    _link_responses(entities, raw, spec_source)
    _link_security(entities, raw, spec_source)


def _endpoint_index(entities: list[dict[str, Any]]) -> dict[tuple[str, str], dict[str, Any]]:
    return {
        (entity.get("path"), entity.get("method")): entity
        for entity in entities
        if entity.get("type") == "Endpoint"
    }


def _operation_index(entities: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {
        str(entity.get("match_key")): entity
        for entity in entities
        if entity.get("type") == "Operation" and entity.get("match_key")
    }


def _link_request_bodies(entities: list[dict[str, Any]], raw: dict[str, Any], spec_source: str) -> None:
    request_entities, endpoint_links = extract_request_body_entities(raw, spec_source)
    entities.extend(request_entities)
    endpoint_idx = _endpoint_index(entities)
    for link in endpoint_links:
        endpoint = endpoint_idx.get((link.get("endpoint_path"), link.get("endpoint_method")))
        if isinstance(endpoint, dict):
            endpoint["request_body_match_key"] = link.get("request_body_match_key")
            endpoint["request_body_required"] = bool(link.get("required", False))


def _link_responses(entities: list[dict[str, Any]], raw: dict[str, Any], spec_source: str) -> None:
    response_entities, endpoint_links = extract_response_entities(raw, spec_source)
    entities.extend(response_entities)
    endpoint_idx = _endpoint_index(entities)
    for link in endpoint_links:
        endpoint = endpoint_idx.get((link.get("endpoint_path"), link.get("endpoint_method")))
        if not isinstance(endpoint, dict):
            continue
        mapping = endpoint.get("response_match_keys")
        if not isinstance(mapping, dict):
            mapping = {}
            endpoint["response_match_keys"] = mapping
        status_code = str(link.get("status_code"))
        mapping[status_code] = link.get("response_match_key")


def _link_operations(entities: list[dict[str, Any]], raw: dict[str, Any], spec_source: str) -> None:
    operations, tags, endpoint_links = extract_operation_entities(raw, spec_source)
    entities.extend(operations)
    entities.extend(tags)
    endpoint_idx = _endpoint_index(entities)
    for link in endpoint_links:
        endpoint = endpoint_idx.get((link.get("endpoint_path"), link.get("endpoint_method")))
        if isinstance(endpoint, dict):
            endpoint["operation_match_key"] = link.get("operation_match_key")


def _link_security(entities: list[dict[str, Any]], raw: dict[str, Any], spec_source: str) -> None:
    scope_entities, endpoint_links, operation_links = extract_security_requirements(raw, spec_source)
    entities.extend(scope_entities)

    endpoint_idx = _endpoint_index(entities)
    for link in endpoint_links:
        endpoint = endpoint_idx.get((link.get("endpoint_path"), link.get("endpoint_method")))
        if isinstance(endpoint, dict):
            endpoint["security_requirements"] = link.get("security_requirements", [])

    operation_idx = _operation_index(entities)
    for link in operation_links:
        operation = operation_idx.get(str(link.get("operation_match_key")))
        if isinstance(operation, dict):
            operation["security_requirements"] = link.get("security_requirements", [])