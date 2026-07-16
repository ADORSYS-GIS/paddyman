"""Low-level DI annotation detection and member-level injection extraction.

Provides helpers that inspect individual AST member nodes (field declarations,
constructor declarations, method declarations) for Spring injection annotations
and build :class:`~java_parser.di.models.DependencyRelationship` objects.

This module does **not** walk the file-level AST — that is handled by
:mod:`java_parser.di.extractor`.
"""
from __future__ import annotations

import logging

from tree_sitter import Node

from java_parser.java_ast.node_helpers import node_text
from java_parser.members._helpers import MemberContext, extract_type_str, first_type_child
from java_parser.members.parameter_extractor import extract_parameters
from java_parser.di.models import DependencyRelationship, InjectionType

logger = logging.getLogger(__name__)

# Recognised injection annotations (simple names only)
INJECTION_ANNOTATIONS: frozenset[str] = frozenset(
    {"Autowired", "Inject", "Resource"}
)

# Java primitives that are never injectable Spring beans
_JAVA_PRIMITIVES: frozenset[str] = frozenset(
    {"int", "long", "double", "float", "boolean", "char", "byte", "short", "void"}
)

_RELATIONSHIP_TYPE = "USES"


# ── Annotation helpers ─────────────────────────────────────────────────────────


def _annotation_name(node: Node) -> str:
    """Return the simple name from a marker_annotation or annotation node."""
    for child in node.children:
        if child.type in ("identifier", "type_identifier", "scoped_type_identifier"):
            return node_text(child)
    return ""


def has_injection_annotation(member_node: Node) -> bool:
    """Return True if *member_node* carries an injection annotation."""
    for child in member_node.children:
        if child.type != "modifiers":
            continue
        for mod in child.children:
            if mod.type in ("marker_annotation", "annotation"):
                if _annotation_name(mod) in INJECTION_ANNOTATIONS:
                    return True
    return False


def _is_injectable_type(type_str: str) -> bool:
    """Return False for primitives that cannot be Spring beans."""
    return type_str not in _JAVA_PRIMITIVES and bool(type_str)


# ── Field injection ────────────────────────────────────────────────────────────


def _field_name(field_node: Node) -> str:
    """Return the first declared variable name from a field_declaration."""
    for child in field_node.children:
        if child.type == "variable_declarator":
            for sub in child.children:
                if sub.type == "identifier":
                    return node_text(sub)
    return ""


def extract_field_injections(
    class_body: Node, ctx: MemberContext
) -> list[DependencyRelationship]:
    """Extract @Autowired/@Inject/@Resource field injections from *class_body*."""
    results: list[DependencyRelationship] = []
    for node in class_body.children:
        if node.type != "field_declaration":
            continue
        if not has_injection_annotation(node):
            continue
        type_node = first_type_child(node)
        target = extract_type_str(type_node).split("<")[0].strip() if type_node else ""
        if not _is_injectable_type(target):
            continue
        field_nm = _field_name(node)
        results.append(
            DependencyRelationship(
                source=ctx.class_name, target=target,
                relationship_type=_RELATIONSHIP_TYPE,
                injection_type=InjectionType.FIELD.value,
                field_name=field_nm or None,
                package=ctx.package, file_path=ctx.file_path,
                repository=ctx.repository, module=ctx.module,
            )
        )
    return results


# ── Constructor injection ──────────────────────────────────────────────────────


def _constructor_params(ctor_node: Node) -> list[tuple[str, str]]:
    """Return ``[(type, name), ...]`` for a constructor_declaration node."""
    for child in ctor_node.children:
        if child.type == "formal_parameters":
            params = extract_parameters(child)
            return [(p.type.split("<")[0].strip(), p.name) for p in params]
    return []


def extract_constructor_injections(
    class_body: Node, ctx: MemberContext
) -> list[DependencyRelationship]:
    """Extract constructor-injected dependencies from *class_body*.

    Detects:
    - Constructors explicitly annotated with @Autowired / @Inject / @Resource.
    - The single constructor of a class (Spring 4.3+ implicit injection)
      when it has at least one parameter.
    """
    ctors = [n for n in class_body.children if n.type == "constructor_declaration"]
    results: list[DependencyRelationship] = []

    for ctor in ctors:
        explicit = has_injection_annotation(ctor)
        implicit = len(ctors) == 1  # Spring 4.3+: single constructor
        if not (explicit or implicit):
            continue
        for type_str, _ in _constructor_params(ctor):
            if not _is_injectable_type(type_str):
                continue
            results.append(
                DependencyRelationship(
                    source=ctx.class_name, target=type_str,
                    relationship_type=_RELATIONSHIP_TYPE,
                    injection_type=InjectionType.CONSTRUCTOR.value,
                    field_name=None,
                    package=ctx.package, file_path=ctx.file_path,
                    repository=ctx.repository, module=ctx.module,
                )
            )
    return results


# ── Setter injection ───────────────────────────────────────────────────────────


def _method_name(method_node: Node) -> str:
    """Return the identifier from a method_declaration node."""
    for child in method_node.children:
        if child.type == "identifier":
            return node_text(child)
    return ""


def extract_setter_injections(
    class_body: Node, ctx: MemberContext
) -> list[DependencyRelationship]:
    """Extract @Autowired setter-injected dependencies from *class_body*."""
    results: list[DependencyRelationship] = []
    for node in class_body.children:
        if node.type != "method_declaration":
            continue
        if not has_injection_annotation(node):
            continue
        for child in node.children:
            if child.type == "formal_parameters":
                params = extract_parameters(child)
                for p in params:
                    type_str = p.type.split("<")[0].strip()
                    if not _is_injectable_type(type_str):
                        continue
                    results.append(
                        DependencyRelationship(
                            source=ctx.class_name, target=type_str,
                            relationship_type=_RELATIONSHIP_TYPE,
                            injection_type=InjectionType.SETTER.value,
                            field_name=_method_name(node) or None,
                            package=ctx.package, file_path=ctx.file_path,
                            repository=ctx.repository, module=ctx.module,
                        )
                    )
    return results
