"""Extract type declarations (class, interface, enum) from Java AST nodes.

Handles extraction of modifiers, annotations, inheritance, and interfaces
for all Java type declaration kinds.
"""
from __future__ import annotations

from tree_sitter import Node

from .models import (
    JavaDeclarationType,
    JavaTypeDeclaration,
    SourceLocation,
)
from .node_helpers import (
    child_of_type,
    extract_modifiers,
    extract_superclass,
    extract_type_list,
    node_text,
)
from .annotation_value_extractor import extract_annotations_from_node


def _location(node: Node) -> SourceLocation:
    """Convert tree-sitter node to SourceLocation."""
    sr, sc = node.start_point
    er, ec = node.end_point
    return SourceLocation(sr, sc, er, ec)


def _get_annotations(node: Node) -> list[JavaAnnotation]:
    """Extract all annotations from the ``modifiers`` child of *node*."""
    mods_node = child_of_type(node, "modifiers")
    if mods_node is None:
        return []
    return extract_annotations_from_node(mods_node)


def extract_class(
    node: Node, package: str, file_path: str, repository: str, module: str
) -> JavaTypeDeclaration:
    """Extract a class declaration from AST node."""
    mods_node = child_of_type(node, "modifiers")
    modifiers = extract_modifiers(mods_node) if mods_node else []
    annotations = _get_annotations(node)
    name = node_text(child_of_type(node, "identifier"))
    superclass = extract_superclass(child_of_type(node, "superclass"))
    ifaces_node = child_of_type(node, "super_interfaces")
    interfaces = extract_type_list(ifaces_node)
    return JavaTypeDeclaration(
        type=JavaDeclarationType.CLASS,
        name=name,
        package=package,
        modifiers=modifiers,
        annotations=annotations,
        superclass=superclass,
        interfaces=interfaces,
        location=_location(node),
        file_path=file_path,
        repository=repository,
        module=module,
    )


def extract_interface(
    node: Node, package: str, file_path: str, repository: str, module: str
) -> JavaTypeDeclaration:
    """Extract an interface declaration from AST node."""
    mods_node = child_of_type(node, "modifiers")
    modifiers = extract_modifiers(mods_node) if mods_node else []
    annotations = _get_annotations(node)
    name = node_text(child_of_type(node, "identifier"))
    extends_node = child_of_type(node, "extends_interfaces")
    interfaces = extract_type_list(extends_node)
    return JavaTypeDeclaration(
        type=JavaDeclarationType.INTERFACE,
        name=name,
        package=package,
        modifiers=modifiers,
        annotations=annotations,
        superclass=None,
        interfaces=interfaces,
        location=_location(node),
        file_path=file_path,
        repository=repository,
        module=module,
    )


def extract_enum(
    node: Node, package: str, file_path: str, repository: str, module: str
) -> JavaTypeDeclaration:
    """Extract an enum declaration from AST node."""
    mods_node = child_of_type(node, "modifiers")
    modifiers = extract_modifiers(mods_node) if mods_node else []
    annotations = _get_annotations(node)
    name = node_text(child_of_type(node, "identifier"))
    ifaces_node = child_of_type(node, "super_interfaces")
    interfaces = extract_type_list(ifaces_node)
    return JavaTypeDeclaration(
        type=JavaDeclarationType.ENUM,
        name=name,
        package=package,
        modifiers=modifiers,
        annotations=annotations,
        superclass=None,
        interfaces=interfaces,
        location=_location(node),
        file_path=file_path,
        repository=repository,
        module=module,
    )


# Map AST node types to their extraction functions
DECLARATION_EXTRACTORS = {
    "class_declaration": extract_class,
    "interface_declaration": extract_interface,
    "enum_declaration": extract_enum,
}
