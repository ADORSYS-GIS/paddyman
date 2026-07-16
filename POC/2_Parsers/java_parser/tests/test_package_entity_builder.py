"""Tests for Java package entity extraction and package relationships."""
from __future__ import annotations

from pathlib import Path

from java_parser.java_ast.extractor import parse_and_extract
from java_parser.package_entity_builder import (
    package_entity_from_ast,
    package_entity_for_record,
    unique_package_entities,
)
from java_parser.package_relationship_builder import build_package_relationships


def _file_ast(src: str, tmp_path: Path):
    path = tmp_path / "Foo.java"
    path.write_text(src, encoding="utf-8")
    return parse_and_extract(path, repository="repo", module="mod", repo_root=tmp_path)


def test_single_file_package_extraction(tmp_path: Path) -> None:
    ast = _file_ast("package com.example;\npublic class Foo {}\n", tmp_path)
    entity = package_entity_from_ast(ast)
    assert entity is not None
    assert entity["type"] == "Package"
    assert entity["qualified_name"] == "com.example"
    assert entity["repository"] == "repo"


def test_multi_file_same_package_deduplicates() -> None:
    entities = [
        {"type": "Package", "qualified_name": "com.example", "name": "com.example"},
        {"type": "Package", "qualified_name": "com.example", "name": "com.example"},
    ]
    unique = unique_package_entities(entities)
    assert len(unique) == 1


def test_nested_package_hierarchy_and_types() -> None:
    entities = [
        {"type": "Package", "qualified_name": "java.util", "name": "java.util", "repository": "repo", "module": "mod", "file_path": "src/java/util"},
        {"type": "Package", "qualified_name": "java.util.concurrent", "name": "java.util.concurrent", "repository": "repo", "module": "mod", "file_path": "src/java/util/concurrent"},
        {"type": "Package", "qualified_name": "com.example.a", "name": "com.example.a", "repository": "repo", "module": "mod", "file_path": "src/com/example/a"},
        {"type": "Package", "qualified_name": "com.example.b", "name": "com.example.b", "repository": "repo", "module": "mod", "file_path": "src/com/example/b"},
        {"type": "Class", "qualified_name": "java.util.concurrent.Executor", "name": "Executor", "package": "java.util.concurrent", "repository": "repo", "module": "mod", "file_path": "Executor.java"},
        {"type": "Interface", "qualified_name": "java.util.concurrent.Callable", "name": "Callable", "package": "java.util.concurrent", "repository": "repo", "module": "mod", "file_path": "Callable.java"},
        {"type": "Enum", "qualified_name": "java.util.concurrent.Mode", "name": "Mode", "package": "java.util.concurrent", "repository": "repo", "module": "mod", "file_path": "Mode.java"},
        {"type": "Import", "name": "com.example.b.Helper", "package": "com.example.a", "repository": "repo", "module": "mod", "file_path": "Helper.java", "is_static": False, "is_wildcard": False},
        {"type": "Import", "name": "com.example.b.*", "package": "com.example.a", "repository": "repo", "module": "mod", "file_path": "Helper.java", "is_static": False, "is_wildcard": True},
    ]

    rels = build_package_relationships(entities, "mod")
    contains = [r for r in rels if r["type"] == "CONTAINS"]
    imports = [r for r in rels if r["type"] == "IMPORTS"]
    belongs_to = [r for r in rels if r["type"] == "BELONGS_TO"]
    assert {r["target"] for r in contains} >= {
        "Package:java.util.concurrent",
        "Class:java.util.concurrent.Executor",
        "Interface:java.util.concurrent.Callable",
        "Enum:java.util.concurrent.Mode",
    }
    assert any(r["source"] == "Package:com.example.a" and r["target"] == "Package:com.example.b" for r in imports)
    assert any(r["source"] == "Package:com.example.a" and r["target"] == "Module:mod" for r in belongs_to)


def test_empty_or_package_less_file_input(tmp_path: Path) -> None:
    ast = _file_ast("public class Bare {}\n", tmp_path)
    assert package_entity_from_ast(ast) is None


def test_invalid_package_metadata_is_ignored() -> None:
    class _Ast:
        package = "1bad.package"
        file_path = "src/Foo.java"
        repository = "repo"
        module = "mod"

    assert package_entity_from_ast(_Ast()) is None


def test_package_entity_for_record(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    java_file = repo / "src" / "main" / "java" / "com" / "example" / "Foo.java"
    java_file.parent.mkdir(parents=True)
    java_file.write_text("package com.example;\npublic class Foo {}\n", encoding="utf-8")

    class _Record:
        repository = "repo"
        relative_path = str(java_file.relative_to(repo))

    entity = package_entity_for_record(repo, _Record(), "mod")
    assert entity is not None
    assert entity["file_path"].endswith("src/main/java/com/example")