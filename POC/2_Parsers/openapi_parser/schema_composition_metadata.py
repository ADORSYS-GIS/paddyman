"""Extract schema composition metadata from raw OpenAPI schema definitions."""
from __future__ import annotations

from typing import Any

from openapi_parser.relationship_builder import extract_schema_name_from_ref

_COMPOSITION_TYPES: tuple[str, ...] = ("allOf", "oneOf", "anyOf")
_REL_TYPE_BY_COMPOSITION = {
    "allOf": "COMPOSES_ALL_OF",
    "oneOf": "ONE_OF",
    "anyOf": "ANY_OF",
    "not": "NOT",
}


def extract_schema_composition_map(raw: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    """Build a map of schema name -> composition relationship descriptors."""
    components = raw.get("components")
    if not isinstance(components, dict):
        return {}
    schemas_block = components.get("schemas")
    if not isinstance(schemas_block, dict):
        return {}

    result: dict[str, list[dict[str, Any]]] = {}
    for schema_name, schema_def in schemas_block.items():
        if not isinstance(schema_def, dict):
            continue
        descriptors: list[dict[str, Any]] = []
        _collect_compositions(schema_def, descriptors, ())
        if descriptors:
            result[str(schema_name)] = descriptors
    return result


def _collect_compositions(
    schema_node: dict[str, Any],
    out: list[dict[str, Any]],
    path: tuple[str, ...],
) -> None:
    discriminator = _discriminator(schema_node)

    for comp_type in _COMPOSITION_TYPES:
        entries = schema_node.get(comp_type)
        if not isinstance(entries, list):
            continue
        for position, entry in enumerate(entries):
            if not isinstance(entry, dict):
                continue
            _append_descriptor(out, comp_type, position, entry, discriminator, path)
            _collect_compositions(entry, out, path + (f"{comp_type}[{position}]",))

    not_entry = schema_node.get("not")
    if isinstance(not_entry, dict):
        _append_descriptor(out, "not", None, not_entry, None, path)
        _collect_compositions(not_entry, out, path + ("not",))


def _append_descriptor(
    out: list[dict[str, Any]],
    composition_type: str,
    position: int | None,
    entry: dict[str, Any],
    discriminator: str | None,
    path: tuple[str, ...],
) -> None:
    ref_path = entry.get("$ref") if isinstance(entry.get("$ref"), str) else None
    target_name = extract_schema_name_from_ref(ref_path) if ref_path else None
    out.append(
        {
            "relationship_type": _REL_TYPE_BY_COMPOSITION[composition_type],
            "composition_type": composition_type,
            "position": position,
            "discriminator": discriminator if composition_type == "oneOf" else None,
            "ref_path": ref_path,
            "target_schema": target_name,
            "inline": ref_path is None,
            "path": "/".join(path),
        }
    )


def _discriminator(schema_node: dict[str, Any]) -> str | None:
    raw = schema_node.get("discriminator")
    if not isinstance(raw, dict):
        return None
    name = raw.get("propertyName")
    if isinstance(name, str) and name:
        return name
    return None
