"""Tests for Java member extraction (methods, fields, constructors, parameters)."""
from __future__ import annotations

from pathlib import Path

import pytest

from java_parser.java_ast.parser import parse_bytes
from java_parser.members.member_builder import (
    extract_file_members,
    parse_and_extract_members,
)
from java_parser.members.models import (
    ClassMembers,
    JavaConstructor,
    JavaField,
    JavaMethod,
)


# ── Test helpers ───────────────────────────────────────────────────────────────

def _members(src: str, pkg: str = "com.example") -> ClassMembers:
    """Parse *src* and return the first ClassMembers result."""
    root = parse_bytes(src.encode())
    results = extract_file_members(
        root,
        package=pkg,
        file_path="Test.java",
        repository="repo",
        module="mod",
    )
    assert results, f"No ClassMembers extracted from:\n{src}"
    return results[0]


# ── Field extraction ───────────────────────────────────────────────────────────

class TestFieldExtraction:
    def test_private_field(self) -> None:
        cm = _members("class A { private String name; }")
        assert len(cm.fields) == 1
        f = cm.fields[0]
        assert f.name == "name"
        assert f.type == "String"
        assert "private" in f.modifiers

    def test_public_static_final_field(self) -> None:
        cm = _members("class A { public static final int MAX = 100; }")
        f = cm.fields[0]
        assert f.name == "MAX"
        assert f.type == "int"
        assert "public" in f.modifiers
        assert "static" in f.modifiers
        assert "final" in f.modifiers

    def test_generic_field(self) -> None:
        cm = _members("class A { private List<String> items; }")
        f = cm.fields[0]
        assert f.name == "items"
        assert "List" in f.type

    def test_array_field(self) -> None:
        cm = _members("class A { private int[] values; }")
        f = cm.fields[0]
        assert f.name == "values"
        assert "int" in f.type

    def test_no_fields_in_empty_class(self) -> None:
        cm = _members("class A {}")
        assert cm.fields == []

    def test_multiple_fields(self) -> None:
        cm = _members("class A { private String a; protected int b; public boolean c; }")
        assert len(cm.fields) == 3
        names = {f.name for f in cm.fields}
        assert names == {"a", "b", "c"}

    def test_field_provenance(self) -> None:
        cm = _members("class A { String x; }")
        f = cm.fields[0]
        assert f.class_name == "A"
        assert f.package == "com.example"
        assert f.repository == "repo"
        assert f.module == "mod"

    def test_field_to_dict_keys(self) -> None:
        cm = _members("class A { int x; }")
        d = cm.fields[0].to_dict()
        assert d["type"] == "field"
        assert "name" in d
        assert "field_type" in d
        assert "class" in d


# ── Method extraction ──────────────────────────────────────────────────────────

