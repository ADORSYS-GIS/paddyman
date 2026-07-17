"""Build SecurityScheme entities as IR dicts.

Converts SecuritySchemeMetadata records into normalized dicts. A
Pydantic SecurityScheme model is used only to produce a stable id.
"""
from __future__ import annotations

from typing import Any

from openapi_parser.models import SecuritySchemeMetadata
from shared.models.openapi import SecurityScheme


def build_security_scheme_entity(scheme: SecuritySchemeMetadata) -> dict[str, Any]:
    """Convert a SecuritySchemeMetadata record to a normalized entity dict."""
    model = SecurityScheme.create(
        name=scheme.name,
        scheme_type=scheme.type,
        spec_source=scheme.spec_source,
        description=scheme.description,
        scheme=scheme.scheme,
        bearer_format=scheme.bearer_format,
        in_=scheme.in_,
        parameter_name=scheme.parameter_name,
        open_id_connect_url=scheme.open_id_connect_url,
        flows=scheme.flows,
    )

    return {
        "id": str(model.id),
        "type": "SecurityScheme",
        "name": scheme.name,
        "scheme_type": scheme.type,
        "description": scheme.description,
        "scheme": scheme.scheme,
        "bearer_format": scheme.bearer_format,
        "in": scheme.in_,
        "parameter_name": scheme.parameter_name,
        "open_id_connect_url": scheme.open_id_connect_url,
        "flows": scheme.flows or {},
        "source_file": scheme.spec_source,
        "source_location": f"#/components/securitySchemes/{scheme.name}",
        "source": f"openapi_parser:{scheme.spec_source}:{scheme.name}",
    }
