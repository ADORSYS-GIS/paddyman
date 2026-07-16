"""Unit tests for type_parsing_helpers."""
from __future__ import annotations

import pytest

from java_parser.type_parsing_helpers import parse_type_declaration


class TestParseTypeDeclaration:
    """Tests for type string parsing logic."""

    def test_simple_type(self):
        """Parse simple type like 'String'."""
        base, is_coll, is_gen, args = parse_type_declaration("String")
        assert base == "String"
        assert not is_coll
        assert not is_gen
        assert args == []

    def test_primitive_type(self):
        """Parse primitive type like 'int'."""
        base, is_coll, is_gen, args = parse_type_declaration("int")
        assert base == "int"
        assert not is_coll
        assert not is_gen

    def test_array_type(self):
        """Parse array type like 'String[]'."""
        base, is_coll, is_gen, args = parse_type_declaration("String[]")
        assert base == "String"
        assert not is_coll
        assert not is_gen

    def test_generic_type(self):
        """Parse generic type like 'List<String>'."""
        base, is_coll, is_gen, args = parse_type_declaration("List<String>")
        assert base == "List"
        assert is_coll
        assert is_gen
        assert args == ["String"]

    def test_generic_with_multiple_args(self):
        """Parse generic type with multiple arguments like 'Map<String, Integer>'."""
        base, is_coll, is_gen, args = parse_type_declaration("Map<String, Integer>")
        assert base == "Map"
        assert is_coll
        assert is_gen
        assert args == ["String", "Integer"]

    def test_nested_generic(self):
        """Parse nested generic like 'Map<String, List<Account>>'."""
        base, is_coll, is_gen, args = parse_type_declaration(
            "Map<String, List<Account>>"
        )
        assert base == "Map"
        assert is_coll
        assert is_gen
        assert len(args) >= 1

    def test_set_type(self):
        """Parse Set collection type."""
        base, is_coll, is_gen, args = parse_type_declaration("Set<Account>")
        assert base == "Set"
        assert is_coll
        assert is_gen
        assert args == ["Account"]

    def test_generic_array(self):
        """Parse generic array like 'List<String>[]'."""
        base, is_coll, is_gen, args = parse_type_declaration("List<String>[]")
        assert base == "List"
        assert is_coll
        assert is_gen
        assert args == ["String"]
