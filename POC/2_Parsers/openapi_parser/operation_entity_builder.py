"""Build normalized Operation and Tag entity dicts."""
from __future__ import annotations

import re
from typing import Any
from uuid import NAMESPACE_URL, uuid5


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
) -> dict[str, Any]:
    """Convert one OpenAPI operation object into an Operation entity."""
    stable_key = f"{spec_source}:{method.upper()}:{path}:{operation_id}"
    operation_tags = operation.get("tags")
    tags = [str(tag) for tag in operation_tags if tag is not None] if isinstance(operation_tags, list) else []
    return {
        "id": str(uuid5(NAMESPACE_URL, f"openapi-operation:{stable_key}")),
        "type": "Operation",
        "name": operation_id,
        "source": f"openapi_parser:{stable_key}",
        "match_key": f"operation:{method.upper()}:{path}",
        "properties": {
            "operation_id": operation_id,
            "summary": operation.get("summary") or None,
            "description": operation.get("description") or None,
            "tags": tags,
            "deprecated": bool(operation.get("deprecated", False)),
            "external_docs": operation.get("externalDocs") if isinstance(operation.get("externalDocs"), dict) else None,
            "source_file": spec_source,
            "method": method.upper(),
            "path": path,
        },
        "security_requirements": [],
    }


def build_tag_entity(tag_name: str, spec_source: str) -> dict[str, Any]:
    """Build a Tag entity for a unique operation tag."""
    stable_key = f"{spec_source}:{tag_name}"
    return {
        "id": str(uuid5(NAMESPACE_URL, f"openapi-tag:{stable_key}")),
        "type": "Tag",
        "name": tag_name,
        "source": f"openapi_parser:{stable_key}",
        "properties": {"tag_name": tag_name, "source_file": spec_source},
    }