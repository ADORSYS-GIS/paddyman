"""Extract import declarations from Java AST nodes.

Handles regular, static, and wildcard imports with full metadata.
"""
from __future__ import annotations

from tree_sitter import Node

from .models import JavaImportDeclaration, SourceLocation
from .node_helpers import extract_import


def _location(node: Node) -> SourceLocation:
    """Convert tree-sitter node to SourceLocation."""
    sr, sc = node.start_point
    er, ec = node.end_point
    return SourceLocation(sr, sc, er, ec)


def extract_imports(root: Node) -> list[str]:
    """Extract import names as strings (backward compatibility).
    
    Returns legacy string list of import names.
    """
    imports: list[str] = []
    for child in root.children:
        if child.type == "import_declaration":
            name = extract_import(child)
            if name:
                imports.append(name)
    return imports


def extract_import_declarations(
    root: Node,
    package: str,
    file_path: str,
    repository: str,
    module: str,
) -> list[JavaImportDeclaration]:
    """Extract structured import declarations from AST.
    
    Returns list of JavaImportDeclaration objects with metadata.
    
    Args:
        root:       Root node of the parsed Java source file.
        package:    Package declared in the file.
        file_path:  Repository-relative path to the source file.
        repository: Repository name (for provenance tracking).
        module:     Module label (for provenance tracking).
    """
    declarations: list[JavaImportDeclaration] = []
    for child in root.children:
        if child.type == "import_declaration":
            name = extract_import(child)
            if not name:
                continue
            is_static = name.startswith("static ")
            clean_name = name[7:] if is_static else name
            is_wildcard = clean_name.endswith(".*")
            
            declarations.append(
                JavaImportDeclaration(
                    name=clean_name,
                    is_static=is_static,
                    is_wildcard=is_wildcard,
                    location=_location(child),
                    file_path=file_path,
                    repository=repository,
                    module=module,
                    package=package,
                )
            )
    return declarations
