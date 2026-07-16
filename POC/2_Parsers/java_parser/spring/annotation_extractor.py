"""Low-level Spring annotation extraction from tree-sitter AST nodes.

Responsible for locating ``marker_annotation`` and ``annotation`` nodes in
a Java class ``modifiers`` subtree and converting them to
:class:`~java_parser.spring.models.SpringAnnotation` instances.

Deliberately limited to node traversal — classification and result assembly
are handled by :mod:`java_parser.spring.classifier`.
"""
from __future__ import annotations

import logging

from tree_sitter import Node

from java_parser.java_ast.node_helpers import child_of_type, node_text
from java_parser.spring.models import SPRING_ANNOTATION_NAMES, SpringAnnotation

logger = logging.getLogger(__name__)

_ANNOTATION_NODE_TYPES: frozenset[str] = frozenset(
    {"annotation", "marker_annotation"}
)
_IGNORED_ARGUMENT_TOKENS: frozenset[str] = frozenset({"(", ")", ","})


# ── Annotation name ────────────────────────────────────────────────────────────


def _annotation_name(node: Node) -> str:
    """Return the simple annotation name from an annotation/marker_annotation node."""
    for child in node.children:
        if child.type in ("identifier", "scoped_type_identifier", "type_identifier"):
            return node_text(child)
    return ""


# ── Annotation value extraction ────────────────────────────────────────────────


def _strip_quotes(text: str) -> str:
    """Remove surrounding double-quotes from a string literal text."""
    if len(text) >= 2 and text[0] == '"' and text[-1] == '"':
        return text[1:-1]
    return text


def _extract_element_value_pair(node: Node) -> tuple[str, str]:
    """Return ``(key, value)`` from an ``element_value_pair`` node."""
    key = ""
    val = ""
    for child in node.children:
        if child.type == "=":
            continue
        if not key:
            key = node_text(child)
        else:
            val = _strip_quotes(node_text(child))
    return key, val


def _collect_string_values(node: Node) -> list[str]:
    """Recursively collect string literal values from *node*."""
    values: list[str] = []
    for child in node.children:
        if child.type == "string_literal":
            values.append(_strip_quotes(node_text(child)))
        elif child.type not in _IGNORED_ARGUMENT_TOKENS:
            values.extend(_collect_string_values(child))
    return values


def _extract_annotation_args(
    node: Node,
) -> tuple[str | None, dict[str, str]]:
    """Extract the primary value and named attributes from an annotation node.

    Returns a ``(primary_value, attributes)`` pair where *primary_value* is
    the un-named argument (e.g. ``"/api/v1"`` in ``@RequestMapping("/api/v1")``)
    and *attributes* are named element–value pairs.
    """
    arg_list = child_of_type(node, "annotation_argument_list")
    if arg_list is None:
        return None, {}

    primary_value: str | None = None
    attributes: dict[str, str] = {}

    for child in arg_list.children:
        if child.type in _IGNORED_ARGUMENT_TOKENS:
            continue
        if child.type == "element_value_pair":
            key, val = _extract_element_value_pair(child)
            if key:
                attributes[key] = val
        elif child.type == "string_literal":
            primary_value = _strip_quotes(node_text(child))
        # element_value_array_initializer — collect first string value
        elif child.type == "element_value_array_initializer":
            collected = _collect_string_values(child)
            if collected:
                primary_value = collected[0]
                if len(collected) > 1:
                    attributes["_extra_paths"] = ",".join(collected[1:])

    return primary_value, attributes


# ── Public extraction function ─────────────────────────────────────────────────


def extract_spring_annotations(modifiers_node: Node) -> list[SpringAnnotation]:
    """Return Spring annotations found in a ``modifiers`` AST node.

    Only annotations whose names appear in
    :data:`~java_parser.spring.models.SPRING_ANNOTATION_NAMES` are included.

    Args:
        modifiers_node: A ``modifiers`` tree-sitter node from a class declaration.

    Returns:
        Ordered list of :class:`SpringAnnotation` instances.
    """
    results: list[SpringAnnotation] = []
    for child in modifiers_node.children:
        if child.type not in _ANNOTATION_NODE_TYPES:
            continue
        name = _annotation_name(child)
        if not name or name not in SPRING_ANNOTATION_NAMES:
            continue
        try:
            if child.type == "marker_annotation":
                results.append(SpringAnnotation(name=name))
            else:
                value, attributes = _extract_annotation_args(child)
                results.append(
                    SpringAnnotation(name=name, value=value, attributes=attributes)
                )
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to extract annotation %s: %s", name, exc)
    return results
