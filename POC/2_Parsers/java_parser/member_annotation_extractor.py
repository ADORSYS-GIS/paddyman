"""Extract annotation entities from Java method and constructor declarations."""
from __future__ import annotations

from typing import Any

from java_parser.annotation_entity_builder import extract_annotation_entities
from java_parser.members.models import JavaConstructor, JavaMethod


def extract_method_annotation_entities(
    method: JavaMethod,
    document_id: str,
    imports: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Extract Annotation entities for a method.

    Args:
        method:      Extracted method declaration.
        document_id: Document ID of the containing file.
        imports:     Import list for FQN annotation resolution.

    Returns:
        List of Annotation entity dicts.
    """
    return extract_annotation_entities(
        method.annotations,
        target_type="Method",
        target_name=method.name,
        file_path=method.file_path,
        repository=method.repository,
        module=method.module,
        start_line=method.location.start_line + 1,
        document_id=document_id,
        imports=imports,
    )


def extract_constructor_annotation_entities(
    ctor: JavaConstructor,
    document_id: str,
    imports: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Extract Annotation entities for a constructor.

    Args:
        ctor:        Extracted constructor declaration.
        document_id: Document ID of the containing file.
        imports:     Import list for FQN annotation resolution.

    Returns:
        List of Annotation entity dicts.
    """
    return extract_annotation_entities(
        ctor.annotations,
        target_type="Constructor",
        target_name=ctor.name,
        file_path=ctor.file_path,
        repository=ctor.repository,
        module=ctor.module,
        start_line=ctor.location.start_line + 1,
        document_id=document_id,
        imports=imports,
    )
