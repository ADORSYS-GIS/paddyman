"""Tests for java_entity_builder: declaration_to_entity and entities_for_record."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Ensure parsers root is on sys.path so shared imports resolve.
_PARSERS_ROOT = Path(__file__).resolve().parent.parent.parent
_POC_ROOT = _PARSERS_ROOT.parent
for _p in (str(_POC_ROOT), str(_PARSERS_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from java_parser.java_ast.extractor import extract_file_ast
from java_parser.java_ast.models import JavaDeclarationType
from java_parser.java_ast.parser import parse_bytes
from java_parser.java_entity_builder import declaration_to_entity, entities_for_record


# ── Helpers ────────────────────────────────────────────────────────────────────

def _declarations(src: str, repository: str = "repo", module: str = "mod"):
    root = parse_bytes(src.encode())
    return extract_file_ast(
        root, file_path="com/example/Foo.java", repository=repository, module=module
    ).declarations


def _file_ast(src: str, repository: str = "repo", module: str = "mod"):
    root = parse_bytes(src.encode())
    return extract_file_ast(
        root, file_path="com/example/Foo.java", repository=repository, module=module
    )


# ── declaration_to_entity ──────────────────────────────────────────────────────

class TestDeclarationToEntity:
    def test_class_entity_fields(self) -> None:
        decls = _declarations("package com.example;\npublic class Foo {}")
        entity = declaration_to_entity(decls[0], "java_parser:repo:mod:Foo.java")
        assert entity["type"] == "Class"
        assert entity["name"] == "Foo"
        assert entity["qualified_name"] == "com.example.Foo"
        assert entity["package"] == "com.example"
        assert entity["visibility"] == "public"
        assert entity["is_abstract"] is False
        assert entity["source"] == "java_parser:repo:mod:Foo.java"
        assert entity["repository"] == "repo"
        assert entity["module"] == "mod"
        assert entity["extends"] is None
        assert entity["implements"] == []
        assert entity["annotations"] == []

    def test_interface_entity_type_label(self) -> None:
        decls = _declarations("package p;\npublic interface MyIface {}")
        entity = declaration_to_entity(decls[0], "src")
        assert entity["type"] == "Interface"
        assert entity["extends"] is None  # interfaces use implements list

    def test_enum_entity_type_label(self) -> None:
        decls = _declarations("package p;\npublic enum Color { RED, GREEN }")
        entity = declaration_to_entity(decls[0], "src")
        assert entity["type"] == "Enum"
        assert entity["name"] == "Color"

    def test_abstract_class(self) -> None:
        decls = _declarations("package p;\npublic abstract class Base {}")
        entity = declaration_to_entity(decls[0], "src")
        assert entity["is_abstract"] is True

    def test_package_private_visibility(self) -> None:
        decls = _declarations("package p;\nclass Hidden {}")
        entity = declaration_to_entity(decls[0], "src")
        assert entity["visibility"] == "package-private"

    def test_class_with_superclass(self) -> None:
        decls = _declarations("package p;\npublic class Child extends Base {}")
        entity = declaration_to_entity(decls[0], "src")
        assert entity["extends"] == "Base"

    def test_class_with_implements(self) -> None:
        decls = _declarations("package p;\npublic class Impl implements Runnable {}")
        entity = declaration_to_entity(decls[0], "src")
        assert "Runnable" in entity["implements"]

    def test_start_end_line_are_one_based(self) -> None:
        src = "package p;\npublic class Foo {}"
        decls = _declarations(src)
        entity = declaration_to_entity(decls[0], "src")
        # start_line must be >= 1 (1-based)
        assert entity["start_line"] >= 1
        assert entity["end_line"] >= entity["start_line"]

    def test_no_package_qualified_name(self) -> None:
        decls = _declarations("public class Bare {}")
        entity = declaration_to_entity(decls[0], "src")
        assert entity["qualified_name"] == "Bare"
        assert entity["package"] == ""

    def test_annotations_list(self) -> None:
        src = "package p;\n@Deprecated\npublic class Old {}"
        decls = _declarations(src)
        entity = declaration_to_entity(decls[0], "src")
        assert entity["annotations"] == [
            {"name": "@Deprecated", "qualified_name": "Deprecated", "attributes": {}}
        ]

    def test_annotation_import_resolution(self) -> None:
        src = (
            "package p;\n"
            "import lombok.extern.slf4j.Slf4j;\n"
            "@Slf4j\n"
            "public class Foo {}"
        )
        file_ast = _file_ast(src)
        entity = declaration_to_entity(file_ast.declarations[0], "src", file_ast.imports)
        assert entity["annotations"] == [
            {
                "name": "@Slf4j",
                "qualified_name": "lombok.extern.slf4j.Slf4j",
                "attributes": {},
            }
        ]


class TestThreeDeclarationTypes:
    """Three entity dicts must appear when a file has class, interface, and enum."""

    def test_three_entities_from_multi_type_file(self) -> None:
        src = (
            "package p;\n"
            "public class MyClass {}\n"
            "public interface MyIface {}\n"
            "public enum MyEnum { A }\n"
        )
        decls = _declarations(src)
        doc_id = "java_parser:repo:mod:Multi.java"
        entities = [declaration_to_entity(d, doc_id) for d in decls]
        assert len(entities) == 3
        types = {e["type"] for e in entities}
        assert types == {"Class", "Interface", "Enum"}


# ── entities_for_record ────────────────────────────────────────────────────────

class TestEntitiesForRecord:
    def test_returns_entities_for_valid_file(self, tmp_path: Path) -> None:
        java_file = tmp_path / "src" / "main" / "java" / "com" / "ex" / "App.java"
        java_file.parent.mkdir(parents=True)
        java_file.write_text(
            "package com.ex;\npublic class App {}\npublic interface IApp {}\n",
            encoding="utf-8",
        )

        class _Record:
            repository = "my-repo"
            module = "my-module"
            relative_path = str(java_file.relative_to(tmp_path))

        entities = entities_for_record(
            tmp_path, _Record(), "java_parser:my-repo:my-module:App.java", "my-module"
        )
        assert len(entities) == 2
        names = {e["name"] for e in entities}
        assert names == {"App", "IApp"}

    def test_returns_empty_list_for_missing_file(self, tmp_path: Path) -> None:
        class _Record:
            repository = "r"
            module = "m"
            relative_path = "nonexistent/Missing.java"

        entities = entities_for_record(
            tmp_path, _Record(), "java_parser:r:m:Missing.java", "m"
        )
        assert entities == []
