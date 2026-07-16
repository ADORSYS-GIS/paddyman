"""Extract OpenAPI operations and tags as first-class entities."""
from __future__ import annotations

from typing import Any

from openapi_parser.operation_entity_builder import (
    build_operation_entity,
    build_tag_entity,
    normalize_operation_id,
)

_HTTP_METHODS: frozenset[str] = frozenset({"get", "post", "put", "patch", "delete", "options", "head"})


def extract_operation_entities(
    raw: dict[str, Any],
    spec_source: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """Extract operations, tags, and endpoint-operation link metadata."""
    paths = raw.get("paths")
    if not isinstance(paths, dict):
        return [], [], []

    operations: list[dict[str, Any]] = []
    endpoint_links: list[dict[str, Any]] = []
    tags_by_name: dict[str, dict[str, Any]] = {}

    for endpoint_path, path_item in paths.items():
        if not isinstance(path_item, dict):
            continue
        for method, operation in path_item.items():
            if method.lower() not in _HTTP_METHODS or not isinstance(operation, dict):
                continue
            op_id = normalize_operation_id(operation.get("operationId"), str(method), str(endpoint_path))
            operation_entity = build_operation_entity(
                operation_id=op_id,
                method=str(method),
                path=str(endpoint_path),
                operation=operation,
                spec_source=spec_source,
            )
            operations.append(operation_entity)
            endpoint_links.append({
                "endpoint_path": str(endpoint_path),
                "endpoint_method": str(method).upper(),
                "operation_match_key": operation_entity.get("match_key"),
            })

            for tag in operation_entity["properties"].get("tags", []):
                if isinstance(tag, str) and tag and tag not in tags_by_name:
                    tags_by_name[tag] = build_tag_entity(tag, spec_source)

    return operations, list(tags_by_name.values()), endpoint_links