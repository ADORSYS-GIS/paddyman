"""Unit tests for field_type_relationship_builder."""
from __future__ import annotations

import pytest

from java_parser.field_type_relationship_builder import build_has_type_relationships


class TestBuildHasTypeRelationships:
    """Tests for HAS_TYPE relationship building."""

    @pytest.fixture
    def string_type_entity(self):
        return {
            "type": "Class",
            "name": "String",
            "uuid": "uuid-string-type",
        }

    @pytest.fixture
    def account_type_entity(self):
        return {
            "type": "Class",
            "name": "Account",
            "uuid": "uuid-account-class",
        }

    @pytest.fixture
    def list_type_entity(self):
        return {
            "type": "Interface",
            "name": "List",
            "uuid": "uuid-list-interface",
        }

    def test_simple_field_type_relationship(self, string_type_entity):
        field_entity = {
            "type": "Field",
            "name": "count",
            "field_type": "int",
            "uuid": "uuid-field-count",
        }
        rels = build_has_type_relationships([field_entity], [field_entity])
        assert len(rels) == 1
        assert rels[0]["type"] == "HAS_TYPE"
        assert rels[0]["properties"]["target_resolved"] is False

    def test_custom_type_field_relationship(self, account_type_entity):
        field_entity = {
            "type": "Field",
            "name": "account",
            "field_type": "Account",
            "uuid": "uuid-field-account",
        }
        rels = build_has_type_relationships(
            [field_entity], [account_type_entity, field_entity]
        )
        assert len(rels) == 1
        assert rels[0]["target"] == "uuid-account-class"

    def test_generic_field_relationship(
        self, list_type_entity, account_type_entity
    ):
        field_entity = {
            "type": "Field",
            "name": "accounts",
            "field_type": "List<Account>",
            "uuid": "uuid-field-accounts",
        }
        rels = build_has_type_relationships(
            [field_entity], [list_type_entity, account_type_entity, field_entity]
        )
        assert rels[0]["properties"]["is_generic"]
        assert rels[0]["properties"]["generic_arguments"] == ["Account"]

    def test_array_field_relationship(self, string_type_entity):
        field_entity = {
            "type": "Field",
            "name": "names",
            "field_type": "String[]",
            "uuid": "uuid-field-names",
        }
        rels = build_has_type_relationships([field_entity], [field_entity])
        assert rels[0]["properties"]["base_type"] == "String"

    def test_multiple_fields(self, account_type_entity):
        field1 = {
            "type": "Field",
            "name": "id",
            "field_type": "String",
            "uuid": "uuid-field-id",
        }
        field2 = {
            "type": "Field",
            "name": "account",
            "field_type": "Account",
            "uuid": "uuid-field-account",
        }
        rels = build_has_type_relationships(
            [field1, field2], [account_type_entity, field1, field2]
        )
        assert len(rels) == 2

    def test_skip_non_field_entities(self):
        class_entity = {"type": "Class", "name": "MyClass", "uuid": "uuid-class"}
        rels = build_has_type_relationships([class_entity], [class_entity])
        assert rels == []

    def test_field_missing_uuid_skipped(self):
        field_entity = {"type": "Field", "name": "name", "field_type": "String"}
        rels = build_has_type_relationships([field_entity], [field_entity])
        assert rels == []

    def test_field_missing_type_skipped(self):
        field_entity = {"type": "Field", "name": "name", "uuid": "uuid-field"}
        rels = build_has_type_relationships([field_entity], [field_entity])
        assert rels == []

    def test_empty_field_list(self):
        assert build_has_type_relationships([], []) == []

