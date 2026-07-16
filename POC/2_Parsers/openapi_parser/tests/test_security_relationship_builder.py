"""Unit tests for SecurityRelationshipBuilder."""
from __future__ import annotations

from openapi_parser.security_relationship_builder import SecurityRelationshipBuilder


def test_endpoint_requires_single_security_scheme() -> None:
    entities = [
        {
            "id": "ep-1",
            "type": "Endpoint",
            "path": "/v1/payments",
            "method": "POST",
            "security_requirements": [{"scheme_name": "BearerAuth", "scopes": [], "required": True}],
        },
        {"id": "sec-1", "type": "SecurityScheme", "name": "BearerAuth"},
    ]

    relationships = SecurityRelationshipBuilder().build(entities)
    requires = [rel for rel in relationships if rel["type"] == "REQUIRES_SECURITY"]

    assert len(requires) == 1
    assert requires[0]["source_entity_id"] == "ep-1"
    assert requires[0]["target_entity_id"] == "sec-1"
    assert requires[0]["properties"]["endpoint_method"] == "POST"


def test_endpoint_and_operation_require_security_with_scopes() -> None:
    entities = [
        {
            "id": "ep-1",
            "type": "Endpoint",
            "path": "/v1/payments",
            "method": "POST",
            "security_requirements": [{"scheme_name": "OAuth2", "scopes": ["payments:write"], "required": True}],
        },
        {
            "id": "op-1",
            "type": "Operation",
            "name": "initiatePayment",
            "properties": {"operation_id": "initiatePayment"},
            "security_requirements": [{"scheme_name": "OAuth2", "scopes": ["payments:write"], "required": True}],
        },
        {"id": "sec-1", "type": "SecurityScheme", "name": "OAuth2"},
        {"id": "scope-1", "type": "Scope", "name": "payments:write"},
    ]

    relationships = SecurityRelationshipBuilder().build(entities)
    requires_security = [rel for rel in relationships if rel["type"] == "REQUIRES_SECURITY"]
    requires_scope = [rel for rel in relationships if rel["type"] == "REQUIRES_SCOPE"]

    assert len(requires_security) == 2
    assert len(requires_scope) == 2
    assert any(rel["source_entity_id"] == "ep-1" for rel in requires_scope)
    assert any(rel["source_entity_id"] == "op-1" for rel in requires_scope)


def test_multiple_security_schemes_and_optional_flag_preserved() -> None:
    entities = [
        {
            "id": "ep-1",
            "type": "Endpoint",
            "path": "/v1/payments",
            "method": "POST",
            "security_requirements": [
                {
                    "scheme_name": "BearerAuth",
                    "scopes": [],
                    "required": False,
                    "optional": True,
                    "logic": "AND",
                    "alternatives": 2,
                },
                {
                    "scheme_name": "ApiKeyAuth",
                    "scopes": [],
                    "required": False,
                    "optional": True,
                    "logic": "AND",
                    "alternatives": 2,
                },
            ],
        },
        {"id": "sec-1", "type": "SecurityScheme", "name": "BearerAuth"},
        {"id": "sec-2", "type": "SecurityScheme", "name": "ApiKeyAuth"},
    ]

    relationships = SecurityRelationshipBuilder().build(entities)
    requires_security = [rel for rel in relationships if rel["type"] == "REQUIRES_SECURITY"]

    assert len(requires_security) == 2
    assert all(rel["properties"]["optional"] is True for rel in requires_security)
    assert all(rel["properties"]["logic"] == "AND" for rel in requires_security)
