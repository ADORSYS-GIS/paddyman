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

class TestMultipleClasses:
    def test_two_classes_extracted(self) -> None:
        src = "class A { void a() {} }\nclass B { void b() {} }"
        root = parse_bytes(src.encode())
        results = extract_file_members(
            root, package="p", file_path="F.java", repository="r", module="m"
        )
        assert len(results) == 2
        names = {cm.class_name for cm in results}
        assert names == {"A", "B"}

    def test_class_and_interface(self) -> None:
        src = "class A { void run() {} }\ninterface B { void check(); }"
        root = parse_bytes(src.encode())
        results = extract_file_members(
            root, package="p", file_path="F.java", repository="r", module="m"
        )
        assert len(results) == 2


# ── Different visibility modifiers ─────────────────────────────────────────────

class TestVisibilityModifiers:
    def test_public_private_protected(self) -> None:
        src = """class A {
            public void pub() {}
            private void priv() {}
            protected void prot() {}
            void pkg() {}
        }"""
        cm = _members(src)
        mod_sets = {m.name: m.modifiers for m in cm.methods}
        assert "public" in mod_sets["pub"]
        assert "private" in mod_sets["priv"]
        assert "protected" in mod_sets["prot"]
        assert mod_sets["pkg"] == []


# ── Generic types ──────────────────────────────────────────────────────────────

class TestGenericTypes:
    def test_generic_method_return(self) -> None:
        cm = _members("class A { public <T> T get(Class<T> c) { return null; } }")
        m = cm.methods[0]
        assert m.name == "get"

    def test_map_field(self) -> None:
        cm = _members("class A { private Map<String, List<Integer>> data; }")
        f = cm.fields[0]
        assert f.name == "data"
        assert "Map" in f.type


# ── Error handling ─────────────────────────────────────────────────────────────

class TestErrorHandling:
    def test_empty_class_body(self) -> None:
        cm = _members("class A {}")
        assert cm.fields == []
        assert cm.methods == []
        assert cm.constructors == []
        assert cm.errors == []

    def test_missing_file_returns_empty(self, tmp_path: Path) -> None:
        result = parse_and_extract_members(tmp_path / "Missing.java")
        assert result == []

    def test_invalid_java_does_not_raise(self) -> None:
        root = parse_bytes(b"not valid java @@@")
        results = extract_file_members(
            root, package="", file_path="x.java", repository="r", module="m"
        )
        assert isinstance(results, list)

    def test_class_members_to_dict(self) -> None:
        cm = _members("class A { int x; void m() {} A() {} }")
        d = cm.to_dict()
        assert "class" in d
        assert "fields" in d
        assert "methods" in d
        assert "constructors" in d

    def test_file_based_extraction(self, tmp_path: Path) -> None:
        f = tmp_path / "Service.java"
        f.write_text(
            "package com.svc;\npublic class Service {\n"
            "  private String id;\n"
            "  public Service(String id) { this.id = id; }\n"
            "  public String getId() { return id; }\n"
            "}\n",
            encoding="utf-8",
        )
        results = parse_and_extract_members(
            f, repository="repo", module="mod", repo_root=tmp_path
        )
        assert len(results) == 1
        cm = results[0]
        assert cm.class_name == "Service"
        assert cm.package == "com.svc"
        assert len(cm.fields) == 1
        assert len(cm.methods) == 1
        assert len(cm.constructors) == 1
