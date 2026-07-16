"""Primitive value extraction from Java annotation AST nodes.

Provides low-level helpers for converting individual tree-sitter nodes
into Python values (strings, lists, raw text) used during annotation
attribute extraction.
"""
from __future__ import annotations

from typing import Any

from tree_sitter import Node

from .node_helpers import node_text

# ── Node type sets ─────────────────────────────────────────────────────────────

_STRING_LITERAL_TYPES: frozenset[str] = frozenset({"string_literal"})

_NUMERIC_LITERAL_TYPES: frozenset[str] = frozenset({
    "decimal_integer_literal", "hex_integer_literal", "octal_integer_literal",
    "binary_integer_literal", "decimal_floating_point_literal",
    "hex_floating_point_literal", "character_literal",
})

_BOOLEAN_TYPES: frozenset[str] = frozenset({"true", "false"})
_NULL_TYPES: frozenset[str] = frozenset({"null_literal"})

_SIMPLE_REF_TYPES: frozenset[str] = frozenset(
    {"identifier", "type_identifier", "field_access", "scoped_type_identifier"}
)

# Structural tokens to skip when iterating argument lists
SKIP_TYPES: frozenset[str] = frozenset({"(", ")", ",", "="})


# ── Value extraction helpers ───────────────────────────────────────────────────


def extract_element_value(node: Node) -> Any:
    """Convert a single annotation value AST node to a Python value.

    - String literals: surrounding quotes are stripped.
    - Numeric, boolean, null: returned as raw text.
    - Simple and field references (enum refs): returned as raw text.
    - Array initialisers: returned as a list of values.
    - All other expressions (nested annotations, calls): raw text.

    Args:
        node: AST node representing one annotation element value.

    Returns:
        ``str`` or ``list[Any]`` depending on value type.
    """
    ntype = node.type
    if ntype in _STRING_LITERAL_TYPES:
        text = node_text(node)
        return text[1:-1] if len(text) >= 2 else text
    if ntype in _NUMERIC_LITERAL_TYPES or ntype in _BOOLEAN_TYPES or ntype in _NULL_TYPES:
        return node_text(node)
    if ntype in _SIMPLE_REF_TYPES:
        return node_text(node)
    if ntype in ("array_initializer", "element_value_array_initializer"):
        return extract_array_value(node)
    return node_text(node)


def extract_array_value(array_node: Node) -> list[Any]:
    """Extract values from an ``array_initializer`` node.

    Args:
        array_node: An ``array_initializer`` tree-sitter node.

    Returns:
        Ordered list of element values.
    """
    results: list[Any] = []
    for child in array_node.children:
        if child.type in SKIP_TYPES or child.type in ("{", "}"):
            continue
        results.append(extract_element_value(child))
    return results


def find_value_node(pair_node: Node) -> Node | None:
    """Return the value node from an ``element_value_pair`` node.

    Iterates children of *pair_node* and returns the first node after ``=``.

    Args:
        pair_node: An ``element_value_pair`` tree-sitter node.

    Returns:
        The value child node, or ``None`` if not found.
    """
    found_eq = False
    for child in pair_node.children:
        if child.type == "=":
            found_eq = True
            continue
        if found_eq:
            return child
    return None
