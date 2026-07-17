"""Unit tests for openapi_parser.security_extractor.

Covers:
- extraction of HTTP bearer security schemes
- extraction of OAuth2 security schemes with flows
- extraction of API key security schemes
- extraction of OpenID Connect security schemes
- missing components block
- missing securitySchemes key
- empty securitySchemes block
- non-dict security scheme entry skipped
- multiple security schemes extracted together
- scheme-specific field population
"""
from __future__ import annotations

from typing import Any

import pytest


# ---------------------------------------------------------------------------
# Test fixtures (raw dicts — no YAML parsing needed, pure dict tests)
# ---------------------------------------------------------------------------

_HTTP_BEARER_SCHEME: dict[str, Any] = {
    "openapi": "3.0.1",
    "info": {"title": "T", "version": "1"},
    "components": {
        "securitySchemes": {
            "BearerAuthOAuth": {
                "type": "http",
                "scheme": "bearer",
                "description": "Bearer Token. Is contained only if an OAuth2 based authentication was performed.",
            }
        }
    },
}

_OAUTH2_SCHEME: dict[str, Any] = {
    "openapi": "3.0.1",
    "info": {"title": "T", "version": "1"},
    "components": {
        "securitySchemes": {
            "OAuth2": {
                "type": "oauth2",
                "description": "OAuth2 authentication",
                "flows": {
                    "authorizationCode": {
                        "authorizationUrl": "https://example.com/oauth/authorize",
                        "tokenUrl": "https://example.com/oauth/token",
                        "scopes": {
                            "read": "Read access",
                            "write": "Write access",
                        },
                    }
                },
            }
        }
    },
}

_API_KEY_SCHEME: dict[str, Any] = {
    "openapi": "3.0.1",
    "info": {"title": "T", "version": "1"},
    "components": {
        "securitySchemes": {
            "ApiKeyAuth": {
                "type": "apiKey",
                "in": "header",
                "name": "X-API-Key",
                "description": "API key authentication",
            }
        }
    },
}

_OPENID_CONNECT_SCHEME: dict[str, Any] = {
    "openapi": "3.0.1",
    "info": {"title": "T", "version": "1"},
    "components": {
        "securitySchemes": {
            "OpenIDConnect": {
                "type": "openIdConnect",
                "openIdConnectUrl": "https://example.com/.well-known/openid-configuration",
                "description": "OpenID Connect authentication",
            }
        }
    },
}

_MULTI_SCHEMES: dict[str, Any] = {
    "openapi": "3.0.1",
    "info": {"title": "T", "version": "1"},
    "components": {
        "securitySchemes": {
            "Bearer": {
                "type": "http",
                "scheme": "bearer",
            },
            "ApiKey": {
                "type": "apiKey",
                "in": "header",
                "name": "X-API-Key",
            },
            "OAuth2": {
                "type": "oauth2",
                "flows": {
                    "clientCredentials": {
                        "tokenUrl": "https://example.com/oauth/token",
                        "scopes": {},
                    }
                },
            },
        }
    },
}

_NO_COMPONENTS: dict[str, Any] = {
    "openapi": "3.0.1",
    "info": {"title": "T", "version": "1"},
    "paths": {},
}

_NO_SECURITY_SCHEMES: dict[str, Any] = {
    "openapi": "3.0.1",
    "info": {"title": "T", "version": "1"},
    "components": {
        "schemas": {
            "MySchema": {"type": "object"}
        }
    },
}

_EMPTY_SECURITY_SCHEMES: dict[str, Any] = {
    "openapi": "3.0.1",
    "info": {"title": "T", "version": "1"},
    "components": {
        "securitySchemes": {}
    },
}

