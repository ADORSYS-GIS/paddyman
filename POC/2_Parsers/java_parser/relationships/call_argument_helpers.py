"""Argument metadata helpers for Java call relationship extraction."""
from __future__ import annotations

from tree_sitter import Node

from java_parser.java_ast.node_helpers import node_text
from java_parser.relationships.call_helpers import extract_constructor_type

_LITERAL_TYPES = {
    "string_literal": "String",
    "character_literal": "char",
    "true": "boolean",
    "false": "boolean",
    "null_literal": "null",
    "decimal_integer_literal": "int",
    "hex_integer_literal": "int",
    "octal_integer_literal": "int",
    "binary_integer_literal": "int",
    "decimal_floating_point_literal": "double",
    "hex_floating_point_literal": "double",
}


def _iter_argument_nodes(invocation_or_creation: Node) -> list[Node]:
    args_node = invocation_or_creation.child_by_field_name("arguments")
    if not args_node:
        return []
    return [n for n in args_node.children if n.type not in ("(", ")", ",")]


def infer_argument_type(arg_node: Node) -> str:
    """Infer a lightweight type label from an argument AST node."""
    if arg_node.type in _LITERAL_TYPES:
        return _LITERAL_TYPES[arg_node.type]
    if arg_node.type == "identifier":
        return "Unknown"
    if arg_node.type == "array_creation_expression":
        type_node = arg_node.child_by_field_name("type")
        base = node_text(type_node).strip() if type_node else "Object"
        return f"{base}[]"
    if arg_node.type == "object_creation_expression":
        return extract_constructor_type(arg_node) or "Object"
    if arg_node.type == "cast_expression":
        type_node = arg_node.child_by_field_name("type")
        return node_text(type_node).strip() if type_node else "Object"
    return "Unknown"


def extract_argument_types(invocation_or_creation: Node) -> list[str]:
    """Extract inferred argument type labels for a call node."""
    return [infer_argument_type(arg) for arg in _iter_argument_nodes(invocation_or_creation)]


def build_method_signature(method_name: str, argument_types: list[str]) -> str:
    """Build simple signature text from name and argument type labels."""
    return f"{method_name}({', '.join(argument_types)})"
