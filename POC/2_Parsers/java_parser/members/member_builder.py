"""Member builder — orchestration layer for member extraction.

Composes the field, method, and constructor extractors and exposes
the public API consumed by downstream pipeline stages.
"""
from __future__ import annotations

import logging
from pathlib import Path

from tree_sitter import Node

from java_parser.java_ast.node_helpers import node_text
from java_parser.java_ast.parser import parse_file

from .constructor_extractor import extract_constructors
from .field_extractor import extract_fields
from .method_extractor import extract_methods
from .models import ClassMembers
from ._helpers import MemberContext

logger = logging.getLogger(__name__)

# Declaration node types that have a class_body (or interface_body)
_BODY_FIELD: dict[str, str] = {
    "class_declaration": "class_body",
    "interface_declaration": "interface_body",
    "enum_declaration": "enum_body",
}


def _find_body(decl_node: Node) -> Node | None:
    """Return the body node of a type declaration."""
    body_type = _BODY_FIELD.get(decl_node.type, "class_body")
    for child in decl_node.children:
        if child.type == body_type:
            return child
    return None


def _class_name(decl_node: Node) -> str:
    """Extract the simple type name from a declaration node."""
    for child in decl_node.children:
        if child.type == "identifier":
            return node_text(child)
    return ""


def extract_class_members(
    decl_node: Node,
    *,
    package: str,
    file_path: str,
    repository: str,
    module: str,
) -> ClassMembers:
    """Extract all members from a single type declaration node.

    Args:
        decl_node:  A ``class_declaration``, ``interface_declaration``, or
                    ``enum_declaration`` tree-sitter node.
        package:    Package of the enclosing file.
        file_path:  Repository-relative path to the source file.
        repository: Repository name.
        module:     Module label.

    Returns:
        :class:`ClassMembers` with extracted fields, methods, and constructors.
    """
    class_name = _class_name(decl_node)
    
    # Determine declaration type
    declaration_type = "class"
    if decl_node.type == "interface_declaration":
        declaration_type = "interface"
    elif decl_node.type == "enum_declaration":
        declaration_type = "enum"
    
    ctx = MemberContext(
        class_name=class_name,
        package=package,
        file_path=file_path,
        repository=repository,
        module=module,
    )
    body = _find_body(decl_node)
    errors: list[str] = []

    if body is None:
        errors.append(f"No body found for {class_name}")
        return ClassMembers(
            class_name=class_name, package=package, file_path=file_path,
            repository=repository, module=module, declaration_type=declaration_type,
            errors=errors,
        )

    fields = extract_fields(body, ctx)
    methods = extract_methods(body, ctx)
    constructors = extract_constructors(body, ctx)

    logger.debug(
        "%s: %d fields, %d methods, %d constructors",
        class_name, len(fields), len(methods), len(constructors),
    )
    return ClassMembers(
        class_name=class_name, package=package, file_path=file_path,
        repository=repository, module=module, declaration_type=declaration_type,
        fields=fields, methods=methods, constructors=constructors, errors=errors,
    )


def extract_file_members(
    root: Node,
    *,
    package: str,
    file_path: str,
    repository: str,
    module: str,
) -> list[ClassMembers]:
    """Extract members for every type declaration in *root*.

    Args:
        root:       Root ``program`` node of a parsed Java file.
        package:    Package declared in the file.
        file_path:  Repository-relative source path.
        repository: Repository name.
        module:     Module label.

    Returns:
        One :class:`ClassMembers` per top-level type declaration.
    """
    results: list[ClassMembers] = []
    for child in root.children:
        if child.type not in _BODY_FIELD:
            continue
        try:
            cm = extract_class_members(
                child,
                package=package,
                file_path=file_path,
                repository=repository,
                module=module,
            )
            results.append(cm)
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed extracting members from %s: %s", file_path, exc)
    return results


def parse_and_extract_members(
    path: Path,
    *,
    package: str = "",
    repository: str = "",
    module: str = "",
    repo_root: Path | None = None,
) -> list[ClassMembers]:
    """Read *path*, parse it, and extract all class members.

    When *package* is not supplied the file is re-parsed to detect it.

    Args:
        path:       Absolute path to a ``.java`` source file.
        package:    Known package (skips re-detection when provided).
        repository: Repository name for provenance.
        module:     Module label for provenance.
        repo_root:  When supplied, ``file_path`` is relative to this directory.

    Returns:
        List of :class:`ClassMembers`, one per top-level type declaration.
    """
    try:
        root, _ = parse_file(path)
    except OSError as exc:
        logger.error("Cannot read %s: %s", path, exc)
        return []

    if repo_root:
        try:
            file_path = path.relative_to(repo_root).as_posix()
        except ValueError:
            file_path = path.name
    else:
        file_path = path.name

    if not package:
        from java_parser.java_ast.extractor import _extract_package  # noqa: PLC0415
        package = _extract_package(root)

    return extract_file_members(
        root, package=package, file_path=file_path,
        repository=repository, module=module,
    )
