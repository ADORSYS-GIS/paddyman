"""Build entity dicts from JavaImportDeclaration objects.

Converts import declarations into the flat entity format expected by
the normalized JSON output schema.
"""
from __future__ import annotations

import logging
from typing import Any

from java_parser.java_ast.models import JavaImportDeclaration

logger = logging.getLogger(__name__)


def import_declaration_to_entity(
    decl: JavaImportDeclaration,
    document_id: str,
) -> dict[str, Any]:
    """Convert a JavaImportDeclaration to an entity dict.

    Args:
        decl:        Parsed import declaration.
        document_id: Document ID of the containing file (used as ``source``).

    Returns:
        Entity dict conforming to the ``NormalizedJson.entities`` schema.
    """
    return {
        "type": "Import",
        "name": decl.name,
        "source": document_id,
        "repository": decl.repository,
        "module": decl.module,
        "file_path": decl.file_path,
        "package": decl.package,
        "is_static": decl.is_static,
        "is_wildcard": decl.is_wildcard,
        "start_line": decl.location.start_line + 1,
        "end_line": decl.location.end_line + 1,
        "imported_name": decl.imported_name,
    }


def import_entities_from_declarations(
    declarations: list[JavaImportDeclaration],
    document_id: str,
) -> list[dict[str, Any]]:
    """Convert a list of import declarations to entity dicts.

    Args:
        declarations: List of parsed import declarations.
        document_id:  Document ID of the containing file.

    Returns:
        List of entity dicts for import entities.
    """
    return [
        import_declaration_to_entity(decl, document_id)
        for decl in declarations
    ]
