"""Unit tests for method_return_type_relationship_builder."""
from __future__ import annotations

from java_parser.method_return_type_relationship_builder import build_returns_relationships


def _method_entity(method_uuid: str, name: str, return_type: str) -> dict[str, str]:
    return {
        "type": "Method",
        "uuid": method_uuid,
        "name": name,
        "return_type": return_type,
    }


def test_simple_return_type_relationship_created() -> None:
    method = _method_entity("method-1", "getName", "String")
    rels = build_returns_relationships([method], [])
    assert len(rels) == 1
    assert rels[0]["type"] == "RETURNS"
    assert rels[0]["properties"]["base_type"] == "String"
    assert rels[0]["properties"]["target_resolved"] is False


def test_custom_class_return_type_relationship_created() -> None:
    method = _method_entity("method-1", "getAccount", "Account")
    account = {"type": "Class", "name": "Account", "uuid": "account-uuid"}
    rels = build_returns_relationships([method], [account])
    assert rels[0]["target"] == "account-uuid"
    assert "target_resolved" not in rels[0]["properties"]


def test_generic_return_type_relationship_created() -> None:
    method = _method_entity("method-1", "getAccounts", "List<Account>")
    list_entity = {"type": "Interface", "name": "List", "uuid": "list-uuid"}
    rels = build_returns_relationships([method], [list_entity])
    assert rels[0]["target"] == "list-uuid"
    assert rels[0]["properties"]["is_collection"] is True
    assert rels[0]["properties"]["is_generic"] is True
    assert rels[0]["properties"]["generic_arguments"] == ["Account"]


def test_array_return_type_relationship_created() -> None:
    method = _method_entity("method-1", "getNames", "String[]")
    rels = build_returns_relationships([method], [])
    assert rels[0]["target"] == "String"
    assert rels[0]["properties"]["base_type"] == "String"


def test_primitive_return_type_relationship_created() -> None:
    method = _method_entity("method-1", "count", "int")
    rels = build_returns_relationships([method], [])
    assert rels[0]["target"] == "int"
    assert rels[0]["properties"]["base_type"] == "int"
    assert rels[0]["properties"]["is_void"] is False


def test_void_return_type_uses_singleton_void_entity() -> None:
    entities: list[dict[str, str]] = []
    method_a = _method_entity("method-1", "update", "void")
    method_b = _method_entity("method-2", "reset", "void")
    rels = build_returns_relationships([method_a, method_b], entities)
    void_entities = [e for e in entities if e.get("type") == "JavaType" and e.get("name") == "void"]
    assert len(void_entities) == 1
    assert rels[0]["target"] == void_entities[0]["uuid"]
    assert rels[1]["target"] == void_entities[0]["uuid"]
    assert rels[0]["properties"]["is_void"] is True


def test_nested_generic_return_type_preserves_generic_arguments() -> None:
    method = _method_entity("method-1", "index", "Map<String, List<Account>>")
    map_entity = {"type": "Interface", "name": "Map", "uuid": "map-uuid"}
    rels = build_returns_relationships([method], [map_entity])
    assert rels[0]["target"] == "map-uuid"
    assert rels[0]["properties"]["generic_arguments"] == ["String", "List<Account>"]
