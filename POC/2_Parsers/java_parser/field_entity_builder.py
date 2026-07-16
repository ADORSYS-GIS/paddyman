"""Build Field entities from Java field declarations."""
from __future__ import annotations

from typing import Any
from uuid import uuid4

from java_parser.annotation_entity_builder import extract_annotation_entities
from java_parser.annotation_normalizer import normalize_annotations
from java_parser.members.models import JavaField


_VISIBILITY_MODIFIERS = frozenset({"public", "protected", "private"})


def _visibility(modifiers: list[str]) -> str:
    """Determine visibility from modifier list."""
    for mod in modifiers:
        if mod in _VISIBILITY_MODIFIERS:
            return mod
    return "package-private"


def field_to_entity(
    field: JavaField, document_id: str, imports: list[str] | None = None
) -> dict[str, Any]:
    """Convert a :class:`JavaField` to an entity dict.

    Args:
        field:       Extracted field declaration.
        document_id: Document ID of the containing file.
        imports:     Import list for annotation resolution.

    Returns:
        Entity dict conforming to the ``NormalizedJson.entities`` schema.
    """
    qualified_class = (
        f"{field.package}.{field.class_name}" if field.package else field.class_name
    )
    return {
        "type": "Field",
        "name": field.name,
        "field_type": field.type,
        "class": field.class_name,
        "qualified_class": qualified_class,
        "visibility": _visibility(field.modifiers),
        "annotation_count": len(field.annotations),
        "annotations": normalize_annotations(field.annotations, imports or []),
        "uuid": str(uuid4()),
        "is_static": "static" in field.modifiers,
        "is_final": "final" in field.modifiers,
        "start_line": field.location.start_line + 1,
        "end_line": field.location.end_line + 1,
        "source": document_id,
        "repository": field.repository,
        "module": field.module,
        "file_path": field.file_path,
    }


def extract_field_annotation_entities(
    field: JavaField,
    document_id: str,
    imports: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Extract Annotation entities for a field.

    Args:
        field:       Extracted field declaration.
        document_id: Document ID of the containing file.
        imports:     Import list for FQN annotation resolution.

    Returns:
        List of Annotation entity dicts.
    """
    return extract_annotation_entities(
        field.annotations,
        target_type="Field",
        target_name=field.name,
        file_path=field.file_path,
        repository=field.repository,
        module=field.module,
        start_line=field.location.start_line + 1,
        document_id=document_id,
        imports=imports,
    )
