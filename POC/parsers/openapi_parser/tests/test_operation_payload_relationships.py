"""Tests for operation-level payload/parameter relationships."""
from __future__ import annotations

from uuid import uuid4

from openapi_parser.relationship_builder import build_openapi_relationships


def test_operation_has_parameter_relationship():
    op_id = str(uuid4())
    param_id = str(uuid4())

    entities = [
        {
            "id": op_id,
            "type": "Operation",
            "properties": {"path": "/payments", "method": "POST"},
            "parameters": [{"name": "paymentId", "location": "path", "required": True}],
        },
        {"id": param_id, "type": "Parameter", "name": "paymentId", "in": "path"},
    ]

    relationships = build_openapi_relationships(entities)
    param_rels = [r for r in relationships if r["type"] == "HAS_PARAMETER"]
    assert len(param_rels) == 1
    assert param_rels[0]["source_entity_id"] == op_id
    assert param_rels[0]["target_entity_id"] == param_id


def test_operation_has_request_body_relationship():
    op_id = str(uuid4())
    rb_id = str(uuid4())

    entities = [
        {"id": op_id, "type": "Operation", "properties": {"path": "/items", "method": "POST"}, "request_body_match_key": "rb:1", "request_body_required": True},
        {"id": rb_id, "type": "RequestBody", "match_key": "rb:1"},
    ]

    relationships = build_openapi_relationships(entities)
    rb_rels = [r for r in relationships if r["type"] == "HAS_REQUEST_BODY"]
    assert len(rb_rels) == 1
    assert rb_rels[0]["source_entity_id"] == op_id
    assert rb_rels[0]["target_entity_id"] == rb_id


def test_operation_has_response_relationship():
    op_id = str(uuid4())
    resp_id = str(uuid4())

    entities = [
        {"id": op_id, "type": "Operation", "properties": {"path": "/items", "method": "GET"}, "response_match_keys": {"200": "resp:ok"}},
        {"id": resp_id, "type": "Response", "match_key": "resp:ok", "schema_refs": {}},
    ]

    relationships = build_openapi_relationships(entities)
    resp_rels = [r for r in relationships if r["type"] == "HAS_RESPONSE"]
    assert len(resp_rels) == 1
    assert resp_rels[0]["source_entity_id"] == op_id
    assert resp_rels[0]["target_entity_id"] == resp_id
