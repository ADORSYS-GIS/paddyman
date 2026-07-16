"""Tests for field_to_entity and field extraction via member_entities_for_record."""
from __future__ import annotations

import sys
from pathlib import Path

_PARSERS_ROOT = Path(__file__).resolve().parent.parent.parent
_POC_ROOT = _PARSERS_ROOT.parent
for _p in (str(_POC_ROOT), str(_PARSERS_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from java_parser.java_ast.models import SourceLocation
from java_parser.field_entity_builder import field_to_entity
from java_parser.member_entity_orchestrator import member_entities_for_record
from java_parser.members.models import JavaField


# ── Helpers ────────────────────────────────────────────────────────────────────

def _field(
    name: str = "myField",
    field_type: str = "String",
    modifiers: list[str] | None = None,
    annotations: list[str] | None = None,
    start_line: int = 4,
    end_line: int = 4,
) -> JavaField:
    loc = SourceLocation(start_line, 0, end_line, 0)
    return JavaField(
        name=name,
        type=field_type,
        modifiers=["private"] if modifiers is None else modifiers,
        class_name="MyClass",
        package="com.example",
        file_path="com/example/MyClass.java",
        repository="my-repo",
        module="my-module",
        annotations=annotations or [],
        location=loc,
    )


# ── field_to_entity ───────────────────────────────────────────────────────────

class TestFieldToEntity:
    def test_required_fields_present(self) -> None:
        entity = field_to_entity(_field(), "doc:id")
        assert entity["type"] == "Field"
        assert entity["name"] == "myField"
        assert entity["field_type"] == "String"
        assert entity["class"] == "MyClass"
        assert entity["visibility"] == "private"
        assert entity["is_static"] is False
        assert entity["is_final"] is False
        assert entity["annotations"] == []
        assert entity["repository"] == "my-repo"
        assert entity["module"] == "my-module"
        assert entity["file_path"] == "com/example/MyClass.java"
        assert entity["source"] == "doc:id"

    def test_line_numbers_are_one_based(self) -> None:
        entity = field_to_entity(_field(start_line=9, end_line=9), "d")
        assert entity["start_line"] == 10
        assert entity["end_line"] == 10

    def test_static_final_constant(self) -> None:
        entity = field_to_entity(
            _field(modifiers=["public", "static", "final"]), "d"
        )
        assert entity["is_static"] is True
        assert entity["is_final"] is True
        assert entity["visibility"] == "public"

    def test_static_non_final(self) -> None:
        entity = field_to_entity(_field(modifiers=["private", "static"]), "d")
        assert entity["is_static"] is True
        assert entity["is_final"] is False

    def test_package_private_visibility(self) -> None:
        entity = field_to_entity(_field(modifiers=[]), "d")
        assert entity["visibility"] == "package-private"

    def test_annotations_preserved(self) -> None:
        entity = field_to_entity(_field(annotations=["@Autowired"]), "d")
        assert entity["annotations"] == [
            {"name": "@Autowired", "qualified_name": "Autowired", "attributes": {}}
        ]

    def test_qualified_class_with_package(self) -> None:
        entity = field_to_entity(_field(), "d")
        assert entity["qualified_class"] == "com.example.MyClass"

    def test_generic_field_type(self) -> None:
        entity = field_to_entity(_field(field_type="List<String>"), "d")
        assert entity["field_type"] == "List<String>"


# ── member_entities_for_record — field integration ────────────────────────────

class _Record:
    def __init__(self, relative_path: str, repository: str = "repo", module: str = "mod") -> None:
        self.relative_path = relative_path
        self.repository = repository
        self.module = module


class TestFieldEntitiesFromRecord:
    def _write_java(self, tmp_path: Path, src: str) -> tuple[Path, str]:
        java_file = tmp_path / "src" / "main" / "java" / "com" / "ex" / "Foo.java"
        java_file.parent.mkdir(parents=True)
        java_file.write_text(src, encoding="utf-8")
        return tmp_path, str(java_file.relative_to(tmp_path))

    def test_three_fields_produce_three_entities(self, tmp_path: Path) -> None:
        src = (
            "package com.ex;\n"
            "public class Foo {\n"
            "  private String name;\n"
            "  private int age;\n"
            "  private boolean active;\n"
            "}\n"
        )
        repo_root, relative = self._write_java(tmp_path, src)
        entities = member_entities_for_record(
            repo_root, _Record(relative), "doc:id", "mod"
        )
        field_entities = [e for e in entities if e["type"] == "Field"]
        assert len(field_entities) == 3
        names = {e["name"] for e in field_entities}
        assert names == {"name", "age", "active"}

    def test_static_final_constant_flags(self, tmp_path: Path) -> None:
        src = (
            "package com.ex;\n"
            "public class Foo {\n"
            '  public static final String FOO = "bar";\n'
            "}\n"
        )
        repo_root, relative = self._write_java(tmp_path, src)
        entities = member_entities_for_record(
            repo_root, _Record(relative), "doc:id", "mod"
        )
        field_entities = [e for e in entities if e["type"] == "Field"]
        assert len(field_entities) == 1
        assert field_entities[0]["is_static"] is True
        assert field_entities[0]["is_final"] is True

    def test_field_entity_has_start_line(self, tmp_path: Path) -> None:
        src = (
            "package com.ex;\n"
            "public class Foo {\n"
            "  private String name;\n"
            "}\n"
        )
        repo_root, relative = self._write_java(tmp_path, src)
        entities = member_entities_for_record(
            repo_root, _Record(relative), "doc:id", "mod"
        )
        field_entities = [e for e in entities if e["type"] == "Field"]
        assert field_entities[0]["start_line"] >= 1

    def test_field_entity_required_keys(self, tmp_path: Path) -> None:
        src = (
            "package com.ex;\n"
            "public class Foo {\n"
            "  private int count;\n"
            "}\n"
        )
        repo_root, relative = self._write_java(tmp_path, src)
        entities = member_entities_for_record(
            repo_root, _Record(relative), "doc:id", "mod"
        )
        field_entities = [e for e in entities if e["type"] == "Field"]
        required = {
            "type", "name", "field_type", "class", "visibility",
            "is_static", "is_final", "annotations", "start_line", "end_line",
            "repository", "module", "file_path",
        }
        assert all(required.issubset(e.keys()) for e in field_entities)

    def test_empty_class_no_field_entities(self, tmp_path: Path) -> None:
        src = "package com.ex;\npublic class Foo {}\n"
        repo_root, relative = self._write_java(tmp_path, src)
        entities = member_entities_for_record(
            repo_root, _Record(relative), "doc:id", "mod"
        )
        assert not any(e["type"] == "Field" for e in entities)
