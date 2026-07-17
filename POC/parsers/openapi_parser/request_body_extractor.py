"""Extract OpenAPI request bodies as first-class entities."""
from __future__ import annotations

from collections import Counter
from typing import Any

from openapi_parser.request_body_entity_builder import (
    build_request_body_entity,
    build_request_body_match_key,
)

_HTTP_METHODS: frozenset[str] = frozenset({"get", "post", "put", "patch", "delete", "options", "head"})


def extract_request_body_entities(
    raw: dict[str, Any],
    spec_source: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Extract request body entities and endpoint-link metadata from a spec."""
    entities_by_key: dict[str, dict[str, Any]] = {}
    endpoint_links: list[dict[str, Any]] = []
    # Map component ref path -> canonical match_key (usually a fingerprint)
    ref_to_match: dict[str, str] = {}

    _extract_component_request_bodies(raw, spec_source, entities_by_key, ref_to_match)
    _extract_endpoint_request_bodies(raw, spec_source, entities_by_key, endpoint_links, ref_to_match)
    _apply_reusability(entities_by_key, endpoint_links)

    entities = sorted(entities_by_key.values(), key=lambda item: item.get("name") or "")
    return entities, endpoint_links


def _extract_component_request_bodies(
    raw: dict[str, Any],
    spec_source: str,
    entities_by_key: dict[str, dict[str, Any]],
    ref_to_match: dict[str, str],
) -> None:
    components = raw.get("components")
    if not isinstance(components, dict):
        return
    request_bodies = components.get("requestBodies")
    if not isinstance(request_bodies, dict):
        return
    for name, body_def in request_bodies.items():
        if not isinstance(body_def, dict):
            continue
        ref_path = f"#/components/requestBodies/{name}"
        entity = build_request_body_entity(
            name=str(name),
            request_body=body_def,
            spec_source=spec_source,
            ref_path=ref_path,
            reusable=True,
        )
        match_key = entity.get("match_key")
        if isinstance(match_key, str):
            entities_by_key[match_key] = entity
            # remember that this component ref corresponds to the canonical match_key
            try:
                ref_to_match[ref_path] = match_key
            except Exception:
                pass


def _extract_endpoint_request_bodies(
    raw: dict[str, Any],
    spec_source: str,
    entities_by_key: dict[str, dict[str, Any]],
    endpoint_links: list[dict[str, Any]],
    ref_to_match: dict[str, str],
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
            request_body = operation.get("requestBody")
            if not isinstance(request_body, dict):
                continue
            operation_id = operation.get("operationId") or f"{method}_{endpoint_path}"
            entity_name = f"{operation_id}RequestBody"
            match_key = _upsert_request_body_entity(
                entities_by_key,
                spec_source,
                entity_name,
                request_body,
                ref_to_match,
            )
            endpoint_links.append({
                "endpoint_path": str(endpoint_path),
                "endpoint_method": str(method).upper(),
                "request_body_match_key": match_key,
                "required": bool(request_body.get("required", False)),
            })


def _upsert_request_body_entity(
    entities_by_key: dict[str, dict[str, Any]],
    spec_source: str,
    entity_name: str,
    request_body: dict[str, Any],
    ref_to_match: dict[str, str],
) -> str | None:
    match_key = build_request_body_match_key(request_body)
    if not isinstance(match_key, str):
        return None
    # If the endpoint used a $ref, try to map the ref to the component's canonical match_key
    if match_key.startswith("ref:"):
        ref_path = match_key[len("ref:"):]
        if ref_path in ref_to_match:
            match_key = ref_to_match[ref_path]
    if match_key not in entities_by_key:
        entities_by_key[match_key] = build_request_body_entity(
            name=entity_name,
            request_body=request_body,
            spec_source=spec_source,
            ref_path=request_body.get("$ref") if isinstance(request_body.get("$ref"), str) else None,
            reusable=False,
        )
    return match_key


def _apply_reusability(
    entities_by_key: dict[str, dict[str, Any]],
    endpoint_links: list[dict[str, Any]],
) -> None:
    counts = Counter(link.get("request_body_match_key") for link in endpoint_links)
    for match_key, entity in entities_by_key.items():
        props = entity.get("properties")
        if not isinstance(props, dict):
            continue
        if counts.get(match_key, 0) > 1:
            props["reusable"] = True