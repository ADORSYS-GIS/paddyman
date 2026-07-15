"""Helper functions for method call and constructor call extraction.

These utilities extract metadata from tree-sitter AST nodes representing
method invocations and object creation expressions.
"""
from __future__ import annotations

from collections.abc import Generator

from tree_sitter import Node

from java_parser.java_ast.node_helpers import node_text


def walk_invocations(node: Node) -> Generator[Node, None, None]:
    """Yield every ``method_invocation`` node in the subtree rooted at *node*."""
    stack = [node]
    while stack:
        current = stack.pop()
        if current.type == "method_invocation":
            yield current
        stack.extend(reversed(current.children))


def walk_constructor_calls(node: Node) -> Generator[Node, None, None]:
    """Yield every ``object_creation_expression`` in the subtree rooted at *node*."""
    stack = [node]
    while stack:
        current = stack.pop()
        if current.type == "object_creation_expression":
            yield current
        stack.extend(reversed(current.children))


def extract_receiver(invocation: Node) -> str:
    """Return the raw receiver expression for *invocation*, or empty string."""
    obj = invocation.child_by_field_name("object")
    return node_text(obj).strip() if obj else ""


def extract_method_name(invocation: Node) -> str:
    """Return the called method name from a ``method_invocation`` node."""
    name_node = invocation.child_by_field_name("name")
    return node_text(name_node).strip() if name_node else ""


def extract_constructor_type(creation: Node) -> str:
    """Return the type being instantiated from an ``object_creation_expression``."""
    type_node = creation.child_by_field_name("type")
    if type_node:
        # Handle generic types like ArrayList<String>
        text = node_text(type_node).strip()
        # Extract just the base type name before <
        if "<" in text:
            return text.split("<")[0].strip()
        return text
    return ""


def count_arguments(invocation_or_creation: Node) -> int:
    """Count the number of arguments in a method call or constructor call."""
    args_node = invocation_or_creation.child_by_field_name("arguments")
    if not args_node:
        return 0
    # Count comma-separated expressions
    count = 0
    for child in args_node.children:
        if child.type not in ("(", ")", ","):
            count += 1
    return count


def is_static_call(invocation: Node) -> bool:
    """Determine if a method invocation is a static call.
    
    Heuristic: if the receiver contains a class-like identifier (starts with
    uppercase), assume static. This works for both simple names (Utils.method)
    and qualified names (com.example.Utils.method).
    
    This is syntactic analysis only; type resolution is deferred.
    """
    receiver = extract_receiver(invocation)
    if not receiver:
        return False
    
    # Check each segment - if any segment starts with uppercase, likely static
    segments = receiver.split(".")
    return any(seg and seg[0].isupper() for seg in segments)


def is_super_call(invocation: Node) -> bool:
    """Check if the invocation is a super call."""
    receiver = extract_receiver(invocation)
    return receiver == "super"


def is_this_call(invocation: Node) -> bool:
    """Check if the invocation is a this call."""
    receiver = extract_receiver(invocation)
    return receiver == "this"


def get_call_line_number(node: Node) -> int:
    """Return the 1-based line number where the call occurs."""
    return node.start_point[0] + 1


def find_method_body(method_node: Node) -> Node | None:
    """Find the body node of a method or constructor declaration.
    
    Returns the block or constructor_body child, or None if not found.
    """
    for child in method_node.children:
        if child.type in ("block", "constructor_body"):
            return child
    return None
