"""Shared helpers for member extraction.

Provides type-string extraction and the :class:`MemberContext` provenance
carrier used by all member extractors.
"""
from __future__ import annotations

from dataclasses import dataclass

from tree_sitter import Node

from java_parser.java_ast.node_helpers import extract_modifiers, extract_annotation_names, node_text
from java_parser.java_ast.models import JavaAnnotation, SourceLocation

# Node types that represent Java types (return types, field types, param types).
_TYPE_NODE_KINDS: frozenset[str] = frozenset(
    {
        "type_identifier",
        "generic_type",
        "integral_type",
        "boolean_type",
        "void_type",
        "array_type",
        "floating_point_type",
        "scoped_type_identifier",
        "annotated_type",
        "wildcard",
    }
)


@dataclass(frozen=True)
class MemberContext:
    """Provenance metadata shared by all member extractors.

    Args:
        class_name:  Simple name of the enclosing class.
        package:     Java package of the enclosing file.
        file_path:   Repository-relative source file path.
        repository:  Repository name.
        module:      Module label.
    """

    class_name: str
    package: str
    file_path: str
    repository: str
    module: str


def extract_type_str(node: Node | None) -> str:
    """Return the full type string from a type AST node.

    Returns the raw text content of the node, which is the most accurate
    representation for all type variants (generic, array, primitive, etc.).

    Args:
        node: Any tree-sitter node representing a Java type.
    """
    return node_text(node)


def first_type_child(node: Node) -> Node | None:
    """Return the first child of *node* that is a recognised type node.

    Args:
        node: Parent node whose children are inspected.
    """
    for child in node.children:
        if child.type in _TYPE_NODE_KINDS:
            return child
    return None


def get_modifiers(node: Node) -> list[str]:
    """Extract keyword modifiers from a member AST node.

    Finds the ``modifiers`` child and delegates to
    :func:`~java_parser.java_ast.node_helpers.extract_modifiers`.

    Args:
        node: A method, field, or constructor declaration node.
    """
    for child in node.children:
        if child.type == "modifiers":
            return extract_modifiers(child)
    return []


def get_annotations(node: Node) -> list[JavaAnnotation]:
    """Return annotation names applied to a member AST node.

    Finds the ``modifiers`` child and extracts annotation names (without
    the ``@`` prefix) for all ``marker_annotation`` and ``annotation`` nodes.

    Args:
        node: A method, field, or constructor declaration node.
    """
    for child in node.children:
        if child.type == "modifiers":
            return [
                JavaAnnotation(name=name, value=value)
                for name, value in extract_annotation_names(child)
            ]
    return []


def make_location(node: Node) -> SourceLocation:
    """Build a :class:`SourceLocation` from a tree-sitter node's position."""
    sr, sc = node.start_point
    er, ec = node.end_point
    return SourceLocation(sr, sc, er, ec)
