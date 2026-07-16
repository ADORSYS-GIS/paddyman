"""Tests for member_entity_builder: method_to_entity, constructor_to_entity,
and member_entities_for_record."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

_PARSERS_ROOT = Path(__file__).resolve().parent.parent.parent
_POC_ROOT = _PARSERS_ROOT.parent
for _p in (str(_POC_ROOT), str(_PARSERS_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from java_parser.java_ast.models import SourceLocation
from java_parser.member_entity_builder import (
    constructor_to_entity,
    method_to_entity,
)
from java_parser.member_entity_orchestrator import member_entities_for_record
from java_parser.members.models import JavaConstructor, JavaMethod, JavaParameter


# ── Helpers ────────────────────────────────────────────────────────────────────

def _method(
    name: str = "doSomething",
    return_type: str = "void",
    modifiers: list[str] | None = None,
    parameters: list[JavaParameter] | None = None,
    annotations: list[str] | None = None,
    start_line: int = 4,
    end_line: int = 8,
) -> JavaMethod:
    loc = SourceLocation(start_line, 0, end_line, 0)
    return JavaMethod(
        name=name,
        return_type=return_type,
        modifiers=["public"] if modifiers is None else modifiers,
        parameters=parameters or [],
        class_name="MyClass",
        package="com.example",
        file_path="com/example/MyClass.java",
        repository="my-repo",
        module="my-module",
        annotations=annotations or [],
        location=loc,
    )


def _constructor(
    modifiers: list[str] | None = None,
    parameters: list[JavaParameter] | None = None,
    start_line: int = 2,
    end_line: int = 3,
) -> JavaConstructor:
    loc = SourceLocation(start_line, 0, end_line, 0)
    return JavaConstructor(
        name="MyClass",
        modifiers=modifiers or ["public"],
        parameters=parameters or [],
        class_name="MyClass",
        package="com.example",
        file_path="com/example/MyClass.java",
        repository="my-repo",
        module="my-module",
        location=loc,
    )


# ── method_to_entity ──────────────────────────────────────────────────────────

class TestMethodToEntity:
    def test_required_fields_present(self) -> None:
        entity = method_to_entity(_method(), "doc:id")
        assert entity["type"] == "Method"
        assert entity["name"] == "doSomething"
        assert entity["class"] == "MyClass"
        assert entity["visibility"] == "public"
        assert entity["return_type"] == "void"
        assert entity["parameter_count"] == 0
        assert entity["annotations"] == []
        assert entity["is_static"] is False
        assert entity["is_abstract"] is False
        assert entity["repository"] == "my-repo"
        assert entity["module"] == "my-module"
        assert entity["file_path"] == "com/example/MyClass.java"
        assert entity["source"] == "doc:id"

    def test_line_numbers_are_one_based(self) -> None:
        entity = method_to_entity(_method(start_line=9, end_line=14), "d")
        assert entity["start_line"] == 10
        assert entity["end_line"] == 15

    def test_static_method(self) -> None:
        entity = method_to_entity(_method(modifiers=["public", "static"]), "d")
        assert entity["is_static"] is True

    def test_abstract_method(self) -> None:
        entity = method_to_entity(_method(modifiers=["public", "abstract"]), "d")
        assert entity["is_abstract"] is True

    def test_parameters_count(self) -> None:
        params = [JavaParameter("x", "int"), JavaParameter("items", "List<String>", is_vararg=False)]
        entity = method_to_entity(_method(parameters=params), "d")
        assert entity["parameter_count"] == 2

    def test_override_annotation_preserved(self) -> None:
        entity = method_to_entity(_method(annotations=["@Override"]), "d")
        assert entity["annotations"] == [
            {"name": "@Override", "qualified_name": "Override", "attributes": {}}
        ]

    def test_qualified_class_with_package(self) -> None:
        entity = method_to_entity(_method(), "d")
        assert entity["qualified_class"] == "com.example.MyClass"

    def test_package_private_visibility(self) -> None:
        entity = method_to_entity(_method(modifiers=[]), "d")
        assert entity["visibility"] == "package-private"

    def test_private_visibility(self) -> None:
        entity = method_to_entity(_method(modifiers=["private"]), "d")
        assert entity["visibility"] == "private"


# ── constructor_to_entity ─────────────────────────────────────────────────────

class TestConstructorToEntity:
    def test_required_fields_present(self) -> None:
        entity = constructor_to_entity(_constructor(), "doc:id")
        assert entity["type"] == "Constructor"
        assert entity["name"] == "MyClass"
        assert entity["class"] == "MyClass"
        assert entity["visibility"] == "public"
        assert entity["return_type"] is None
        assert entity["parameter_count"] == 0
        assert entity["is_static"] is False
        assert entity["is_abstract"] is False
        assert entity["repository"] == "my-repo"
        assert entity["module"] == "my-module"
        assert entity["source"] == "doc:id"

    def test_line_numbers_are_one_based(self) -> None:
        entity = constructor_to_entity(_constructor(start_line=0, end_line=3), "d")
        assert entity["start_line"] == 1
        assert entity["end_line"] == 4

    def test_parameters_count(self) -> None:
        params = [JavaParameter("name", "String")]
        entity = constructor_to_entity(_constructor(parameters=params), "d")
        assert entity["parameter_count"] == 1

    def test_return_type_is_null(self) -> None:
        entity = constructor_to_entity(_constructor(), "d")
        assert entity["return_type"] is None


# ── member_entities_for_record ────────────────────────────────────────────────

class _Record:
    def __init__(self, relative_path: str, repository: str = "repo", module: str = "mod") -> None:
        self.relative_path = relative_path
        self.repository = repository
        self.module = module


class TestMemberEntitiesForRecord:
    def _write_java(self, tmp_path: Path, src: str) -> tuple[Path, str]:
        java_file = tmp_path / "src" / "main" / "java" / "com" / "ex" / "Foo.java"
        java_file.parent.mkdir(parents=True)
        java_file.write_text(src, encoding="utf-8")
        relative = str(java_file.relative_to(tmp_path))
        return tmp_path, relative

    def test_two_methods_one_constructor(self, tmp_path: Path) -> None:
        src = (
            "package com.ex;\n"
            "public class Foo {\n"
            "  public Foo() {}\n"
            "  public void alpha() {}\n"
            "  public void beta() {}\n"
            "}\n"
        )
        repo_root, relative = self._write_java(tmp_path, src)
        record = _Record(relative)
        entities = member_entities_for_record(repo_root, record, "doc:id", "mod")

        types = [e["type"] for e in entities]
        assert types.count("Constructor") == 1
        assert types.count("Method") == 2

    def test_static_method_flagged(self, tmp_path: Path) -> None:
        src = (
            "package com.ex;\n"
            "public class Foo {\n"
            "  public static Foo create() { return new Foo(); }\n"
            "}\n"
        )
        repo_root, relative = self._write_java(tmp_path, src)
        entities = member_entities_for_record(
            repo_root, _Record(relative), "doc:id", "mod"
        )
        method_entities = [e for e in entities if e["type"] == "Method"]
        assert len(method_entities) == 1
        assert method_entities[0]["is_static"] is True

    def test_abstract_method_flagged(self, tmp_path: Path) -> None:
        src = (
            "package com.ex;\n"
            "public abstract class Foo {\n"
            "  public abstract void process();\n"
            "}\n"
        )
        repo_root, relative = self._write_java(tmp_path, src)
        entities = member_entities_for_record(
            repo_root, _Record(relative), "doc:id", "mod"
        )
        method_entities = [e for e in entities if e["type"] == "Method"]
        assert len(method_entities) == 1
        assert method_entities[0]["is_abstract"] is True

    def test_missing_file_returns_empty(self, tmp_path: Path) -> None:
        record = _Record("nonexistent/Missing.java")
        entities = member_entities_for_record(tmp_path, record, "doc:id", "mod")
        assert entities == []

    def test_entity_fields_include_required_keys(self, tmp_path: Path) -> None:
        src = (
            "package com.ex;\n"
            "public class Foo {\n"
            "  public String getName() { return null; }\n"
            "}\n"
        )
        repo_root, relative = self._write_java(tmp_path, src)
        entities = member_entities_for_record(
            repo_root, _Record(relative), "doc:id", "mod"
        )
        required = {
            "type", "name", "class", "visibility", "return_type",
            "parameter_count", "annotations", "is_static", "is_abstract",
            "start_line", "end_line", "repository", "module", "file_path",
        }
        assert all(required.issubset(e.keys()) for e in entities)

    def test_empty_class_returns_empty(self, tmp_path: Path) -> None:
        src = "package com.ex;\npublic class Foo {}\n"
        repo_root, relative = self._write_java(tmp_path, src)
        entities = member_entities_for_record(
            repo_root, _Record(relative), "doc:id", "mod"
        )
        assert entities == []

    def test_member_annotations_are_structured(self, tmp_path: Path) -> None:
        src = (
            "package com.ex;\n"
            "import javax.inject.Inject;\n"
            "import org.springframework.web.bind.annotation.RequestMapping;\n"
            "public class Foo {\n"
            "  @Inject\n"
            "  public Foo() {}\n"
            "  @RequestMapping(value=\"/v1\", method=GET)\n"
            "  public void handle() {}\n"
            "}\n"
        )
        repo_root, relative = self._write_java(tmp_path, src)
        imports = [
            "javax.inject.Inject",
            "org.springframework.web.bind.annotation.RequestMapping",
        ]
        entities = member_entities_for_record(
            repo_root, _Record(relative), "doc:id", "mod", imports=imports
        )

        ctor = next(e for e in entities if e["type"] == "Constructor")
        method = next(e for e in entities if e["type"] == "Method")
        assert ctor["annotations"] == [
            {"name": "@Inject", "qualified_name": "javax.inject.Inject", "attributes": {}}
        ]
        assert method["annotations"] == [
            {
                "name": "@RequestMapping",
                "qualified_name": "org.springframework.web.bind.annotation.RequestMapping",
                "attributes": {"value": "/v1", "method": "GET"},
            }
        ]
