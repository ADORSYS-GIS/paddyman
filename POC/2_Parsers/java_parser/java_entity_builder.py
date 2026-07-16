"""Build NormalizedJson entity dicts from Java AST type declarations.

Converts :class:`~java_parser.java_ast.models.JavaTypeDeclaration` objects
produced by the AST extractor into the flat ``dict`` format stored in
``NormalizedJson.entities``.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any
from uuid import uuid4

from java_parser.annotation_entity_builder import extract_annotation_entities
from java_parser.annotation_normalizer import normalize_annotations
from java_parser.java_ast.extractor import parse_and_extract
from java_parser.java_ast.models import JavaDeclarationType, JavaTypeDeclaration
from java_parser.member_entity_orchestrator import member_entities_for_record
from java_parser.import_entity_builder import import_entities_from_declarations

logger = logging.getLogger(__name__)

_VISIBILITY_MODIFIERS = frozenset({"public", "protected", "private"})


def _visibility(modifiers: list[str]) -> str:
    for mod in modifiers:
        if mod in _VISIBILITY_MODIFIERS:
            return mod
    return "package-private"


def declaration_to_entity(
    decl: JavaTypeDeclaration,
    document_id: str,
    imports: list[str] | None = None,
) -> dict[str, Any]:
    """Convert a single :class:`JavaTypeDeclaration` to an entity dict.

    Args:
        decl:        Parsed type declaration.
        document_id: Document ID of the containing file (used as ``source``).
        imports:     Import list of the file for FQN annotation resolution.

    Returns:
        Entity dict conforming to the ``NormalizedJson.entities`` schema.
    """
    qualified_name = f"{decl.package}.{decl.name}" if decl.package else decl.name
    decl_type = decl.type
    type_label = decl_type.value.capitalize()

    return {
        "type": type_label,
        "name": decl.name,
        "qualified_name": qualified_name,
        "package": decl.package,
        "visibility": _visibility(decl.modifiers),
        "is_abstract": "abstract" in decl.modifiers,
        "source": document_id,
        "repository": decl.repository,
        "module": decl.module,
        "file_path": decl.file_path,
        "start_line": decl.location.start_line + 1,
        "end_line": decl.location.end_line + 1,
        "annotation_count": len(decl.annotations),
        "annotations": normalize_annotations(decl.annotations, imports or []),
        "uuid": str(uuid4()),
        "extends": decl.superclass if decl_type is JavaDeclarationType.CLASS else None,
        "implements": list(decl.interfaces),
    }


def extract_type_annotation_entities(
    decl: JavaTypeDeclaration,
    document_id: str,
    imports: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Extract Annotation entities for a type declaration.

    Args:
        decl:        Parsed type declaration.
        document_id: Document ID of the containing file.
        imports:     Import list for FQN annotation resolution.

    Returns:
        List of Annotation entity dicts.
    """
    type_label = decl.type.value.capitalize()
    return extract_annotation_entities(
        decl.annotations,
        target_type=type_label,
        target_name=decl.name,
        file_path=decl.file_path,
        repository=decl.repository,
        module=decl.module,
        start_line=decl.location.start_line + 1,
        document_id=document_id,
        imports=imports,
    )


def entities_for_record(
    repo_root: Path,
    record: Any,
    document_id: str,
    module_label: str,
) -> list[dict[str, Any]]:
    """Extract entity dicts for all type declarations in *record*.

    Args:
        repo_root:   Absolute path to the repository root directory.
        record:      :class:`~java_parser.discovery.models.JavaFileRecord`.
        document_id: Document ID assigned to this file.
        module_label: Resolved module label (may differ from ``record.module``).

    Returns:
        List of entity dicts; empty when the file cannot be parsed.
    """
    path = repo_root / record.relative_path
    try:
        file_ast = parse_and_extract(
            path,
            repository=record.repository,
            module=module_label,
            repo_root=repo_root,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("Entity extraction failed for %s: %s", path, exc)
        return []

    import_entities = import_entities_from_declarations(
        file_ast.import_declarations, document_id
    )
    type_entities = [declaration_to_entity(decl, document_id, file_ast.imports) for decl in file_ast.declarations]
    
    # Extract annotation entities for type declarations
    type_annotation_entities: list[dict[str, Any]] = []
    for decl in file_ast.declarations:
        type_annotation_entities.extend(
            extract_type_annotation_entities(decl, document_id, file_ast.imports)
        )
    
    member_entities = member_entities_for_record(
        repo_root, record, document_id, module_label, imports=file_ast.imports
    )
    return import_entities + type_entities + type_annotation_entities + member_entities
