"""Build normalized RequestBody entity dicts."""
from __future__ import annotations

import hashlib
import json
from typing import Any
from uuid import NAMESPACE_URL, uuid5


def build_request_body_match_key(request_body: dict[str, Any] | None) -> str | None:
    """Build a stable match key for request-body dedup and linking."""
    if not isinstance(request_body, dict):
        return None
    ref_path = request_body.get("$ref")
    if isinstance(ref_path, str) and ref_path:
        return f"ref:{ref_path}"
    canonical = json.dumps(request_body, sort_keys=True, separators=(",", ":"), default=str)
    return f"fingerprint:{hashlib.sha256(canonical.encode('utf-8')).hexdigest()}"


def extract_schema_refs_by_content_type(request_body: dict[str, Any]) -> dict[str, str]:
    """Collect schema refs for each content type in a request body."""
    refs: dict[str, str] = {}
    content = request_body.get("content")
    if not isinstance(content, dict):
        return refs
    for content_type, media_type_obj in content.items():
        if not isinstance(media_type_obj, dict):
            continue
        schema = media_type_obj.get("schema")
        if not isinstance(schema, dict):
            continue
        schema_ref = schema.get("$ref")
        if isinstance(schema_ref, str) and schema_ref:
            refs[str(content_type)] = schema_ref
    return refs


def build_request_body_entity(
    *,
    name: str,
    request_body: dict[str, Any],
    spec_source: str,
    ref_path: str | None,
    reusable: bool,
) -> dict[str, Any]:
    """Convert a request-body object into a normalized RequestBody entity."""
    match_key = build_request_body_match_key(request_body)
    stable_source = ref_path or f"{spec_source}:{name}:{match_key}"
    content = request_body.get("content")
    content_types = sorted(content.keys()) if isinstance(content, dict) else []
    schema_refs = extract_schema_refs_by_content_type(request_body)
    required = bool(request_body.get("required", False))

    return {
        "id": str(uuid5(NAMESPACE_URL, f"openapi-request-body:{stable_source}")),
        "type": "RequestBody",
        "name": name,
        "source": f"openapi_parser:{stable_source}",
        "match_key": match_key,
        "schema_refs": schema_refs,
        "properties": {
            "description": request_body.get("description") or None,
            "required": required,
            "content_types": content_types,
            "source_file": spec_source,
            "reusable": reusable,
            "ref_path": ref_path,
        },
    }