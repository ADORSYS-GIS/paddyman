"""OpenAPI security scheme extractor.

Pure function module — no I/O.  Accepts a parsed OpenAPI document (Python
dict) and returns structured :class:`~openapi_parser.models.SecuritySchemeMetadata`
records, one per entry in ``components.securitySchemes``.

Supported scheme types: ``http``, ``apiKey``, ``oauth2``, ``openIdConnect``.

Intentionally excluded:
- global or operation-level security requirement resolution
- token/credential generation
"""
from __future__ import annotations

import logging
from typing import Any

from openapi_parser.models import SecuritySchemeMetadata

logger = logging.getLogger(__name__)


def extract_security_schemes(
    raw: dict[str, Any],
    spec_source: str,
) -> list[SecuritySchemeMetadata]:
    """Extract all security scheme definitions from ``components.securitySchemes``.

    Args:
        raw:         Parsed OpenAPI YAML document (top-level mapping).
        spec_source: File path or repository identifier of the source spec.

    Returns:
        List of :class:`~openapi_parser.models.SecuritySchemeMetadata`, one per
        entry under ``components.securitySchemes``.  Returns an empty list when
        the section is absent or not a mapping.
    """
    components = raw.get("components")
    if not isinstance(components, dict):
        logger.debug("No 'components' block found in spec from %s", spec_source)
        return []

    schemes_block = components.get("securitySchemes")
    if not isinstance(schemes_block, dict):
        logger.debug("No 'components.securitySchemes' block found in spec from %s", spec_source)
        return []

    results: list[SecuritySchemeMetadata] = []
    for scheme_name, scheme_def in schemes_block.items():
        if not isinstance(scheme_def, dict):
            logger.debug(
                "Skipping non-dict security scheme '%s' in %s", scheme_name, spec_source
            )
            continue
        results.append(_build_scheme(str(scheme_name), scheme_def, spec_source))

    logger.debug("Extracted %d security scheme(s) from %s", len(results), spec_source)
    return results


def _build_scheme(
    name: str,
    scheme: dict[str, Any],
    spec_source: str,
) -> SecuritySchemeMetadata:
    """Build a :class:`SecuritySchemeMetadata` from a single scheme definition dict."""
    scheme_type: str = str(scheme.get("type", "")).lower()
    description: str | None = scheme.get("description") or None

    # http-specific fields
    http_scheme: str | None = scheme.get("scheme") or None
    bearer_format: str | None = scheme.get("bearerFormat") or None

    # apiKey-specific fields
    in_: str | None = scheme.get("in") or None
    parameter_name: str | None = scheme.get("name") or None

    # openIdConnect-specific
    oidc_url: str | None = scheme.get("openIdConnectUrl") or None

    # oauth2 flows
    flows_raw = scheme.get("flows")
    flows: dict[str, Any] = dict(flows_raw) if isinstance(flows_raw, dict) else {}

    return SecuritySchemeMetadata(
        name=name,
        type=scheme_type,
        spec_source=spec_source,
        scheme=http_scheme,
        bearer_format=bearer_format,
        in_=in_,
        parameter_name=parameter_name,
        open_id_connect_url=oidc_url,
        description=description,
        flows=flows,
    )
