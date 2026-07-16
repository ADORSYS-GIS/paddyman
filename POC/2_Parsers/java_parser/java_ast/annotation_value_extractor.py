"""Extract annotation attribute values from Java AST nodes.

Parses ``annotation_argument_list`` nodes into structured attribute dicts
and builds :class:`~java_parser.java_ast.models.JavaAnnotation` instances
with fully-populated ``attributes`` fields.

Attribute values are extracted from the AST rather than raw text, covering
strings, numerics, booleans, enum references, arrays, and nested annotations.
"""
from __future__ import annotations

from typing import Any

from tree_sitter import Node

from .models import JavaAnnotation
from .node_helpers import child_of_type, node_text
from .annotation_node_values import (
    SKIP_TYPES,
    extract_element_value,
    find_value_node,
)


def extract_annotation_attributes(args_node: Node | None) -> dict[str, Any]:
    """Parse an ``annotation_argument_list`` node into an attributes dict.

    Named attributes (``key = value`` pairs) are stored by key name.
    A single unnamed value is stored under the conventional ``"value"`` key.
    Marker annotations (no args node) return an empty dict.

    Args:
        args_node: An ``annotation_argument_list`` node, or ``None``.

    Returns:
        Mapping of attribute names to their parsed values.
    """
    if args_node is None:
        return {}
    attrs: dict[str, Any] = {}
    single_values: list[Any] = []
    for child in args_node.children:
        if child.type in SKIP_TYPES:
            continue
        if child.type == "element_value_pair":
            key_node = child_of_type(child, "identifier")
            key = node_text(key_node) if key_node else ""
            value_node = find_value_node(child)
            if key and value_node is not None:
                attrs[key] = extract_element_value(value_node)
        else:
            single_values.append(extract_element_value(child))
    if not attrs and single_values:
        attrs["value"] = single_values[0] if len(single_values) == 1 else single_values
    return attrs


def extract_annotations_from_node(node: Node) -> list[JavaAnnotation]:
    """Extract fully-parsed :class:`JavaAnnotation` instances from an AST node.

    Iterates the direct children of *node* for ``marker_annotation`` and
    ``annotation`` child nodes.  Works on ``modifiers``, ``formal_parameter``,
    and any parent node that may have annotations as direct children.

    Attribute values are parsed from AST nodes rather than raw text, producing
    structured attributes for all Java annotation value types.

    Args:
        node: A tree-sitter node whose children may include annotations.

    Returns:
        List of :class:`JavaAnnotation` instances with populated ``attributes``.
    """
    result: list[JavaAnnotation] = []
    for child in node.children:
        if child.type == "marker_annotation":
            name = node_text(child_of_type(child, "identifier"))
            if name:
                result.append(JavaAnnotation(name=name))
        elif child.type == "annotation":
            name = node_text(child_of_type(child, "identifier"))
            if not name:
                continue
            args = child_of_type(child, "annotation_argument_list")
            attributes = extract_annotation_attributes(args)
            result.append(JavaAnnotation(name=name, attributes=attributes))
    return result

