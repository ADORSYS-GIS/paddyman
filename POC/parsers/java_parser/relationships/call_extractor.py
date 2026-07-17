"""Method-call and constructor-call relationship extraction from tree-sitter AST.

Walks method bodies and yields CALLS relationships for every method_invocation
and object_creation_expression node. Receiver expressions are stored as-is;
type resolution is deferred to the graph normalisation stage.
"""
from __future__ import annotations

import logging

from tree_sitter import Node

from java_parser.java_ast.node_helpers import child_of_type, node_text
from java_parser.members._helpers import MemberContext
from java_parser.relationships.call_helpers import (
    extract_constructor_type,
    extract_method_name,
    extract_receiver,
    find_method_body,
    get_call_line_number,
    walk_constructor_calls,
    walk_invocations,
)
from java_parser.relationships.models import JavaRelationship
from java_parser.relationships.relationship_builders import (
    create_constructor_call_relationship,
    create_method_call_relationship,
)

logger = logging.getLogger(__name__)

_CLASS_DECL_TYPES: frozenset[str] = frozenset(
    {"class_declaration", "interface_declaration", "enum_declaration"}
)
_BODY_TYPE: dict[str, str] = {
    "class_declaration": "class_body",
    "interface_declaration": "interface_body",
    "enum_declaration": "enum_body",
}


def _extract_calls_from_method(
    method_node: Node,
    ctx: MemberContext,
) -> list[JavaRelationship]:
    """Extract CALLS relationships from a single method or constructor node."""
    source_method_node = child_of_type(method_node, "identifier")
    source_method = node_text(source_method_node) if source_method_node else ""

    body = find_method_body(method_node)
    if body is None:
        return []

    results: list[JavaRelationship] = []
    seen: set[tuple[str, str]] = set()  # (target, source_method) for deduplication

    # Extract method invocations
    for inv in walk_invocations(body):
        method = extract_method_name(inv)
        if not method:
            continue

        receiver = extract_receiver(inv)
        target_str = f"{receiver}.{method}" if receiver else method
        
        dedup_key = (target_str, source_method)
        if dedup_key in seen:
            continue
        seen.add(dedup_key)

        results.append(create_method_call_relationship(inv, source_method, ctx))

    # Extract constructor calls
    for creation in walk_constructor_calls(body):
        constructor_type = extract_constructor_type(creation)
        if not constructor_type:
            continue

        dedup_key = (constructor_type, source_method)
        if dedup_key in seen:
            continue
        seen.add(dedup_key)

        results.append(create_constructor_call_relationship(creation, source_method, ctx))

    return results


def extract_call_relationships(
    root: Node,
    file_path: str,
    repository: str,
    module: str,
    package: str,
) -> list[JavaRelationship]:
    """Extract CALLS relationships from all class declarations in *root*.

    Args:
        root:       Root node of the parsed Java source file.
        file_path:  Repository-relative source file path.
        repository: Repository name.
        module:     Module label.
        package:    Package of the file.

    Returns:
        List of ``CALLS`` :class:`JavaRelationship` instances including both
        method invocations and constructor calls.
    """
    results: list[JavaRelationship] = []
    for decl in root.children:
        if decl.type not in _CLASS_DECL_TYPES:
            continue

        class_name_node = child_of_type(decl, "identifier")
        class_name = node_text(class_name_node) if class_name_node else ""

        body_type = _BODY_TYPE.get(decl.type, "class_body")
        body: Node | None = None
        for child in decl.children:
            if child.type == body_type:
                body = child
                break
        if body is None:
            continue

        ctx = MemberContext(
            class_name=class_name,
            package=package,
            file_path=file_path,
            repository=repository,
            module=module,
        )

        for member in body.children:
            if member.type not in ("method_declaration", "constructor_declaration"):
                continue
            try:
                results.extend(_extract_calls_from_method(member, ctx))
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "Skipping call extraction in %s.%s: %s",
                    class_name, file_path, exc,
                )
    return results


