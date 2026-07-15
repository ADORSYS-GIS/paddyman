"""Build normalized security scheme entity dicts.

Pure transformation - converts SecuritySchemeMetadata records into
flat entity dictionaries.
"""
from __future__ import annotations

from typing import Any
from uuid import uuid4

from openapi_parser.models import SecuritySchemeMetadata


def build_security_scheme_entity(scheme: SecuritySchemeMetadata) -> dict[str, Any]:
    """Convert a SecuritySchemeMetadata record to a normalized entity dict."""
    entity: dict[str, Any] = {
        "id": str(uuid4()),
        "type": "SecurityScheme",
        "name": scheme.name,
        "scheme_type": scheme.type,
        "description": scheme.description,
        "source_file": scheme.spec_source,
    }

    # HTTP-specific fields
    entity["scheme"] = scheme.scheme if scheme.scheme else None
    entity["bearer_format"] = scheme.bearer_format if scheme.bearer_format else None

    # API key-specific fields
    entity["in"] = scheme.in_ if scheme.in_ else None
    entity["parameter_name"] = scheme.parameter_name if scheme.parameter_name else None

    # OpenID Connect-specific field
    entity["open_id_connect_url"] = (
        scheme.open_id_connect_url if scheme.open_id_connect_url else None
    )

    # OAuth2 flows
    entity["flows"] = scheme.flows if scheme.flows else {}

    return entity
