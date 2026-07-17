"""OpenAPI ``$ref`` reference resolver (Chunk 3.4).

Pure function module — no I/O.  Accepts already-extracted endpoint and schema
objects together with the raw parsed YAML document, and produces
:class:`~openapi_parser.models.RelationshipMetadata` records representing
the directed relationships implied by ``$ref`` values.

Three relationship types are produced:

* ``RETURNS``    — endpoint → schema (response schema refs).
* ``ACCEPTS``    — endpoint → schema (requestBody schema refs).
* ``REFERENCES`` — schema → schema (allOf / oneOf / anyOf and property refs).

Intentionally excluded:
- final graph construction
- ``$ref`` dereferencing for code generation
- API relationship analysis beyond direct refs
"""
from __future__ import annotations

import logging
from typing import Any

from openapi_parser.models import EndpointMetadata, RelationshipMetadata, SchemaMetadata

logger = logging.getLogger(__name__)

_SCHEMA_REF_PREFIX = "#/components/schemas/"
_MAX_FOLLOW_DEPTH = 5  # guard against circular refs


def resolve_refs(
    raw: dict[str, Any],
    endpoints: list[EndpointMetadata],
    schemas: list[SchemaMetadata],
    spec_source: str,
) -> list[RelationshipMetadata]:
    """Resolve all ``$ref`` values and produce relationship records.

    Args:
        raw:        Parsed OpenAPI YAML document (top-level mapping).
        endpoints:  Endpoint records extracted by :mod:`openapi_parser.extractor`.
        schemas:    Schema records extracted by :mod:`openapi_parser.schema_extractor`.
        spec_source: File path or repository identifier of the source spec.

    Returns:
        Flat list of :class:`~openapi_parser.models.RelationshipMetadata`.
    """
    results: list[RelationshipMetadata] = []
    results.extend(_endpoint_returns(raw, endpoints, spec_source))
    results.extend(_endpoint_accepts(raw, endpoints, spec_source))
    results.extend(_schema_references(schemas, spec_source))
    logger.debug("Resolved %d relationship(s) from %s", len(results), spec_source)
    return results


# ---------------------------------------------------------------------------
# Endpoint → schema relationships
# ---------------------------------------------------------------------------

def _endpoint_returns(
    raw: dict[str, Any],
    endpoints: list[EndpointMetadata],
    spec_source: str,
) -> list[RelationshipMetadata]:
    """Produce RETURNS relationships from response ``$ref`` values."""
    results: list[RelationshipMetadata] = []
    for ep in endpoints:
        source_label = f"{ep.method} {ep.path}"
        for ref in _schema_refs_from_obj(raw, ep.responses):
            name = _schema_name(ref)
            if name:
                results.append(_make_rel(
                    source_label, name, "RETURNS", ref, spec_source, ep
                ))
    return results


def _endpoint_accepts(
    raw: dict[str, Any],
    endpoints: list[EndpointMetadata],
    spec_source: str,
) -> list[RelationshipMetadata]:
    """Produce ACCEPTS relationships from requestBody ``$ref`` values."""
    results: list[RelationshipMetadata] = []
    for ep in endpoints:
        if not ep.request_body:
            continue
        source_label = f"{ep.method} {ep.path}"
        for ref in _schema_refs_from_obj(raw, ep.request_body):
            name = _schema_name(ref)
            if name:
                results.append(_make_rel(
                    source_label, name, "ACCEPTS", ref, spec_source, ep
                ))
    return results


# ---------------------------------------------------------------------------
# Schema → schema relationships
# ---------------------------------------------------------------------------

def _schema_references(
    schemas: list[SchemaMetadata],
    spec_source: str,
) -> list[RelationshipMetadata]:
    """Produce REFERENCES relationships from schema allOf/oneOf/anyOf and property refs."""
    results: list[RelationshipMetadata] = []
    for schema in schemas:
        for ref in schema.refs:
            name = _schema_name(ref)
            if name:
                results.append(_make_rel(schema.name, name, "REFERENCES", ref, spec_source))
        for prop in schema.properties:
            if prop.ref:
                name = _schema_name(prop.ref)
                if name:
                    results.append(
                        _make_rel(schema.name, name, "REFERENCES", prop.ref, spec_source)
                    )
    return results


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _schema_refs_from_obj(
    raw: dict[str, Any],
    obj: Any,
    _visited: frozenset[str] | None = None,
    _depth: int = 0,
) -> list[str]:
    """Recursively collect ``#/components/schemas/...`` refs reachable from *obj*.

    Intermediate ``$ref`` values (e.g. ``#/components/responses/...``) are
    followed once to find nested schema refs.  A depth limit and a visited set
    prevent infinite loops.
    """
    if _depth > _MAX_FOLLOW_DEPTH:
        return []
    visited: frozenset[str] = _visited or frozenset()
    refs: list[str] = []

    if isinstance(obj, dict):
        ref_val = obj.get("$ref")
        if isinstance(ref_val, str) and ref_val not in visited:
            visited = visited | {ref_val}
            if ref_val.startswith(_SCHEMA_REF_PREFIX):
                refs.append(ref_val)
            elif ref_val.startswith("#/"):
                resolved = _follow_ref(raw, ref_val)
                if resolved is not None:
                    refs.extend(
                        _schema_refs_from_obj(raw, resolved, visited, _depth + 1)
                    )
        for key, val in obj.items():
            if key != "$ref":
                refs.extend(_schema_refs_from_obj(raw, val, visited, _depth))

    elif isinstance(obj, list):
        for item in obj:
            refs.extend(_schema_refs_from_obj(raw, item, visited, _depth))

    return refs


def _follow_ref(raw: dict[str, Any], ref: str) -> dict[str, Any] | None:
    """Resolve a ``#/a/b/c`` JSON Pointer against *raw*; return ``None`` on failure."""
    if not ref.startswith("#/"):
        return None
    parts = ref[2:].split("/")
    obj: Any = raw
    for part in parts:
        if not isinstance(obj, dict) or part not in obj:
            return None
        obj = obj[part]
    return obj if isinstance(obj, dict) else None


def _schema_name(ref: str) -> str | None:
    """Extract the schema name from a ``#/components/schemas/<Name>`` ref."""
    if ref.startswith(_SCHEMA_REF_PREFIX):
        return ref[len(_SCHEMA_REF_PREFIX):]
    return None


def _make_rel(
    source: str,
    target: str,
    relationship: str,
    ref_path: str,
    spec_source: str,
    ep: EndpointMetadata | None = None,
) -> RelationshipMetadata:
    return RelationshipMetadata(
        type="relationship",
        source=source,
        target=target,
        relationship=relationship,
        spec_source=spec_source,
        endpoint_method=ep.method if ep else None,
        endpoint_path=ep.path if ep else None,
        ref_path=ref_path,
    )
