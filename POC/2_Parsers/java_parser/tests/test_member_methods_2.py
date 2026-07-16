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
    def test_multiple_methods(self) -> None:
        src = "class A { void a() {} void b() {} void c() {} }"
        cm = _members(src)
        assert len(cm.methods) == 3
        names = {m.name for m in cm.methods}
        assert names == {"a", "b", "c"}

    def test_overloaded_methods(self) -> None:
        src = "class A { void process(String s) {} void process(int i) {} }"
        cm = _members(src)
        assert len(cm.methods) == 2
        names = [m.name for m in cm.methods]
        assert names.count("process") == 2

    def test_method_provenance(self) -> None:
        cm = _members("class A { void m() {} }")
        m = cm.methods[0]
        assert m.class_name == "A"
        assert m.package == "com.example"
        assert m.repository == "repo"
        assert m.module == "mod"

    def test_method_location_set(self) -> None:
        cm = _members("class A { void m() {} }")
        loc = cm.methods[0].location
        assert loc.start_line >= 0

    def test_method_to_dict_keys(self) -> None:
        cm = _members("class A { void m() {} }")
        d = cm.methods[0].to_dict()
        assert d["type"] == "method"
        required = {"name", "return_type", "modifiers", "parameters", "class", "package"}
        assert required <= set(d.keys())

    def test_annotated_method_modifiers_only(self) -> None:
        src = "class A { @Override public boolean equals(Object o) { return false; } }"
        cm = _members(src)
        mods = cm.methods[0].modifiers
        assert "public" in mods
        # Annotation text should not appear in modifiers list
        assert all("@" not in mod for mod in mods)

    def test_boolean_return_type(self) -> None:
        cm = _members("class A { public boolean isValid() { return true; } }")
        assert cm.methods[0].return_type == "boolean"


# ── Constructor extraction ─────────────────────────────────────────────────────

