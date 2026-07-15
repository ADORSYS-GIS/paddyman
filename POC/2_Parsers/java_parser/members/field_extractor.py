"""Field extraction from Java class bodies.

Extracts :class:`~.models.JavaField` instances from ``field_declaration``
nodes in a tree-sitter Java parse tree.
"""
from __future__ import annotations

import logging
from tree_sitter import Node

from java_parser.java_ast.node_helpers import node_text

from .models import JavaField
from ._helpers import MemberContext, extract_type_str, first_type_child, get_annotations, get_modifiers, make_location

logger = logging.getLogger(__name__)


def _extract_field_name(field_node: Node) -> str:
    """Return the field identifier from a ``field_declaration`` node."""
    for child in field_node.children:
        if child.type == "variable_declarator":
            # First identifier child of variable_declarator is the field name
            for sub in child.children:
                if sub.type == "identifier":
                    return node_text(sub)
    return ""


def extract_fields(class_body: Node, ctx: MemberContext) -> list[JavaField]:
    """Extract all field declarations from *class_body*.

    Each ``field_declaration`` may declare multiple variables but tree-sitter
    emits one ``variable_declarator`` per variable — this implementation
    produces one :class:`JavaField` per declarator.

    Args:
        class_body: A ``class_body`` tree-sitter node.
        ctx:        Provenance metadata for the enclosing class.

    Returns:
        List of :class:`JavaField` instances.
    """
    fields: list[JavaField] = []
    for member in class_body.children:
        if member.type != "field_declaration":
            continue
        try:
            fields.extend(_extract_field_node(member, ctx))
        except Exception as exc:  # noqa: BLE001
            logger.warning("Skipping field in %s.%s: %s", ctx.class_name, ctx.file_path, exc)
    return fields


def _extract_field_node(field_node: Node, ctx: MemberContext) -> list[JavaField]:
    """Extract one or more :class:`JavaField` instances from a single field_declaration."""
    modifiers = get_modifiers(field_node)
    annotations = get_annotations(field_node)
    type_node = first_type_child(field_node)
    type_str = extract_type_str(type_node) if type_node else ""

    results: list[JavaField] = []
    for child in field_node.children:
        if child.type != "variable_declarator":
            continue
        name = ""
        for sub in child.children:
            if sub.type == "identifier":
                name = node_text(sub)
                break
        if not name:
            continue
        results.append(
            JavaField(
                name=name,
                type=type_str,
                modifiers=modifiers,
                annotations=annotations,
                class_name=ctx.class_name,
                package=ctx.package,
                file_path=ctx.file_path,
                repository=ctx.repository,
                module=ctx.module,
                location=make_location(field_node),
            )
        )
    return results
