"""Helpers to convert CALLS relationships into enriched dict payloads."""
from __future__ import annotations

from java_parser.relationships.models import JavaRelationship


def build_calls_payload(
    rel: JavaRelationship,
    source_id: str,
    target_id: str,
    target_resolved: bool,
) -> dict:
    """Build enriched CALLS relationship dict with metadata properties."""
    argument_types = rel.argument_types or []
    payload = {
        "type": rel.relationship_type,
        "source": source_id,
        "target": target_id,
        "source_entity_id": source_id,
        "target_entity_id": target_id,
        "repository": rel.repository,
        "module": rel.module,
        "package": rel.package,
        "file_path": rel.file_path,
        "source_method": rel.source_method,
        "target_method": rel.target_method,
        "target_class": rel.target_class,
        "properties": {
            "source_method": rel.source_method,
            "target_method": rel.target_method,
            "target_class": rel.target_class,
            "call_site_line": rel.call_site_line,
            "is_static": rel.is_static,
            "receiver_type": rel.receiver_type,
            "receiver_variable": rel.receiver_variable,
            "argument_count": rel.arguments_count,
            "argument_types": argument_types,
            "method_signature": rel.method_signature,
            "is_constructor": rel.is_constructor,
        },
    }
    if not target_resolved:
        payload["target_resolved"] = False
    return payload
