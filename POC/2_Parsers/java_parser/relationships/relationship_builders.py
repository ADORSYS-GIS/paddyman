"""Builders for creating JavaRelationship instances from AST nodes.

Constructs fully populated JavaRelationship objects for method calls and
constructor calls with all required metadata.
"""
from __future__ import annotations

from tree_sitter import Node

from java_parser.members._helpers import MemberContext
from java_parser.relationships.call_helpers import (
    count_arguments,
    extract_constructor_type,
    extract_method_name,
    extract_receiver,
    get_call_line_number,
    is_static_call,
)
from java_parser.relationships.models import JavaRelationship, RelationshipType


def create_method_call_relationship(
    inv: Node,
    source_method: str,
    ctx: MemberContext,
) -> JavaRelationship:
    """Create a CALLS relationship from a method_invocation node.
    
    Args:
        inv: The method_invocation AST node.
        source_method: Name of the enclosing method.
        ctx: Context containing class name, package, file path, etc.
        
    Returns:
        A JavaRelationship for the method call.
    """
    receiver = extract_receiver(inv)
    method = extract_method_name(inv)
    target_str = f"{receiver}.{method}" if receiver else method
    
    return JavaRelationship(
        source=ctx.class_name,
        target=target_str,
        relationship_type=RelationshipType.CALLS.value,
        package=ctx.package,
        file_path=ctx.file_path,
        repository=ctx.repository,
        module=ctx.module,
        source_method=source_method or None,
        target_method=method,
        target_class=receiver or None,
        call_site_line=get_call_line_number(inv),
        arguments_count=count_arguments(inv),
        is_static=is_static_call(inv) if receiver else None,
        is_constructor=False,
    )


def create_constructor_call_relationship(
    creation: Node,
    source_method: str,
    ctx: MemberContext,
) -> JavaRelationship:
    """Create a CALLS relationship from an object_creation_expression node.
    
    Args:
        creation: The object_creation_expression AST node.
        source_method: Name of the enclosing method.
        ctx: Context containing class name, package, file path, etc.
        
    Returns:
        A JavaRelationship for the constructor call.
    """
    constructor_type = extract_constructor_type(creation)
    
    return JavaRelationship(
        source=ctx.class_name,
        target=constructor_type,
        relationship_type=RelationshipType.CALLS.value,
        package=ctx.package,
        file_path=ctx.file_path,
        repository=ctx.repository,
        module=ctx.module,
        source_method=source_method or None,
        target_method="<init>",
        target_class=constructor_type,
        call_site_line=get_call_line_number(creation),
        arguments_count=count_arguments(creation),
        is_static=False,
        is_constructor=True,
    )
