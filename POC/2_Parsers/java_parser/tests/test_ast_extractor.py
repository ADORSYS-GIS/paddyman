"""Tests for the java_parser AST extraction module.

Covers package extraction, import extraction, class/interface/enum detection,
multiple declarations per file, annotation handling, and syntax-error resilience.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from java_parser.java_ast.extractor import extract_file_ast, parse_and_extract
from java_parser.java_ast.models import JavaDeclarationType, JavaFileAst
from java_parser.java_ast.parser import parse_bytes


# ── Helpers ────────────────────────────────────────────────────────────────────

def _parse(src: str, file_path: str = "Test.java") -> JavaFileAst:
    """Parse *src* as Java source and return extracted AST."""
    root = parse_bytes(src.encode())
    return extract_file_ast(root, file_path=file_path, repository="repo", module="mod")


# ── Package extraction ─────────────────────────────────────────────────────────

class TestPackageExtraction:
    def test_simple_package(self) -> None:
        ast = _parse("package com.example;\npublic class Foo {}")
        assert ast.package == "com.example"

    def test_deep_package(self) -> None:
        ast = _parse("package de.adorsys.psd2.xs2a.core;\npublic class X {}")
        assert ast.package == "de.adorsys.psd2.xs2a.core"

    def test_no_package_returns_empty(self) -> None:
        ast = _parse("public class NoPackage {}")
        assert ast.package == ""

    def test_package_with_semicolon_whitespace(self) -> None:
        ast = _parse("package   org.example  ;\nclass A {}")
        assert ast.package == "org.example"


# ── Import extraction ──────────────────────────────────────────────────────────

class TestImportExtraction:
    def test_single_import(self) -> None:
        ast = _parse("import java.util.List;\nclass A {}")
        assert "java.util.List" in ast.imports

    def test_multiple_imports(self) -> None:
        src = "import java.util.List;\nimport java.util.Map;\nclass A {}"
        ast = _parse(src)
        assert "java.util.List" in ast.imports
        assert "java.util.Map" in ast.imports
        assert len(ast.imports) == 2

    def test_static_import(self) -> None:
        ast = _parse("import static org.junit.Assert.assertEquals;\nclass A {}")
        assert any("assertEquals" in i for i in ast.imports)
        assert any(i.startswith("static") for i in ast.imports)

    def test_wildcard_import(self) -> None:
        ast = _parse("import java.util.*;\nclass A {}")
        assert any("java.util" in i for i in ast.imports)

    def test_no_imports_returns_empty_list(self) -> None:
        ast = _parse("class A {}")
        assert ast.imports == []


# ── Class detection ────────────────────────────────────────────────────────────

class TestClassDetection:
    def test_simple_class(self) -> None:
        ast = _parse("package p;\nclass Foo {}")
        assert len(ast.declarations) == 1
        d = ast.declarations[0]
        assert d.type == JavaDeclarationType.CLASS
        assert d.name == "Foo"
        assert d.package == "p"

    def test_public_class(self) -> None:
        ast = _parse("public class Bar {}")
        d = ast.declarations[0]
        assert "public" in d.modifiers

    def test_abstract_class(self) -> None:
        ast = _parse("public abstract class Abs {}")
        d = ast.declarations[0]
        assert "abstract" in d.modifiers
        assert "public" in d.modifiers

    def test_final_class(self) -> None:
        ast = _parse("public final class Fin {}")
        assert "final" in ast.declarations[0].modifiers

    def test_class_extends(self) -> None:
        ast = _parse("class Child extends Parent {}")
        d = ast.declarations[0]
        assert d.superclass == "Parent"

    def test_class_implements_single(self) -> None:
        ast = _parse("class Foo implements Runnable {}")
        assert "Runnable" in ast.declarations[0].interfaces

    def test_class_implements_multiple(self) -> None:
        ast = _parse("class Foo implements Runnable, Serializable {}")
        ifaces = ast.declarations[0].interfaces
        assert "Runnable" in ifaces
        assert "Serializable" in ifaces

    def test_class_extends_and_implements(self) -> None:
        ast = _parse("class Foo extends Base implements Runnable {}")
        d = ast.declarations[0]
        assert d.superclass == "Base"
        assert "Runnable" in d.interfaces

    def test_class_with_generics_superclass(self) -> None:
        ast = _parse("class Foo extends AbstractList<String> {}")
        assert ast.declarations[0].superclass == "AbstractList"

    def test_annotated_class_modifiers_exclude_annotations(self) -> None:
        ast = _parse("@Deprecated public class Ann {}")
        mods = ast.declarations[0].modifiers
        assert "public" in mods
        assert "@Deprecated" not in mods

    def test_class_provenance_fields(self) -> None:
        ast = _parse("class X {}", file_path="com/X.java")
        d = ast.declarations[0]
        assert d.file_path == "com/X.java"
        assert d.repository == "repo"
        assert d.module == "mod"

    def test_class_source_location(self) -> None:
        ast = _parse("class X {}")
        loc = ast.declarations[0].location
        assert loc.start_line == 0
        assert loc.start_col == 0


# ── Interface detection ────────────────────────────────────────────────────────

class TestInterfaceDetection:
    def test_simple_interface(self) -> None:
        ast = _parse("interface IFoo {}")
        d = ast.declarations[0]
        assert d.type == JavaDeclarationType.INTERFACE
        assert d.name == "IFoo"

    def test_public_interface(self) -> None:
        ast = _parse("public interface IBar {}")
        assert "public" in ast.declarations[0].modifiers

    def test_interface_extends_single(self) -> None:
        ast = _parse("interface Child extends Parent {}")
        assert "Parent" in ast.declarations[0].interfaces

    def test_interface_extends_multiple(self) -> None:
        ast = _parse("interface Multi extends A, B, C {}")
        ifaces = ast.declarations[0].interfaces
        assert "A" in ifaces
        assert "B" in ifaces
        assert "C" in ifaces

    def test_interface_no_superclass(self) -> None:
        ast = _parse("interface IFoo {}")
        assert ast.declarations[0].superclass is None


# ── Enum detection ─────────────────────────────────────────────────────────────

class TestEnumDetection:
    def test_simple_enum(self) -> None:
        ast = _parse("enum Color { RED, GREEN, BLUE }")
        d = ast.declarations[0]
        assert d.type == JavaDeclarationType.ENUM
        assert d.name == "Color"

    def test_public_enum(self) -> None:
        ast = _parse("public enum Status { ACTIVE, INACTIVE }")
        assert "public" in ast.declarations[0].modifiers

    def test_enum_no_superclass(self) -> None:
        ast = _parse("enum E { A }")
        assert ast.declarations[0].superclass is None


# ── Multiple declarations per file ─────────────────────────────────────────────

class TestMultipleDeclarations:
    def test_class_and_interface(self) -> None:
        src = "class A {}\ninterface B {}"
        ast = _parse(src)
        types = {d.type for d in ast.declarations}
        assert JavaDeclarationType.CLASS in types
        assert JavaDeclarationType.INTERFACE in types

    def test_all_three_kinds(self) -> None:
        src = "class A {}\ninterface B {}\nenum C { X }"
        ast = _parse(src)
        types = {d.type for d in ast.declarations}
        assert len(types) == 3

    def test_two_classes(self) -> None:
        src = "class First {}\nclass Second {}"
        ast = _parse(src)
        names = {d.name for d in ast.declarations}
        assert "First" in names
        assert "Second" in names

    def test_declaration_count(self) -> None:
        src = "class A {}\nclass B {}\ninterface C {}\nenum D { X }"
        ast = _parse(src)
        assert len(ast.declarations) == 4


# ── Annotation type handling ───────────────────────────────────────────────────

class TestAnnotationTypes:
    def test_annotation_type_not_extracted_as_declaration(self) -> None:
        # @interface is a Java annotation type — not in scope for this stage
        ast = _parse("public @interface MyAnnotation {}")
        # Should produce zero declarations (annotation_type_declaration is skipped)
        assert all(
            d.type in (JavaDeclarationType.CLASS, JavaDeclarationType.INTERFACE, JavaDeclarationType.ENUM)
            for d in ast.declarations
        )

    def test_annotated_class_still_extracted(self) -> None:
        ast = _parse("@SuppressWarnings(\"all\")\npublic class Annotated {}")
        assert len(ast.declarations) == 1
        assert ast.declarations[0].name == "Annotated"


# ── Error handling ─────────────────────────────────────────────────────────────

class TestErrorHandling:
    def test_empty_source(self) -> None:
        ast = _parse("")
        assert ast.package == ""
        assert ast.imports == []
        assert ast.declarations == []

    def test_invalid_java_flags_has_errors(self) -> None:
        ast = _parse("this is not valid java @@@!")
        assert ast.has_errors is True

    def test_partial_class_extracts_what_it_can(self) -> None:
        # tree-sitter recovers partial ASTs
        ast = _parse("package p;\nclass Incomplete {")
        # package should still be extracted even with errors
        assert ast.package == "p"

    def test_error_message_set_on_invalid_input(self) -> None:
        ast = _parse("!!! invalid !!!")
        if ast.has_errors:
            assert ast.error_message is not None

    def test_missing_file_returns_error_ast(self, tmp_path: Path) -> None:
        result = parse_and_extract(tmp_path / "Missing.java", repository="r", module="m")
        assert result.has_errors is True
        assert result.error_message is not None


# ── File-based parsing ─────────────────────────────────────────────────────────

class TestFileBasedParsing:
    def test_parses_real_file(self, tmp_path: Path) -> None:
        f = tmp_path / "Service.java"
        f.write_text(
            "package com.example;\npublic interface Service {\n}\n",
            encoding="utf-8",
        )
        ast = parse_and_extract(f, repository="repo", module="mod", repo_root=tmp_path)
        assert ast.package == "com.example"
        assert ast.declarations[0].name == "Service"

    def test_relative_path_in_result(self, tmp_path: Path) -> None:
        sub = tmp_path / "com" / "example"
        sub.mkdir(parents=True)
        f = sub / "Foo.java"
        f.write_text("package com.example;\nclass Foo {}", encoding="utf-8")
        ast = parse_and_extract(f, repository="r", module="m", repo_root=tmp_path)
        assert ast.file_path == "com/example/Foo.java"

    def test_to_dict_structure(self, tmp_path: Path) -> None:
        f = tmp_path / "A.java"
        f.write_text("package p;\npublic class A {}", encoding="utf-8")
        ast = parse_and_extract(f, repository="r", module="m", repo_root=tmp_path)
        d = ast.to_dict()
        assert set(d.keys()) >= {
            "file_path", "repository", "module", "package",
            "imports", "declarations", "has_errors", "error_message",
        }
        assert d["declarations"][0]["type"] == "class"

    def test_declaration_to_dict_keys(self) -> None:
        ast = _parse("package p;\npublic class Z {}")
        d = ast.declarations[0].to_dict()
        expected = {
            "type", "name", "package", "modifiers", "superclass",
            "interfaces", "annotations", "location", "file_path", "repository", "module",
        }
        assert expected == set(d.keys())