_NON_DICT_SCHEME: dict[str, Any] = {
    "openapi": "3.0.1",
    "info": {"title": "T", "version": "1"},
    "components": {
        "securitySchemes": {
            "InvalidScheme": "not a dict",
            "ValidScheme": {
                "type": "http",
                "scheme": "bearer",
            }
        }
    },
}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestExtractSecuritySchemes:
    def _import(self):
        from openapi_parser.security_extractor import extract_security_schemes
        return extract_security_schemes

    def test_http_bearer_scheme_extracted(self):
        extract = self._import()
        results = extract(_HTTP_BEARER_SCHEME, "/test.yaml")

        assert len(results) == 1
        scheme = results[0]
        assert scheme.name == "BearerAuthOAuth"
        assert scheme.type == "http"
        assert scheme.scheme == "bearer"
        assert scheme.description == "Bearer Token. Is contained only if an OAuth2 based authentication was performed."
        assert scheme.spec_source == "/test.yaml"
        assert scheme.in_ is None
        assert scheme.parameter_name is None
        assert scheme.open_id_connect_url is None
        assert scheme.flows == {}

    def test_oauth2_scheme_extracted(self):
        extract = self._import()
        results = extract(_OAUTH2_SCHEME, "/test.yaml")

        assert len(results) == 1
        scheme = results[0]
        assert scheme.name == "OAuth2"
        assert scheme.type == "oauth2"
        assert scheme.description == "OAuth2 authentication"
        assert scheme.spec_source == "/test.yaml"
        assert "authorizationCode" in scheme.flows
        assert scheme.flows["authorizationCode"]["authorizationUrl"] == "https://example.com/oauth/authorize"
        assert scheme.flows["authorizationCode"]["tokenUrl"] == "https://example.com/oauth/token"
        assert "read" in scheme.flows["authorizationCode"]["scopes"]

    def test_api_key_scheme_extracted(self):
        extract = self._import()
        results = extract(_API_KEY_SCHEME, "/test.yaml")

        assert len(results) == 1
        scheme = results[0]
        assert scheme.name == "ApiKeyAuth"
        assert scheme.type == "apikey"
        assert scheme.in_ == "header"
        assert scheme.parameter_name == "X-API-Key"
        assert scheme.description == "API key authentication"
        assert scheme.spec_source == "/test.yaml"
        assert scheme.scheme is None
        assert scheme.open_id_connect_url is None
        assert scheme.flows == {}

    def test_openid_connect_scheme_extracted(self):
        extract = self._import()
        results = extract(_OPENID_CONNECT_SCHEME, "/test.yaml")

        assert len(results) == 1
        scheme = results[0]
        assert scheme.name == "OpenIDConnect"
        assert scheme.type == "openidconnect"
        assert scheme.open_id_connect_url == "https://example.com/.well-known/openid-configuration"
        assert scheme.description == "OpenID Connect authentication"
        assert scheme.spec_source == "/test.yaml"
        assert scheme.scheme is None
        assert scheme.in_ is None
        assert scheme.flows == {}

    def test_multiple_schemes_extracted(self):
        extract = self._import()
        results = extract(_MULTI_SCHEMES, "/test.yaml")

        assert len(results) == 3
        names = {s.name for s in results}
        assert names == {"Bearer", "ApiKey", "OAuth2"}

        bearer = [s for s in results if s.name == "Bearer"][0]
        assert bearer.type == "http"
        assert bearer.scheme == "bearer"

        api_key = [s for s in results if s.name == "ApiKey"][0]
        assert api_key.type == "apikey"
        assert api_key.in_ == "header"
        assert api_key.parameter_name == "X-API-Key"

        oauth2 = [s for s in results if s.name == "OAuth2"][0]
        assert oauth2.type == "oauth2"
        assert "clientCredentials" in oauth2.flows

    def test_no_components_returns_empty_list(self):
        extract = self._import()
        results = extract(_NO_COMPONENTS, "/test.yaml")

        assert results == []

    def test_no_security_schemes_returns_empty_list(self):
        extract = self._import()
        results = extract(_NO_SECURITY_SCHEMES, "/test.yaml")

        assert results == []

    def test_empty_security_schemes_returns_empty_list(self):
        extract = self._import()
        results = extract(_EMPTY_SECURITY_SCHEMES, "/test.yaml")

        assert results == []

    def test_non_dict_scheme_skipped(self):
        extract = self._import()
        results = extract(_NON_DICT_SCHEME, "/test.yaml")

        assert len(results) == 1
        assert results[0].name == "ValidScheme"
        assert results[0].type == "http"
