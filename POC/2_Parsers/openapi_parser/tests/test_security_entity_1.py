"""Unit tests for openapi_parser.entity_builder.

Covers:
- converting EndpointMetadata to entity dict
- all fields present in output
- optional fields as None when absent
- parameters list conversion
- type field is "Endpoint" (capitalized)
"""
from __future__ import annotations

import pytest

class TestBuildSecuritySchemeEntity:
    def _import(self):
        from openapi_parser.entity_builder import build_security_scheme_entity
        return build_security_scheme_entity

    def test_http_bearer_scheme_converted(self):
        from openapi_parser.models import SecuritySchemeMetadata

        build = self._import()
        scheme = SecuritySchemeMetadata(
            name="BearerAuthOAuth",
            type="http",
            spec_source="/specs/payment.yaml",
            scheme="bearer",
            description="Bearer Token. Is contained only if an OAuth2 based authentication was performed.",
        )
        entity = build(scheme)

        assert entity["type"] == "SecurityScheme"
        assert entity["name"] == "BearerAuthOAuth"
        assert entity["scheme_type"] == "http"
        assert entity["scheme"] == "bearer"
        assert entity["description"] == "Bearer Token. Is contained only if an OAuth2 based authentication was performed."
        assert entity["source_file"] == "/specs/payment.yaml"
        assert entity["bearer_format"] is None
        assert entity["in"] is None
        assert entity["parameter_name"] is None
        assert entity["open_id_connect_url"] is None
        assert entity["flows"] == {}

    def test_http_bearer_with_format(self):
        from openapi_parser.models import SecuritySchemeMetadata

        build = self._import()
        scheme = SecuritySchemeMetadata(
            name="JwtBearer",
            type="http",
            spec_source="/specs/api.yaml",
            scheme="bearer",
            bearer_format="JWT",
        )
        entity = build(scheme)

        assert entity["type"] == "SecurityScheme"
        assert entity["name"] == "JwtBearer"
        assert entity["scheme_type"] == "http"
        assert entity["scheme"] == "bearer"
        assert entity["bearer_format"] == "JWT"

    def test_api_key_scheme_converted(self):
        from openapi_parser.models import SecuritySchemeMetadata

        build = self._import()
        scheme = SecuritySchemeMetadata(
            name="ApiKeyAuth",
            type="apiKey",
            spec_source="/specs/api.yaml",
            in_="header",
            parameter_name="X-API-Key",
            description="API key authentication",
        )
        entity = build(scheme)

        assert entity["type"] == "SecurityScheme"
        assert entity["name"] == "ApiKeyAuth"
        assert entity["scheme_type"] == "apiKey"
        assert entity["in"] == "header"
        assert entity["parameter_name"] == "X-API-Key"
        assert entity["description"] == "API key authentication"
        assert entity["source_file"] == "/specs/api.yaml"
        assert entity["scheme"] is None
        assert entity["bearer_format"] is None
        assert entity["open_id_connect_url"] is None
        assert entity["flows"] == {}

