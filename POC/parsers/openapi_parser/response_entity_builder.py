"""Build normalized Response entity dicts.

This module now uses the `Response` Pydantic model for canonical IDs and
provenance while still emitting the existing IR dict shape to preserve
backwards compatibility with downstream code and tests.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any
from uuid import NAMESPACE_URL, uuid5
from shared.models.openapi import Response


def build_response_match_key(
    response: dict[str, Any] | None,
    status_code: str | None,
) -> str | None:
    """Build a stable match key for response dedup/linking."""
    if not isinstance(response, dict):
        return None
    ref_path = response.get("$ref")
    if isinstance(ref_path, str) and ref_path:
        return f"ref:{ref_path}"
    canonical = json.dumps(response, sort_keys=True, separators=(",", ":"), default=str)
    suffix = status_code or "unknown"
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return f"fingerprint:{suffix}:{digest}"


def extract_schema_refs_by_content_type(response: dict[str, Any]) -> dict[str, str]:
    """Collect schema refs for each response content type."""
    refs: dict[str, str] = {}
    content = response.get("content")
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


def response_error_category(status_code: str | None) -> tuple[bool, str | None]:
    """Return error flags for HTTP status classes."""
    if not status_code or not status_code[:1].isdigit():
        return False, None
    if status_code.startswith("4"):
        return True, "client_error"
    if status_code.startswith("5"):
        return True, "server_error"
    if status_code.startswith("2"):
        return False, "success"
    return False, "other"


def build_response_entity(
    *,
    name: str,
    response: dict[str, Any],
    spec_source: str,
    status_code: str | None,
    ref_path: str | None,
    reusable: bool,
) -> dict[str, Any]:
    """Convert one response object to a normalized Response entity."""
    match_key = build_response_match_key(response, status_code)
    stable_source = ref_path or f"{spec_source}:{name}:{status_code}:{match_key}"
    content = response.get("content")
    content_types = sorted(content.keys()) if isinstance(content, dict) else []
    schema_refs = extract_schema_refs_by_content_type(response)
    is_error, category = response_error_category(status_code)

    # Build a Pydantic Response model for canonical id/provenance
    resp_model = Response.create(
        name=name,
        status_code=status_code,
        description=response.get("description") or "",
        schema_refs=schema_refs,
        content_types=content_types,
        spec_source=spec_source,
        ref_path=ref_path,
        reusable=reusable,
        is_error=is_error,
        error_category=category,
        id_seed=stable_source,
    )

    # Emit the historical IR dict shape so downstream consumers remain stable
    return {
        "id": str(resp_model.id),
        "type": "Response",
        "name": name,
        "source": f"openapi_parser:{stable_source}",
        "match_key": match_key,
        "schema_refs": schema_refs,
        "properties": {
            "status_code": status_code,
            "description": response.get("description") or "",
            "content_types": content_types,
            "source_file": spec_source,
            "reusable": reusable,
            "ref_path": ref_path,
            "is_error": is_error,
            "error_category": category,
        },
    }