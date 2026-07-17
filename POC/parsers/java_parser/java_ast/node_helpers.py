"""AST node traversal helpers.

Low-level utilities for navigating tree-sitter Java nodes.  Kept separate
from the extractor so each file stays under the 150 LOC limit.
"""
from __future__ import annotations

from tree_sitter import Node

# Modifier-type node names that are NOT Java keyword modifiers
_ANNOTATION_TYPES: frozenset[str] = frozenset(
    {"annotation", "marker_annotation", "element_value_pair"}
)

_JAVA_MODIFIERS: frozenset[str] = frozenset(
    {
        "public", "private", "protected", "static", "final", "abstract",
        "synchronized", "native", "transient", "volatile", "strictfp",
        "default", "sealed", "non-sealed",
    }
)


def node_text(node: Node | None) -> str:
    """Return UTF-8 decoded text of *node*, or an empty string when None."""
    if node is None or node.text is None:
        return ""
    return node.text.decode("utf-8", errors="replace")


def child_of_type(node: Node, *types: str) -> Node | None:
    """Return the first direct child of *node* matching any of *types*."""
    for child in node.children:
        if child.type in types:
            return child
    return None


def children_of_type(node: Node, *types: str) -> list[Node]:
    """Return all direct children of *node* matching any of *types*."""
    return [c for c in node.children if c.type in types]


def extract_modifiers(node: Node) -> list[str]:
    """Return the Java keyword modifiers from a ``modifiers`` AST node.

    Annotation child nodes (e.g. ``@Deprecated``) are excluded.

    Args:
        node: A ``modifiers`` tree-sitter node.
    """
    result: list[str] = []
    for child in node.children:
        if child.type not in _ANNOTATION_TYPES and child.type in _JAVA_MODIFIERS:
            text = node_text(child).strip()
            if text:
                result.append(text)
    return result


def extract_type_list(node: Node | None) -> list[str]:
    """Return a list of simple type names from a ``type_list`` node.

    Handles ``super_interfaces``, ``extends_interfaces``, and plain
    ``type_list`` nodes by extracting the comma-separated type names.

    Args:
        node: The container node (``super_interfaces`` or similar).
    """
    if node is None:
        return []

    # Look for a nested type_list node first
    type_list_node = child_of_type(node, "type_list")
    if type_list_node is None:
        type_list_node = node

    result: list[str] = []
    for child in type_list_node.children:
        if child.type in (",", "implements", "extends", "type_list"):
            continue
        text = node_text(child).strip()
        if text:
            # Strip generic parameters: Foo<Bar> → Foo
            base = text.split("<")[0].strip()
            if base:
                result.append(base)
    return result


def extract_superclass(node: Node | None) -> str | None:
    """Return the simple superclass name from a ``superclass`` node.

    Args:
        node: The ``superclass`` tree-sitter node (``extends Foo``).
    """
    if node is None:
        return None
    # The superclass node children: ['extends', identifier_or_scoped]
    for child in node.children:
        if child.type not in ("extends",):
            text = node_text(child).split("<")[0].strip()
            if text:
                return text
    return None


def extract_import(node: Node) -> str:
    """Reconstruct the fully-qualified import name from an import_declaration.

    Handles both regular and ``static`` imports, including wildcard ``.*``.

    Args:
        node: An ``import_declaration`` tree-sitter node.
    """
    parts: list[str] = []
    is_static = False
    for child in node.children:
        if child.type == "import":
            continue
        if child.type == "static":
            is_static = True
            continue
        if child.type == ";":
            continue
        if child.type == "asterisk":
            parts.append("*")
            continue
        if child.type == ".":
            # separator before wildcard — already handled by parts joining
            if parts and parts[-1] != ".":
                parts.append(".")
            continue
        text = node_text(child).strip()
        if text:
            parts.append(text)
    name = "".join(parts)
    return f"static {name}" if is_static else name
