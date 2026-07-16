"""Inheritance and interface-implementation relationship extraction.

Works entirely from :class:`~java_parser.java_ast.models.JavaFileAst` —
no raw AST traversal needed.  The ``superclass`` and ``interfaces`` fields
on each :class:`~java_parser.java_ast.models.JavaTypeDeclaration` already
carry the information required.
"""
from __future__ import annotations

import logging

from java_parser.java_ast.models import JavaFileAst, JavaTypeDeclaration
from java_parser.relationships.models import JavaRelationship, RelationshipType

logger = logging.getLogger(__name__)


def _make_rel(
    source: str,
    target: str,
    rel_type: RelationshipType,
    decl: JavaTypeDeclaration,
) -> JavaRelationship:
    return JavaRelationship(
        source=source,
        target=target,
        relationship_type=rel_type.value,
        package=decl.package,
        file_path=decl.file_path,
        repository=decl.repository,
        module=decl.module,
        target_class=target,
    )


def extract_inheritance_relationships(
    file_ast: JavaFileAst,
) -> list[JavaRelationship]:
    """Extract EXTENDS and IMPLEMENTS relationships from *file_ast*.

    Iterates over every :class:`~java_parser.java_ast.models.JavaTypeDeclaration`
    in the file and emits:

    - One ``EXTENDS`` relationship when a ``superclass`` is declared.
    - One ``IMPLEMENTS`` relationship per entry in ``interfaces``.

    Args:
        file_ast: Parsed AST metadata for a single Java file.

    Returns:
        List of :class:`~java_parser.relationships.models.JavaRelationship`
        instances (empty when the file contains no inheritance or
        implementation declarations).
    """
    results: list[JavaRelationship] = []
    for decl in file_ast.declarations:
        try:
            results.extend(_relationships_for_decl(decl))
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Skipping inheritance extraction for %s in %s: %s",
                decl.name,
                file_ast.file_path,
                exc,
            )
    return results


def _relationships_for_decl(
    decl: JavaTypeDeclaration,
) -> list[JavaRelationship]:
    results: list[JavaRelationship] = []

    if decl.superclass:
        results.append(
            _make_rel(decl.name, decl.superclass, RelationshipType.EXTENDS, decl)
        )

    for iface in decl.interfaces:
        if iface:
            results.append(
                _make_rel(decl.name, iface, RelationshipType.IMPLEMENTS, decl)
            )

    return results
