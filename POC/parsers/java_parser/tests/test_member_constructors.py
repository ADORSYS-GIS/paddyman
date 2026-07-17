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

class TestConstructorExtraction:
    def test_default_constructor_not_extracted(self) -> None:
        # Implicit default constructor has no AST node
        cm = _members("class A {}")
        assert cm.constructors == []

    def test_explicit_constructor(self) -> None:
        cm = _members("class A { public A() {} }")
        assert len(cm.constructors) == 1
        c = cm.constructors[0]
        assert c.name == "A"
        assert "public" in c.modifiers
        assert c.parameters == []

    def test_constructor_with_parameters(self) -> None:
        cm = _members("class A { public A(String name, int age) {} }")
        c = cm.constructors[0]
        assert len(c.parameters) == 2
        assert c.parameters[0].name == "name"
        assert c.parameters[0].type == "String"
        assert c.parameters[1].name == "age"

    def test_multiple_constructors(self) -> None:
        src = "class A { public A() {} public A(String s) {} }"
        cm = _members(src)
        assert len(cm.constructors) == 2

    def test_constructor_provenance(self) -> None:
        cm = _members("class A { A() {} }")
        c = cm.constructors[0]
        assert c.class_name == "A"
        assert c.package == "com.example"

    def test_constructor_location_set(self) -> None:
        cm = _members("class A { A() {} }")
        assert cm.constructors[0].location.start_line >= 0

    def test_constructor_to_dict_keys(self) -> None:
        cm = _members("class A { A() {} }")
        d = cm.constructors[0].to_dict()
        assert d["type"] == "constructor"
        assert "parameters" in d
        assert "class" in d


# ── Parameter extraction ───────────────────────────────────────────────────────

class TestParameterExtraction:
    def test_primitive_parameter(self) -> None:
        cm = _members("class A { void m(int x) {} }")
        p = cm.methods[0].parameters[0]
        assert p.name == "x"
        assert p.type == "int"

    def test_generic_parameter(self) -> None:
        cm = _members("class A { void m(List<String> items) {} }")
        p = cm.methods[0].parameters[0]
        assert p.name == "items"
        assert "List" in p.type

    def test_array_parameter(self) -> None:
        cm = _members("class A { void m(int[] arr) {} }")
        p = cm.methods[0].parameters[0]
        assert "int" in p.type
        assert p.name == "arr"

    def test_parameter_to_dict(self) -> None:
        cm = _members("class A { void m(String s) {} }")
        d = cm.methods[0].parameters[0].to_dict()
        assert "name" in d
        assert "type" in d
        assert "is_vararg" in d

    def test_multiple_parameters_order_preserved(self) -> None:
        cm = _members("class A { void m(String a, int b, boolean c) {} }")
        params = cm.methods[0].parameters
        assert [p.name for p in params] == ["a", "b", "c"]


# ── Multiple classes per file ──────────────────────────────────────────────────

