"""$ref resolution utility functions.

Pure functions for working with $ref strings - pattern matching,
traversal, and metadata creation.
"""
from __future__ import annotations

import re
from typing import Any

from openapi_parser.ref_metadata import RefMetadata, SchemaRefInfo

_INTERNAL_REF_PATTERN = re.compile(r"^#/")


def is_external_ref(ref_path: str) -> bool:
    """Check if $ref points to external file or URL.

    External refs are any refs that don't start with #/ - they reference
    another document via URL, absolute path, or relative path.

    Examples:
        >>> is_external_ref("#/components/schemas/Account")
        False
        >>> is_external_ref("./common.yaml#/components/schemas/Address")
        True
        >>> is_external_ref("primitives.yaml#/components/schemas/Max35Text")
        True
        >>> is_external_ref("https://example.com/spec.yaml#/definitions/User")
        True

    Args:
        ref_path: The $ref string to check.

    Returns:
        True if the ref is external, False otherwise.
    """
    return not ref_path.startswith("#/")


def is_internal_ref(ref_path: str) -> bool:
    """Check if $ref is an internal JSON Pointer.

    Internal refs start with #/ and point within the same document.

    Examples:
        >>> is_internal_ref("#/components/schemas/Account")
        True
        >>> is_internal_ref("./common.yaml#/components/schemas/Address")
        False

    Args:
        ref_path: The $ref string to check.

    Returns:
        True if the ref is internal, False otherwise.
    """
    return bool(_INTERNAL_REF_PATTERN.match(ref_path))


def collect_refs_from_schema(schema: Any) -> list[str]:
    """Recursively collect all $ref paths from a schema definition.

    Traverses the schema object tree and extracts all $ref strings,
    including those in properties, allOf, oneOf, anyOf, items, etc.

    Args:
        schema: Schema object (dict, list, or primitive).

    Returns:
        List of all $ref strings found in the schema.

    Example:
        >>> schema = {
        ...     "type": "object",
        ...     "properties": {
        ...         "address": {"$ref": "#/components/schemas/Address"},
        ...         "currency": {"$ref": "#/components/schemas/Currency"}
        ...     },
        ...     "allOf": [{"$ref": "#/components/schemas/Base"}]
        ... }
        >>> refs = collect_refs_from_schema(schema)
        >>> len(refs)
        3
    """
    refs: list[str] = []

    if isinstance(schema, dict):
        if "$ref" in schema:
            refs.append(str(schema["$ref"]))

        for key, value in schema.items():
            if key != "$ref":
                refs.extend(collect_refs_from_schema(value))

    elif isinstance(schema, list):
        for item in schema:
            refs.extend(collect_refs_from_schema(item))

    return refs


def create_schema_ref_info(
    schema_def: dict[str, Any],
    ref_metadata: RefMetadata | None = None,
) -> SchemaRefInfo:
    """Create complete $ref tracking info for a schema.

    Analyzes the schema definition and builds a SchemaRefInfo record
    containing all $ref tracking data.

    Args:
        schema_def: The schema definition dict.
        ref_metadata: Optional metadata if this schema is itself a reference.

    Returns:
        SchemaRefInfo instance with complete tracking data.
    """
    info = SchemaRefInfo()

    # If this schema is a reference to another schema
    if ref_metadata:
        info.is_reference = True
        info.ref_path = ref_metadata.ref_path
        info.dereferenced = ref_metadata.dereferenced
        if ref_metadata.circular:
            info.circular_refs.append(ref_metadata.ref_path)

    # Collect all refs within this schema
    all_refs = collect_refs_from_schema(schema_def)
    info.refs = all_refs

    # Separate external refs
    info.external_refs = [ref for ref in all_refs if is_external_ref(ref)]

    return info
