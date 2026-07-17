"""Constructor extraction from Java class bodies.

Extracts :class:`~.models.JavaConstructor` instances from
``constructor_declaration`` nodes in a tree-sitter Java parse tree.
"""
from __future__ import annotations

import logging
from tree_sitter import Node

from java_parser.java_ast.node_helpers import node_text

from .models import JavaConstructor
from ._helpers import MemberContext, get_annotations, get_modifiers, make_location
from .parameter_extractor import extract_parameters

logger = logging.getLogger(__name__)


def extract_constructors(class_body: Node, ctx: MemberContext) -> list[JavaConstructor]:
    """Extract all constructor declarations from *class_body*.

    Args:
        class_body: A ``class_body`` tree-sitter node.
        ctx:        Provenance metadata for the enclosing class.

    Returns:
        List of :class:`JavaConstructor` instances.
    """
    constructors: list[JavaConstructor] = []
    for member in class_body.children:
        if member.type != "constructor_declaration":
            continue
        try:
            ctor = _extract_constructor(member, ctx)
            if ctor:
                constructors.append(ctor)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Skipping constructor in %s.%s: %s",
                ctx.class_name,
                ctx.file_path,
                exc,
            )
    return constructors


def _extract_constructor_name(ctor_node: Node) -> str:
    """Return the constructor name (class name) from a constructor_declaration."""
    for child in ctor_node.children:
        if child.type == "identifier":
            return node_text(child)
    return ""


def _extract_formal_params(ctor_node: Node) -> Node | None:
    """Return the formal_parameters child of a constructor_declaration."""
    for child in ctor_node.children:
        if child.type == "formal_parameters":
            return child
    return None


def _extract_constructor(
    ctor_node: Node, ctx: MemberContext
) -> JavaConstructor | None:
    """Build a :class:`JavaConstructor` from a ``constructor_declaration`` node."""
    name = _extract_constructor_name(ctor_node)
    if not name:
        return None

    modifiers = get_modifiers(ctor_node)
    annotations = get_annotations(ctor_node)
    params_node = _extract_formal_params(ctor_node)
    params = extract_parameters(params_node) if params_node else []
    location = make_location(ctor_node)

    return JavaConstructor(
        name=name,
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
