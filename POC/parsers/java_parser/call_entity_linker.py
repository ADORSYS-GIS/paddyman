"""Resolve CALLS relationship entity ids to Method/Constructor UUIDs when available."""
from __future__ import annotations

from typing import Any


def _method_index(entities: list[dict[str, Any]]) -> dict[str, str]:
    index: dict[str, str] = {}
    for entity in entities:
        entity_type = entity.get("type")
        qualified_class = entity.get("qualified_class")
        name = entity.get("name")
        entity_uuid = entity.get("uuid")
        if not qualified_class or not name or not entity_uuid:
            continue
        if entity_type == "Method":
            index[f"{qualified_class}#{name}"] = entity_uuid
        if entity_type == "Constructor":
            index[f"{qualified_class}#<init>"] = entity_uuid
            index[f"{qualified_class}#{name}"] = entity_uuid
    return index


def attach_call_entity_ids(
    relationships: list[dict[str, Any]],
    entities: list[dict[str, Any]],
) -> None:
    """Update CALLS relationship entity-id fields with actual UUIDs when resolvable."""
    index = _method_index(entities)
    for rel in relationships:
        if rel.get("type") != "CALLS":
            continue
        source_key = str(rel.get("source", ""))
        target_key = str(rel.get("target", ""))
        source_uuid = index.get(source_key)
        target_uuid = index.get(target_key)
        if source_uuid:
            rel["source_entity_id"] = source_uuid
        if target_uuid:
            rel["target_entity_id"] = target_uuid
