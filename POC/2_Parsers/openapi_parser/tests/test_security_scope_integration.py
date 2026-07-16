"""Integration-style tests for security extraction and relationship wiring."""
from __future__ import annotations

from openapi_parser.endpoint_payload_linker import link_endpoint_payload_entities
from openapi_parser.relationship_builder import build_openapi_relationships


def test_secured_endpoints_get_requires_security_relationships() -> None:
    raw = {
        "security": [{"BearerAuth": []}],
        "paths": {
            "/payments": {"post": {"responses": {"201": {"description": "ok"}}}},
            "/public": {"get": {"security": [], "responses": {"200": {"description": "ok"}}}},
        },
    }
    entities = [
        {"id": "ep-1", "type": "Endpoint", "path": "/payments", "method": "POST", "parameters": []},
        {"id": "ep-2", "type": "Endpoint", "path": "/public", "method": "GET", "parameters": []},
        {"id": "sec-1", "type": "SecurityScheme", "name": "BearerAuth"},
    ]

    link_endpoint_payload_entities(entities, raw, "spec.yaml")
    relationships = build_openapi_relationships(entities)

    secure_rels = [
        rel for rel in relationships if rel["type"] == "REQUIRES_SECURITY" and rel["source_entity_id"] == "ep-1"
    ]
    public_rels = [
        rel for rel in relationships if rel["type"] == "REQUIRES_SECURITY" and rel["source_entity_id"] == "ep-2"
    ]

    assert len(secure_rels) == 1
    assert public_rels == []


def test_oauth_scopes_become_entities_and_scope_relationships() -> None:
    raw = {
        "paths": {
            "/payments": {
                "post": {
                    "operationId": "initiatePayment",
                    "security": [{"OAuth2": ["payments:write", "payments:read"]}],
                    "responses": {"201": {"description": "ok"}},
                }
            }
        }
    }
    entities = [
        {"id": "ep-1", "type": "Endpoint", "path": "/payments", "method": "POST", "parameters": []},
        {"id": "sec-1", "type": "SecurityScheme", "name": "OAuth2"},
    ]

    link_endpoint_payload_entities(entities, raw, "spec.yaml")
    relationships = build_openapi_relationships(entities)

    scope_entities = [entity for entity in entities if entity.get("type") == "Scope"]
    scope_rels = [rel for rel in relationships if rel["type"] == "REQUIRES_SCOPE"]
    op_security = [
        rel for rel in relationships if rel["type"] == "REQUIRES_SECURITY" and rel["properties"].get("operation_id") == "initiatePayment"
    ]

    assert sorted(entity["name"] for entity in scope_entities) == ["payments:read", "payments:write"]
    assert len(scope_rels) >= 2
    assert len(op_security) == 1
