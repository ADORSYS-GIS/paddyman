"""OpenAPI schema extractor (Chunk 3.3).

Pure function module — no I/O.  Accepts a parsed OpenAPI document (Python
dict) and returns structured :class:`~openapi_parser.models.SchemaMetadata`
records, one per entry in ``components.schemas``.

Now includes $ref tracking metadata for each schema.

Intentionally excluded:
- schema dependency graph generation
- ``$ref`` resolution / dereferencing
- code generation
- API relationship analysis
"""
from __future__ import annotations

import logging
from typing import Any

from openapi_parser.models import PropertyMetadata, SchemaMetadata
from openapi_parser.ref_utils import collect_refs_from_schema, is_external_ref

logger = logging.getLogger(__name__)

#: Composition keywords whose items may carry ``$ref`` entries.
_COMPOSITION_KEYS: tuple[str, ...] = ("allOf", "oneOf", "anyOf")


def extract_schemas(
    raw: dict[str, Any],
    spec_source: str,
) -> list[SchemaMetadata]:
    """Extract all schema definitions from ``components.schemas``.

    Args:
        raw:        Parsed OpenAPI YAML document (top-level mapping).
        spec_source: File path or repository identifier of the source spec.

    Returns:
        List of :class:`~openapi_parser.models.SchemaMetadata`, one per
        entry under ``components.schemas``.  Returns an empty list when the
        section is absent or not a mapping.
    """
    components = raw.get("components")
    if not isinstance(components, dict):
        logger.debug("No 'components' block found in spec from %s", spec_source)
        return []

    schemas_block = components.get("schemas")
    if not isinstance(schemas_block, dict):
        logger.debug("No 'components.schemas' block found in spec from %s", spec_source)
        return []

    results: list[SchemaMetadata] = []
    for schema_name, schema_def in schemas_block.items():
        if not isinstance(schema_def, dict):
            logger.debug("Skipping non-dict schema entry '%s' in %s", schema_name, spec_source)
            continue
        results.append(_build_schema(str(schema_name), schema_def, spec_source))

    logger.debug("Extracted %d schema(s) from %s", len(results), spec_source)
    return results


def _build_schema(
    name: str,
    schema: dict[str, Any],
    spec_source: str,
) -> SchemaMetadata:
    """Build a :class:`SchemaMetadata` from a single schema definition dict."""
    schema_type: str | None = schema.get("type") or None
    description: str | None = schema.get("description") or None

    enum_raw = schema.get("enum")
    enum_values: list[Any] = list(enum_raw) if isinstance(enum_raw, list) else []

    required_raw = schema.get("required")
    required: list[str] = (
        [str(f) for f in required_raw if f is not None]
        if isinstance(required_raw, list)
        else []
    )
    required_set: set[str] = set(required)

    props_raw = schema.get("properties")
    properties: list[PropertyMetadata] = (
        _extract_properties(props_raw, required_set)
        if isinstance(props_raw, dict)
        else []
    )

    refs: list[str] = _collect_composition_refs(schema)
    
    # Collect all $ref paths and identify external ones
    all_refs = collect_refs_from_schema(schema)
    external_refs = [ref for ref in all_refs if is_external_ref(ref)]

    return SchemaMetadata(
        type="schema",
        name=name,
        spec_source=spec_source,
        schema_type=schema_type,
        description=description,
        properties=properties,
        required=required,
        enum_values=enum_values,
        refs=refs,
        external_refs=external_refs,
    )


def _extract_properties(
    props: dict[str, Any],
    required: set[str],
) -> list[PropertyMetadata]:
    """Build a :class:`PropertyMetadata` list from a schema ``properties`` block."""
    result: list[PropertyMetadata] = []
    for prop_name, prop_def in props.items():
        if not isinstance(prop_def, dict):
            continue
        enum_raw = prop_def.get("enum")
        result.append(
            PropertyMetadata(
                name=str(prop_name),
                type=prop_def.get("type") or None,
                ref=prop_def.get("$ref") or None,
                description=prop_def.get("description") or None,
                required=prop_name in required,
                enum_values=list(enum_raw) if isinstance(enum_raw, list) else [],
                format=prop_def.get("format") or None,
            )
        )
    return result


def _collect_composition_refs(schema: dict[str, Any]) -> list[str]:
    """Collect ``$ref`` strings from ``allOf`` / ``oneOf`` / ``anyOf`` entries."""
    refs: list[str] = []
    for key in _COMPOSITION_KEYS:
        items = schema.get(key)
        if not isinstance(items, list):
            continue
        for item in items:
            if isinstance(item, dict) and "$ref" in item:
                refs.append(str(item["$ref"]))
    return refs
