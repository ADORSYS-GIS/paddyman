"""Java structural relationship extractor — orchestration layer.

Combines inheritance/implementation relationships (derived from
:class:`~java_parser.java_ast.models.JavaFileAst` declarations) and
method-call relationships (derived from raw AST traversal) into a unified
list of :class:`~java_parser.relationships.models.JavaRelationship` objects.

Typical usage::

    root = parse_bytes(source)
    file_ast = extract_file_ast(root, file_path=..., repository=..., module=...)
    relationships = extract_relationships(root, file_ast)
"""
from __future__ import annotations

import logging

from tree_sitter import Node

from java_parser.java_ast.extractor import extract_file_ast
from java_parser.java_ast.models import JavaFileAst
from java_parser.java_ast.parser import parse_bytes
from java_parser.relationships.call_extractor import extract_call_relationships
from java_parser.relationships.inheritance_extractor import (
    extract_inheritance_relationships,
)
from java_parser.relationships.models import JavaRelationship

logger = logging.getLogger(__name__)


def extract_relationships(
    root: Node,
    file_ast: JavaFileAst,
) -> list[JavaRelationship]:
    """Extract all structural relationships from a parsed Java file.

    Combines:

    - ``EXTENDS`` / ``IMPLEMENTS`` from :func:`extract_inheritance_relationships`
      (uses :class:`JavaFileAst` declarations — no extra AST traversal).
    - ``CALLS`` from :func:`extract_call_relationships`
      (traverses method bodies in the raw AST root).

    Args:
        root:     Root node of the parsed Java source file.
        file_ast: Corresponding :class:`JavaFileAst` providing package,
                  file path, repository, and module context.

    Returns:
        Combined list of :class:`JavaRelationship` instances.
    """
    results: list[JavaRelationship] = []

    try:
        results.extend(extract_inheritance_relationships(file_ast))
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "Inheritance extraction failed for %s: %s", file_ast.file_path, exc
        )

    try:
        results.extend(
            extract_call_relationships(
                root,
                file_path=file_ast.file_path,
                repository=file_ast.repository,
                module=file_ast.module,
                package=file_ast.package,
            )
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "Call extraction failed for %s: %s", file_ast.file_path, exc
        )

    return results


def extract_relationships_from_source(
    source: bytes,
    *,
    file_path: str = "",
    repository: str = "",
    module: str = "",
) -> list[JavaRelationship]:
    """Parse *source* bytes and extract all structural relationships.

    Convenience wrapper combining :func:`parse_bytes`,
    :func:`~java_parser.java_ast.extractor.extract_file_ast`, and
    :func:`extract_relationships`.

    Args:
        source:     Raw Java source bytes.
        file_path:  Repository-relative path (provenance only).
        repository: Repository name (provenance only).
        module:     Module label (provenance only).
    """
    root = parse_bytes(source)
    file_ast = extract_file_ast(
        root, file_path=file_path, repository=repository, module=module
    )
    return extract_relationships(root, file_ast)
