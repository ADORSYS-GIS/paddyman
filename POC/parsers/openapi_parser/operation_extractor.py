from typing import Any
from uuid import NAMESPACE_URL, uuid5

from .operation_entity_builder import normalize_operation_id

_HTTP_METHODS: frozenset[str] = frozenset({"get", "post", "put", "patch", "delete", "options", "head"})


def extract_operation_entities(
    raw: dict[str, Any],
    spec_source: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """Extract operations, tags, and endpoint-operation link metadata.

    Returns lists of plain dicts (IR) for operations and tags plus a list of
    endpoint link descriptors. This preserves the parser's IR contract.
    """
    paths = raw.get("paths")
    if not isinstance(paths, dict):
        return [], [], []

    operations: list[dict[str, Any]] = []
    tags_by_name: dict[str, dict[str, Any]] = {}
    endpoint_links: list[dict[str, Any]] = []

    # Process global/top-level `tags` array in the spec when present. These
    # entries may contain `name` and `description` keys and should be used to
    # seed Tag entities so that operation tags can reference them.
    global_tags = raw.get("tags")
    if isinstance(global_tags, list):
        for t in global_tags:
            if isinstance(t, dict):
                tag_name = t.get("name")
                description = t.get("description") or None
            elif isinstance(t, str):
                tag_name = t
                description = None
            else:
                continue
            if not tag_name:
                continue
            tag_name = str(tag_name)
            if tag_name not in tags_by_name:
                tag_stable = f"{spec_source}:tag:{tag_name}"
                tags_by_name[tag_name] = {
                    "id": str(uuid5(NAMESPACE_URL, f"openapi-tag:{tag_stable}")),
                    "type": "Tag",
                    "name": tag_name,
                    "source": f"openapi_parser:{tag_stable}",
                    "description": description,
                    "source_file": spec_source,
                    "source_location": f"#/tags/{tag_name}",
                }

    for endpoint_path, path_item in paths.items():
        if not isinstance(path_item, dict):
            continue
        for method, operation in path_item.items():
            if method.lower() not in _HTTP_METHODS or not isinstance(operation, dict):
                continue

            op_id = normalize_operation_id(operation.get("operationId"), str(method), str(endpoint_path))
            match_key = f"operation:{str(method).upper()}:{str(endpoint_path)}"
            stable_source = f"{spec_source}:{match_key}:{op_id}"

            tags = [str(t) for t in operation.get("tags", []) if t is not None] if isinstance(operation.get("tags", []), list) else []

            properties = {
                "operation_id": operation.get("operationId") or op_id,
                "summary": operation.get("summary") or None,
                "description": operation.get("description") or None,
                "tags": tags,
                "deprecated": bool(operation.get("deprecated", False)),
                "external_docs": operation.get("externalDocs"),
                "method": str(method).upper(),
                "path": str(endpoint_path),
                "source_file": spec_source,
            }

            operation_entity = {
                "id": str(uuid5(NAMESPACE_URL, f"openapi-operation:{stable_source}")),
                "type": "Operation",
                "name": properties["operation_id"],
                "source": f"openapi_parser:{stable_source}",
                "match_key": match_key,
                "properties": properties,
            }
            operations.append(operation_entity)

            endpoint_links.append({
                "endpoint_path": str(endpoint_path),
                "endpoint_method": str(method).upper(),
                "operation_match_key": match_key,
            })

            for tag_name in tags:
                if tag_name and tag_name not in tags_by_name:
                    tag_stable = f"{spec_source}:tag:{tag_name}"
                    tags_by_name[tag_name] = {
                        "id": str(uuid5(NAMESPACE_URL, f"openapi-tag:{tag_stable}")),
                        "type": "Tag",
                        "name": tag_name,
                        "source": f"openapi_parser:{tag_stable}",
                        "description": None,
                        "source_file": spec_source,
                        "source_location": f"#/tags/{tag_name}",
                    }

    return operations, list(tags_by_name.values()), endpoint_links