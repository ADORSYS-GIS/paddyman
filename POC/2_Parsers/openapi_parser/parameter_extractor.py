"""OpenAPI parameter extractor.

Pure function module — no I/O.  Accepts a parsed OpenAPI document (Python
dict) and returns structured :class:`~openapi_parser.models.ParameterMetadata`
records, one per entry in ``components.parameters``.

Intentionally excluded:
- ``$ref`` resolution / dereferencing
- inline parameter extraction (handled by endpoint extractor)
- API relationship analysis
"""
from __future__ import annotations

import logging
from typing import Any

from openapi_parser.models import ParameterMetadata

logger = logging.getLogger(__name__)


def extract_parameters(
    raw: dict[str, Any],
    spec_source: str,
) -> list[ParameterMetadata]:
    """Extract all reusable parameter definitions from ``components.parameters``.

    Args:
        raw:        Parsed OpenAPI YAML document (top-level mapping).
        spec_source: File path or repository identifier of the source spec.

    Returns:
        List of :class:`~openapi_parser.models.ParameterMetadata`, one per
        entry under ``components.parameters``.  Returns an empty list when the
        section is absent or not a mapping.
    """
    components = raw.get("components")
    if not isinstance(components, dict):
        logger.debug("No 'components' block found in spec from %s", spec_source)
        return []

    params_block = components.get("parameters")
    if not isinstance(params_block, dict):
        logger.debug("No 'components.parameters' block found in spec from %s", spec_source)
        return []

    results: list[ParameterMetadata] = []
    for param_name, param_def in params_block.items():
        if not isinstance(param_def, dict):
            logger.debug("Skipping non-dict parameter entry '%s' in %s", param_name, spec_source)
            continue
        results.append(_build_parameter(str(param_name), param_def, spec_source))

    logger.debug("Extracted %d parameter(s) from %s", len(results), spec_source)
    return results


def _build_parameter(
    name: str,
    param: dict[str, Any],
    spec_source: str,
) -> ParameterMetadata:
    """Build a :class:`ParameterMetadata` from a single parameter definition dict.

    Args:
        name:        Parameter name (key from components.parameters).
        param:       Parameter definition object.
        spec_source: File path or repository identifier of the source spec.

    Returns:
        Structured parameter metadata record.
    """
    location: str = str(param.get("in", ""))
    required: bool = bool(param.get("required", False))
    description: str | None = param.get("description") or None
    deprecated: bool = bool(param.get("deprecated", False))
    example: Any | None = param.get("example")

    # Extract schema information
    schema = param.get("schema") or {}
    schema_type: str | None = schema.get("type") or None
    schema_ref: str | None = schema.get("$ref") or None
    format_val: str | None = schema.get("format") or None

    # Extract enum values if present
    enum_raw = schema.get("enum")
    enum_values: list[Any] = list(enum_raw) if isinstance(enum_raw, list) else []

    return ParameterMetadata(
        name=name,
        location=location,
        required=required,
        description=description,
        schema_type=schema_type,
        schema_ref=schema_ref,
        format=format_val,
        deprecated=deprecated,
        example=example,
        enum_values=enum_values,
        spec_source=spec_source,
    )
