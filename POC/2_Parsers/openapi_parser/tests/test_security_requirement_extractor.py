"""Unit tests for security requirement extraction precedence and scope discovery."""
from __future__ import annotations

from openapi_parser.security_requirement_extractor import extract_security_requirements


def _single_endpoint_links(raw: dict) -> tuple[list[dict], list[dict], list[dict]]:
    return extract_security_requirements(raw, "spec.yaml")


def test_global_security_applies_when_no_override() -> None:
    raw = {
        "security": [{"BearerAuth": []}],
        "paths": {"/payments": {"post": {"responses": {"201": {"description": "ok"}}}}},
    }

    scopes, endpoint_links, operation_links = _single_endpoint_links(raw)

    assert scopes == []
    assert endpoint_links[0]["security_requirements"][0]["scheme_name"] == "BearerAuth"
    assert operation_links[0]["security_requirements"][0]["scheme_name"] == "BearerAuth"


def test_operation_security_overrides_global_security() -> None:
    raw = {
        "security": [{"BearerAuth": []}],
        "paths": {
            "/payments": {
                "post": {
                    "security": [{"ApiKeyAuth": []}],
                    "responses": {"201": {"description": "ok"}},
                }
            }
        },
    }

    _, endpoint_links, operation_links = _single_endpoint_links(raw)

    assert endpoint_links[0]["security_requirements"][0]["scheme_name"] == "ApiKeyAuth"
    assert operation_links[0]["security_requirements"][0]["scheme_name"] == "ApiKeyAuth"


def test_multiple_schemes_and_logic_preserved() -> None:
    raw = {
        "paths": {
            "/payments": {
                "post": {
                    "security": [{"BearerAuth": [], "ApiKeyAuth": []}],
                    "responses": {"201": {"description": "ok"}},
                }
            }
        }
    }

    _, endpoint_links, _ = _single_endpoint_links(raw)
    reqs = endpoint_links[0]["security_requirements"]

    assert len(reqs) == 2
    assert all(req["logic"] == "AND" for req in reqs)


def test_oauth2_scopes_extracted_as_unique_scope_entities() -> None:
    raw = {
        "paths": {
            "/payments": {
                "post": {
                    "security": [{"OAuth2": ["payments:write", "payments:read"]}],
                    "responses": {"201": {"description": "ok"}},
                }
            }
        }
    }

    scopes, endpoint_links, _ = _single_endpoint_links(raw)

    scope_names = [entity["name"] for entity in scopes]
    assert scope_names == ["payments:read", "payments:write"]
    assert endpoint_links[0]["security_requirements"][0]["scopes"] == [
        "payments:write",
        "payments:read",
    ]


def test_public_operation_with_empty_security_is_not_secured() -> None:
    raw = {
        "security": [{"BearerAuth": []}],
        "paths": {
            "/public": {
                "get": {
                    "security": [],
                    "responses": {"200": {"description": "ok"}},
                }
            }
        },
    }

    _, endpoint_links, operation_links = _single_endpoint_links(raw)

    assert endpoint_links[0]["security_requirements"] == []
    assert operation_links[0]["security_requirements"] == []
