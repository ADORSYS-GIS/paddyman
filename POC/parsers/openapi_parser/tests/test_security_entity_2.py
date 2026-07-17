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

    def test_oauth2_scheme_converted(self):
        from openapi_parser.models import SecuritySchemeMetadata

        build = self._import()
        scheme = SecuritySchemeMetadata(
            name="OAuth2",
            type="oauth2",
            spec_source="/specs/api.yaml",
            description="OAuth2 authentication",
            flows={
                "authorizationCode": {
                    "authorizationUrl": "https://example.com/oauth/authorize",
                    "tokenUrl": "https://example.com/oauth/token",
                    "scopes": {
                        "read": "Read access",
                        "write": "Write access",
                    },
                }
            },
        )
        entity = build(scheme)

        assert entity["type"] == "SecurityScheme"
        assert entity["name"] == "OAuth2"
        assert entity["scheme_type"] == "oauth2"
        assert entity["description"] == "OAuth2 authentication"
        assert entity["source_file"] == "/specs/api.yaml"
        assert "authorizationCode" in entity["flows"]
        assert entity["flows"]["authorizationCode"]["authorizationUrl"] == "https://example.com/oauth/authorize"
        assert entity["flows"]["authorizationCode"]["tokenUrl"] == "https://example.com/oauth/token"
        assert "read" in entity["flows"]["authorizationCode"]["scopes"]

    def test_openid_connect_scheme_converted(self):
        from openapi_parser.models import SecuritySchemeMetadata

        build = self._import()
        scheme = SecuritySchemeMetadata(
            name="OpenIDConnect",
            type="openIdConnect",
            spec_source="/specs/api.yaml",
            open_id_connect_url="https://example.com/.well-known/openid-configuration",
            description="OpenID Connect authentication",
        )
        entity = build(scheme)

        assert entity["type"] == "SecurityScheme"
        assert entity["name"] == "OpenIDConnect"
        assert entity["scheme_type"] == "openIdConnect"
        assert entity["open_id_connect_url"] == "https://example.com/.well-known/openid-configuration"
        assert entity["description"] == "OpenID Connect authentication"
        assert entity["source_file"] == "/specs/api.yaml"
        assert entity["scheme"] is None
        assert entity["in"] is None
        assert entity["flows"] == {}

    def test_minimal_scheme_all_optional_fields_none(self):
        from openapi_parser.models import SecuritySchemeMetadata

        build = self._import()
        scheme = SecuritySchemeMetadata(
            name="MinimalScheme",
            type="http",
            spec_source="/specs/api.yaml",
        )
        entity = build(scheme)

        assert entity["type"] == "SecurityScheme"
        assert entity["name"] == "MinimalScheme"
        assert entity["scheme_type"] == "http"
        assert entity["description"] is None
        assert entity["scheme"] is None
        assert entity["bearer_format"] is None
        assert entity["in"] is None
        assert entity["parameter_name"] is None
        assert entity["open_id_connect_url"] is None
        assert entity["flows"] == {}

    def test_oauth2_client_credentials_flow(self):
        from openapi_parser.models import SecuritySchemeMetadata

        build = self._import()
        scheme = SecuritySchemeMetadata(
            name="OAuth2ClientCreds",
            type="oauth2",
            spec_source="/specs/api.yaml",
            flows={
                "clientCredentials": {
                    "tokenUrl": "https://example.com/oauth/token",
                    "scopes": {},
                }
            },
        )
        entity = build(scheme)

        assert entity["type"] == "SecurityScheme"
        assert entity["name"] == "OAuth2ClientCreds"
        assert entity["scheme_type"] == "oauth2"
        assert "clientCredentials" in entity["flows"]
        assert entity["flows"]["clientCredentials"]["tokenUrl"] == "https://example.com/oauth/token"
        assert entity["flows"]["clientCredentials"]["scopes"] == {}



