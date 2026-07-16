"""Dependency injection relationship extractor — orchestration layer.

Walks a tree-sitter Java AST root, locates class bodies, and delegates to the
injection detectors in :mod:`java_parser.di.injection_detector` for each
supported injection style (field, constructor, setter).

Compose on top of existing AST extraction:
1. Parse with :func:`~java_parser.java_ast.parser.parse_bytes`.
2. Produce metadata with :func:`~java_parser.java_ast.extractor.extract_file_ast`.
3. Extract DI relationships with :func:`extract_di_relationships`.
"""
from __future__ import annotations

import logging

from tree_sitter import Node

from java_parser.java_ast.extractor import extract_file_ast
from java_parser.java_ast.models import JavaFileAst
from java_parser.java_ast.node_helpers import child_of_type, node_text
from java_parser.java_ast.parser import parse_bytes
from java_parser.members._helpers import MemberContext
from java_parser.di.injection_detector import (
    extract_constructor_injections,
    extract_field_injections,
    extract_setter_injections,
)
from java_parser.di.models import DependencyRelationship

logger = logging.getLogger(__name__)

_CLASS_DECL_TYPES: frozenset[str] = frozenset(
    {"class_declaration", "interface_declaration", "enum_declaration"}
)

_BODY_TYPE: dict[str, str] = {
    "class_declaration": "class_body",
    "interface_declaration": "interface_body",
    "enum_declaration": "enum_body",
}


# ── Internal helpers ───────────────────────────────────────────────────────────


def _class_name(decl_node: Node) -> str:
    ident = child_of_type(decl_node, "identifier")
    return node_text(ident) if ident else ""


def _find_body(decl_node: Node) -> Node | None:
    body_type = _BODY_TYPE.get(decl_node.type, "class_body")
    for child in decl_node.children:
        if child.type == body_type:
            return child
    return None


def _process_declaration(
    decl_node: Node,
    file_ast: JavaFileAst,
) -> list[DependencyRelationship]:
    """Extract all DI relationships from a single type declaration."""
    body = _find_body(decl_node)
    if body is None:
        return []

    ctx = MemberContext(
        class_name=_class_name(decl_node),
        package=file_ast.package,
        file_path=file_ast.file_path,
        repository=file_ast.repository,
        module=file_ast.module,
    )

    results: list[DependencyRelationship] = []
    try:
        results.extend(extract_field_injections(body, ctx))
        results.extend(extract_constructor_injections(body, ctx))
        results.extend(extract_setter_injections(body, ctx))
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "Error extracting DI from %s in %s: %s",
            ctx.class_name,
            file_ast.file_path,
            exc,
        )
    return results


# ── Public API ─────────────────────────────────────────────────────────────────


def extract_di_relationships(
    root: Node,
    file_ast: JavaFileAst,
) -> list[DependencyRelationship]:
    """Extract Spring DI relationships from a tree-sitter AST root.

    Args:
        root:     Root node of the parsed Java source file.
        file_ast: Corresponding :class:`JavaFileAst` providing package,
                  file path, repository, and module context.

    Returns:
        List of :class:`DependencyRelationship` instances — one per injected
        dependency found across all class declarations in the file.
    """
    results: list[DependencyRelationship] = []
    for child in root.children:
        if child.type not in _CLASS_DECL_TYPES:
            continue
        results.extend(_process_declaration(child, file_ast))
    return results


def extract_di_from_source(
    source: bytes,
    *,
    file_path: str = "",
    repository: str = "",
    module: str = "",
) -> list[DependencyRelationship]:
    """Parse *source* bytes and extract Spring DI relationships.

    Convenience wrapper combining :func:`parse_bytes`,
    :func:`~java_parser.java_ast.extractor.extract_file_ast`, and
    :func:`extract_di_relationships`.

    Args:
        source:     Raw Java source bytes.
        file_path:  Repository-relative path (for provenance only).
        repository: Repository name (for provenance only).
        module:     Module label (for provenance only).
    """
    root = parse_bytes(source)
    file_ast = extract_file_ast(
        root, file_path=file_path, repository=repository, module=module
    )
    return extract_di_relationships(root, file_ast)
