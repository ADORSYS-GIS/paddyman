"""Method extraction from Java class bodies.

Extracts :class:`~.models.JavaMethod` instances from ``method_declaration``
nodes in a tree-sitter Java parse tree.
"""
from __future__ import annotations

import logging
from tree_sitter import Node

from java_parser.java_ast.node_helpers import node_text

from .models import JavaMethod
from ._helpers import MemberContext, extract_type_str, get_annotations, get_modifiers, make_location
from .parameter_extractor import extract_parameters

logger = logging.getLogger(__name__)

# Return-type node kinds (excluding void_type, which is also valid).
_RETURN_TYPE_KINDS: frozenset[str] = frozenset(
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
    }
)


def _extract_return_type(method_node: Node) -> str:
    """Return the return type string for a method_declaration node.

    Skips ``modifiers`` and ``type_parameters`` children and returns the
    first remaining type-node text.
    """
    skip = {"modifiers", "type_parameters"}
    for child in method_node.children:
        if child.type in skip:
            continue
        if child.type in _RETURN_TYPE_KINDS:
            return extract_type_str(child)
    return ""


def _extract_method_name(method_node: Node) -> str:
    """Return the method identifier from a method_declaration node."""
    for child in method_node.children:
        if child.type == "identifier":
            return node_text(child)
    return ""


def _extract_formal_params(method_node: Node) -> Node | None:
    """Return the formal_parameters child of a method_declaration node."""
    for child in method_node.children:
        if child.type == "formal_parameters":
            return child
    return None


def extract_methods(class_body: Node, ctx: MemberContext) -> list[JavaMethod]:
    """Extract all method declarations from *class_body*.

    Args:
        class_body: A ``class_body`` or ``interface_body`` tree-sitter node.
        ctx:        Provenance metadata for the enclosing class.

    Returns:
        List of :class:`JavaMethod` instances.
    """
    methods: list[JavaMethod] = []
    for member in class_body.children:
        if member.type != "method_declaration":
            continue
        try:
            method = _extract_method(member, ctx)
            if method:
                methods.append(method)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Skipping method in %s.%s: %s", ctx.class_name, ctx.file_path, exc
            )
    return methods


def _extract_method(method_node: Node, ctx: MemberContext) -> JavaMethod | None:
    """Build a :class:`JavaMethod` from a ``method_declaration`` node."""
    name = _extract_method_name(method_node)
    if not name:
        return None

    modifiers = get_modifiers(method_node)
    annotations = get_annotations(method_node)
    return_type = _extract_return_type(method_node)
    params_node = _extract_formal_params(method_node)
    params = extract_parameters(params_node) if params_node else []
    location = make_location(method_node)

    return JavaMethod(
        name=name,
        return_type=return_type,
        modifiers=modifiers,
        annotations=annotations,
        parameters=params,
        class_name=ctx.class_name,
        package=ctx.package,
        file_path=ctx.file_path,
        repository=ctx.repository,
        module=ctx.module,
        location=location,
    )
