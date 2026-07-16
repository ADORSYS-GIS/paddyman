"""Extract OpenAPI responses as first-class entities."""
from __future__ import annotations

from collections import Counter
from typing import Any

from openapi_parser.response_entity_builder import (
    build_response_entity,
    build_response_match_key,
)

_HTTP_METHODS: frozenset[str] = frozenset({"get", "post", "put", "patch", "delete", "options", "head"})


def extract_response_entities(
    raw: dict[str, Any],
    spec_source: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Extract response entities and endpoint-link metadata from a spec."""
    entities_by_key: dict[str, dict[str, Any]] = {}
    endpoint_links: list[dict[str, Any]] = []
    _extract_component_responses(raw, spec_source, entities_by_key)
    _extract_endpoint_responses(raw, spec_source, entities_by_key, endpoint_links)
    _apply_reusability(entities_by_key, endpoint_links)
    entities = sorted(entities_by_key.values(), key=lambda item: item.get("name") or "")
    return entities, endpoint_links


def _extract_component_responses(
    raw: dict[str, Any],
    spec_source: str,
    entities_by_key: dict[str, dict[str, Any]],
) -> None:
    components = raw.get("components")
    if not isinstance(components, dict):
        return
    responses = components.get("responses")
    if not isinstance(responses, dict):
        return
    for name, response_def in responses.items():
        if not isinstance(response_def, dict):
            continue
        ref_path = f"#/components/responses/{name}"
        entity = build_response_entity(
            name=str(name),
            response=response_def,
            spec_source=spec_source,
            status_code=_infer_status_from_name(str(name)),
            ref_path=ref_path,
            reusable=True,
        )
        match_key = entity.get("match_key")
        if isinstance(match_key, str):
            entities_by_key[match_key] = entity


def _extract_endpoint_responses(
    raw: dict[str, Any],
    spec_source: str,
    entities_by_key: dict[str, dict[str, Any]],
    endpoint_links: list[dict[str, Any]],
) -> None:
    paths = raw.get("paths")
    if not isinstance(paths, dict):
        return
    for endpoint_path, path_item in paths.items():
        if not isinstance(path_item, dict):
            continue
        for method, operation in path_item.items():
            if method.lower() not in _HTTP_METHODS or not isinstance(operation, dict):
                continue
            responses = operation.get("responses")
            if not isinstance(responses, dict):
                continue
            for status_code, response_def in responses.items():
                if not isinstance(response_def, dict):
                    continue
                op_id = operation.get("operationId") or f"{method}_{endpoint_path}"
                entity_name = f"{status_code} {op_id}Response"
                match_key = _upsert_response_entity(
                    entities_by_key,
                    spec_source,
                    entity_name,
                    str(status_code),
                    response_def,
                )
                endpoint_links.append({
                    "endpoint_path": str(endpoint_path),
                    "endpoint_method": str(method).upper(),
                    "status_code": str(status_code),
                    "response_match_key": match_key,
                })


def _upsert_response_entity(
    entities_by_key: dict[str, dict[str, Any]],
    spec_source: str,
    name: str,
    status_code: str,
    response: dict[str, Any],
) -> str | None:
    match_key = build_response_match_key(response, status_code)
    if not isinstance(match_key, str):
        return None
    if match_key not in entities_by_key:
        ref_path = response.get("$ref") if isinstance(response.get("$ref"), str) else None
        entities_by_key[match_key] = build_response_entity(
            name=name,
            response=response,
            spec_source=spec_source,
            status_code=status_code,
            ref_path=ref_path,
            reusable=False,
        )
    return match_key


def _apply_reusability(entities_by_key: dict[str, dict[str, Any]], endpoint_links: list[dict[str, Any]]) -> None:
    counts = Counter(link.get("response_match_key") for link in endpoint_links)
    for match_key, entity in entities_by_key.items():
        props = entity.get("properties")
        if isinstance(props, dict) and counts.get(match_key, 0) > 1:
            props["reusable"] = True


def _infer_status_from_name(name: str) -> str | None:
    parts = [part for part in name.replace("-", "_").split("_") if part]
    for part in parts:
        if len(part) == 3 and part.isdigit():
            return part
    return None