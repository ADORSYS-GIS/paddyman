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

class TestMethodExtraction:
    def test_simple_void_method(self) -> None:
        cm = _members("class A { public void run() {} }")
        assert len(cm.methods) == 1
        m = cm.methods[0]
        assert m.name == "run"
        assert m.return_type == "void"
        assert "public" in m.modifiers

    def test_method_with_return_type(self) -> None:
        cm = _members("class A { public String getName() { return null; } }")
        m = cm.methods[0]
        assert m.name == "getName"
        assert m.return_type == "String"

    def test_method_with_parameters(self) -> None:
        cm = _members("class A { public void add(String key, int val) {} }")
        m = cm.methods[0]
        assert len(m.parameters) == 2
        assert m.parameters[0].name == "key"
        assert m.parameters[0].type == "String"
        assert m.parameters[1].name == "val"
        assert m.parameters[1].type == "int"

    def test_method_no_parameters(self) -> None:
        cm = _members("class A { void reset() {} }")
        assert cm.methods[0].parameters == []

    def test_private_method(self) -> None:
        cm = _members("class A { private void helper() {} }")
        assert "private" in cm.methods[0].modifiers

    def test_static_method(self) -> None:
        cm = _members("class A { public static int count() { return 0; } }")
        m = cm.methods[0]
        assert "static" in m.modifiers
        assert m.return_type == "int"

    def test_abstract_method(self) -> None:
        cm = _members("abstract class A { public abstract void process(); }")
        m = cm.methods[0]
        assert "abstract" in m.modifiers

    def test_generic_return_type(self) -> None:
        cm = _members("class A { public List<String> getAll() { return null; } }")
        assert "List" in cm.methods[0].return_type

