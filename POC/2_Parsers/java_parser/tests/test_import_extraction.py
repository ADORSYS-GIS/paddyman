"""Tests for Java import extraction.

Covers import entity extraction, import relationship building,
and handling of regular, static, and wildcard imports.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from java_parser.java_ast.extractor import parse_and_extract
from java_parser.import_entity_builder import (
    import_declaration_to_entity,
    import_entities_from_declarations,
)
from java_parser.import_relationship_builder import build_imports_relationships


def test_extract_regular_import(tmp_path: Path) -> None:
    """Verify standard import extraction."""
    src = """
package com.example;
import java.util.List;
public class Foo {}
"""
    path = tmp_path / "Foo.java"
    path.write_text(src)
    
    ast = parse_and_extract(path, repository="repo", module="mod", repo_root=tmp_path)
    
    assert len(ast.import_declarations) == 1
    import_decl = ast.import_declarations[0]
    assert import_decl.name == "java.util.List"
    assert import_decl.is_static is False
    assert import_decl.is_wildcard is False
    assert import_decl.package == "com.example"


def test_extract_static_import(tmp_path: Path) -> None:
    """Verify static import extraction."""
    src = """
package com.example;
import static java.lang.Math.sqrt;
public class Calc {}
"""
    path = tmp_path / "Calc.java"
    path.write_text(src)
    
    ast = parse_and_extract(path, repository="repo", module="mod", repo_root=tmp_path)
    
    assert len(ast.import_declarations) == 1
    import_decl = ast.import_declarations[0]
    assert import_decl.name == "java.lang.Math.sqrt"
    assert import_decl.is_static is True
    assert import_decl.is_wildcard is False


def test_extract_wildcard_import(tmp_path: Path) -> None:
    """Verify wildcard import extraction."""
    src = """
package com.example;
import java.util.*;
public class Container {}
"""
    path = tmp_path / "Container.java"
    path.write_text(src)
    
    ast = parse_and_extract(path, repository="repo", module="mod", repo_root=tmp_path)
    
    assert len(ast.import_declarations) == 1
    import_decl = ast.import_declarations[0]
    assert import_decl.name == "java.util.*"
    assert import_decl.is_static is False
    assert import_decl.is_wildcard is True


def test_extract_multiple_imports(tmp_path: Path) -> None:
    """Verify multiple imports are extracted."""
    src = """
package com.example;
import java.util.List;
import java.util.Map;
import java.io.IOException;
public class Multi {}
"""
    path = tmp_path / "Multi.java"
    path.write_text(src)
    
    ast = parse_and_extract(path, repository="repo", module="mod", repo_root=tmp_path)
    
    assert len(ast.import_declarations) == 3
    names = [decl.name for decl in ast.import_declarations]
    assert "java.util.List" in names
    assert "java.util.Map" in names
    assert "java.io.IOException" in names


def test_import_declaration_to_entity() -> None:
    """Verify import declaration converts to entity dict."""
    from java_parser.java_ast.models import JavaImportDeclaration, SourceLocation
    
    decl = JavaImportDeclaration(
        name="java.util.List",
        is_static=False,
        is_wildcard=False,
        location=SourceLocation(5, 0, 5, 25),
        file_path="src/Foo.java",
        repository="repo",
        module="mod",
        package="com.example",
    )
    
    entity = import_declaration_to_entity(decl, "java_parser:repo:mod:src/Foo.java")
    
    assert entity["type"] == "Import"
    assert entity["name"] == "java.util.List"
    assert entity["source"] == "java_parser:repo:mod:src/Foo.java"
    assert entity["is_static"] is False
    assert entity["is_wildcard"] is False
    assert entity["start_line"] == 6  # 1-indexed
    assert entity["end_line"] == 6
    assert entity["imported_name"] == "List"


def test_import_entities_from_declarations() -> None:
    """Verify multiple import declarations convert to entity dicts."""
    from java_parser.java_ast.models import JavaImportDeclaration, SourceLocation
    
    declarations = [
        JavaImportDeclaration(
            name="java.util.List",
            is_static=False,
            is_wildcard=False,
            location=SourceLocation(5, 0, 5, 25),
            file_path="src/Foo.java",
            repository="repo",
            module="mod",
            package="com.example",
        ),
        JavaImportDeclaration(
            name="java.util.Map",
            is_static=False,
            is_wildcard=False,
            location=SourceLocation(6, 0, 6, 24),
            file_path="src/Foo.java",
            repository="repo",
            module="mod",
            package="com.example",
        ),
    ]
    
    entities = import_entities_from_declarations(declarations, "java_parser:repo:mod:src/Foo.java")
    
    assert len(entities) == 2
    assert all(e["type"] == "Import" for e in entities)
    assert entities[0]["name"] == "java.util.List"
    assert entities[1]["name"] == "java.util.Map"


def test_build_imports_relationships() -> None:
    """Verify IMPORTS relationships are created."""
    file_entities = [
        {
            "type": "Import",
            "name": "java.util.List",
            "source": "java_parser:repo:mod:src/Foo.java",
        },
        {
            "type": "Import",
            "name": "java.util.Map",
            "source": "java_parser:repo:mod:src/Foo.java",
        },
        {
            "type": "Class",
            "name": "Foo",
            "qualified_name": "com.example.Foo",
            "file_path": "src/Foo.java",
            "repository": "repo",
            "module": "mod",
        },
    ]
    
    relationships = build_imports_relationships(file_entities)
    
    assert len(relationships) == 2  # Class -> List, Class -> Map
    assert all(r["type"] == "IMPORTS" for r in relationships)
    assert relationships[0]["source"] == "Class:com.example.Foo"
    assert relationships[0]["target"] == "Import:java.util.List"
    assert relationships[1]["target"] == "Import:java.util.Map"


def test_no_imports_returns_empty_list(tmp_path: Path) -> None:
    """Verify files without imports return empty list."""
    src = """
package com.example;
public class NoImports {}
"""
    path = tmp_path / "NoImports.java"
    path.write_text(src)
    
    ast = parse_and_extract(path, repository="repo", module="mod", repo_root=tmp_path)
    
    assert ast.import_declarations == []


def test_imports_preserve_line_numbers(tmp_path: Path) -> None:
    """Verify import line numbers match source."""
    src = """package com.example;

import java.util.List;
import java.util.Map;

public class Foo {}
"""
    path = tmp_path / "Foo.java"
    path.write_text(src)
    
    ast = parse_and_extract(path, repository="repo", module="mod", repo_root=tmp_path)
    
    assert len(ast.import_declarations) == 2
    # Line numbers are 0-indexed in SourceLocation
    assert ast.import_declarations[0].location.start_line == 2  # Line 3 in file
    assert ast.import_declarations[1].location.start_line == 3  # Line 4 in file


def test_imported_name_extraction() -> None:
    """Verify imported_name property extracts simple name."""
    from java_parser.java_ast.models import JavaImportDeclaration, SourceLocation
    
    regular = JavaImportDeclaration(
        name="java.util.List",
        is_static=False,
        is_wildcard=False,
        location=SourceLocation(0, 0, 0, 0),
    )
    assert regular.imported_name == "List"
    
    wildcard = JavaImportDeclaration(
        name="java.util.*",
        is_static=False,
        is_wildcard=True,
        location=SourceLocation(0, 0, 0, 0),
    )
    assert wildcard.imported_name == "util"
    
    static_import = JavaImportDeclaration(
        name="java.lang.Math.sqrt",
        is_static=True,
        is_wildcard=False,
        location=SourceLocation(0, 0, 0, 0),
    )
    assert static_import.imported_name == "sqrt"
