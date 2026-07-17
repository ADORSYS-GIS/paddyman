"""Unit tests for operation and tag relationship builder."""
from __future__ import annotations

from openapi_parser.operation_relationships import build_operation_relationships


def test_builds_implements_operation_relationship() -> None:
    entities = [
        {
            "id": "ep-1",
            "type": "Endpoint",
            "method": "POST",
            "path": "/payments",
            "operation_match_key": "operation:POST:/payments",
        },
        {
            "id": "op-1",
            "type": "Operation",
            "match_key": "operation:POST:/payments",
            "properties": {"tags": ["payments"]},
        },
        {"id": "tag-1", "type": "Tag", "name": "payments", "properties": {}},
    ]

    relationships = build_operation_relationships(entities)

    assert any(rel["type"] == "IMPLEMENTS_OPERATION" for rel in relationships)
    assert any(rel["type"] == "TAGGED_AS" for rel in relationships)


def test_skips_relationships_when_targets_missing() -> None:
    entities = [{"id": "ep-1", "type": "Endpoint", "operation_match_key": "operation:GET:/missing"}]

    relationships = build_operation_relationships(entities)

    assert relationships == []
