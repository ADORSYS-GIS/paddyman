"""Unit tests for parameter_type_relationship_builder."""
from __future__ import annotations

from java_parser.parameter_type_relationship_builder import (
    build_parameter_has_type_relationships,
)


def _parameter_entity(
    parameter_uuid: str,
    name: str,
    parameter_type: str,
    is_vararg: bool = False,
) -> dict[str, str | bool]:
    return {
        "type": "Parameter",
        "uuid": parameter_uuid,
        "name": name,
        "parameter_type": parameter_type,
        "is_vararg": is_vararg,
    }


def test_simple_parameter_type_relationship_created() -> None:
    param = _parameter_entity("param-1", "name", "String")
    rels = build_parameter_has_type_relationships([param], [])
    assert len(rels) == 1
    assert rels[0]["type"] == "HAS_TYPE"
    assert rels[0]["properties"]["parameter_name"] == "name"
    assert rels[0]["properties"]["base_type"] == "String"


def test_custom_class_parameter_type_relationship_created() -> None:
    param = _parameter_entity("param-1", "account", "Account")
    account = {"type": "Class", "name": "Account", "uuid": "account-uuid"}
    rels = build_parameter_has_type_relationships([param], [account])
    assert rels[0]["target"] == "account-uuid"
    assert "target_resolved" not in rels[0]["properties"]


def test_generic_parameter_type_relationship_created() -> None:
    param = _parameter_entity("param-1", "accounts", "List<Account>")
    list_entity = {"type": "Interface", "name": "List", "uuid": "list-uuid"}
    rels = build_parameter_has_type_relationships([param], [list_entity])
    assert rels[0]["target"] == "list-uuid"
    assert rels[0]["properties"]["is_collection"] is True
    assert rels[0]["properties"]["is_generic"] is True
    assert rels[0]["properties"]["generic_arguments"] == ["Account"]


def test_array_parameter_type_relationship_created() -> None:
    param = _parameter_entity("param-1", "names", "String[]")
    rels = build_parameter_has_type_relationships([param], [])
    assert rels[0]["target"] == "String"
    assert rels[0]["properties"]["base_type"] == "String"


def test_primitive_parameter_type_relationship_created() -> None:
    param = _parameter_entity("param-1", "count", "int")
    rels = build_parameter_has_type_relationships([param], [])
    assert rels[0]["target"] == "int"
    assert rels[0]["properties"]["base_type"] == "int"


def test_varargs_parameter_type_relationship_created() -> None:
    param = _parameter_entity("param-1", "values", "String", is_vararg=True)
    rels = build_parameter_has_type_relationships([param], [])
    assert rels[0]["target"] == "String"
    assert rels[0]["properties"]["is_varargs"] is True
    assert rels[0]["properties"]["is_collection"] is True
    assert rels[0]["properties"]["type_name"] == "String..."


def test_nested_generic_parameter_type_preserves_generic_arguments() -> None:
    param = _parameter_entity("param-1", "index", "Map<String, List<Account>>")
    map_entity = {"type": "Interface", "name": "Map", "uuid": "map-uuid"}
    rels = build_parameter_has_type_relationships([param], [map_entity])
    assert rels[0]["target"] == "map-uuid"
    assert rels[0]["properties"]["generic_arguments"] == ["String", "List<Account>"]
