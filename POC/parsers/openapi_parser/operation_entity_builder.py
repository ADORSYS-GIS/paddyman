from shared.models.openapi import Operation, Tag
from uuid import uuid5, NAMESPACE_URL, UUID
import re
from typing import Any


def normalize_operation_id(operation_id: str | None, method: str, path: str) -> str:
    """Return operation id, generating a deterministic fallback when missing."""
    if isinstance(operation_id, str) and operation_id.strip():
        return operation_id.strip()
    raw = f"{method.lower()}_{path}".replace("/", "_")
    normalized = re.sub(r"[^a-zA-Z0-9_]+", "_", raw)
    normalized = re.sub(r"_+", "_", normalized)
    return normalized.strip("_") or "operation"


def build_operation_entity(
    *,
    operation_id: str,
    method: str,
    path: str,
    operation: dict[str, Any],
    spec_source: str,
    endpoint_id: UUID,
) -> Operation:
    """Convert one OpenAPI operation object into an Operation entity."""
    # Emit historical IR dict shape (id as string + nested properties)
    op_id = normalize_operation_id(operation_id, method, path)
    match_key = f"operation:{str(method).upper()}:{str(path)}"
    stable_source = f"{spec_source}:{match_key}:{op_id}"

    return {
        "id": str(uuid5(NAMESPACE_URL, f"openapi-operation:{stable_source}")),
        "type": "Operation",
        "name": op_id,
        "source": f"openapi_parser:{stable_source}",
        "match_key": match_key,
        "properties": {
            "operation_id": operation.get("operationId") or op_id,
            "summary": operation.get("summary") or None,
            "description": operation.get("description") or None,
            "tags": [str(t) for t in operation.get("tags", []) if t is not None] if isinstance(operation.get("tags", []), list) else [],
            "deprecated": bool(operation.get("deprecated", False)),
            "external_docs": operation.get("externalDocs"),
            "method": str(method).upper(),
            "path": str(path),
            "source_file": spec_source,
        },
    }


def build_tag_entity(tag_name: str, spec_source: str, description: str | None = None) -> Tag:
    """Build a Tag entity for a unique operation tag."""
    stable = f"{spec_source}:tag:{tag_name}"
    return {
        "id": str(uuid5(NAMESPACE_URL, f"openapi-tag:{stable}")),
        "type": "Tag",
        "name": tag_name,
        "source": f"openapi_parser:{stable}",
        "description": description,
        "source_file": spec_source,
        "source_location": f"#/tags/{tag_name}",
    }