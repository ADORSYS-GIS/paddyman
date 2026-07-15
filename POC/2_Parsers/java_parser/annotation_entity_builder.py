"""Build Annotation entities from Java annotation declarations.

Extracts annotations as first-class entities rather than inline properties,
enabling annotation-level querying, relationship tracking, and pattern analysis.
"""
from __future__ import annotations

from typing import Any
from uuid import uuid4

from java_parser.annotation_normalizer import normalize_annotation
from java_parser.java_ast.models import JavaAnnotation


AnnotationInput = JavaAnnotation | str


def annotation_to_entity(
    annotation: AnnotationInput,
    target_type: str,
    target_name: str,
    file_path: str,
    repository: str,
    module: str,
    start_line: int,
    document_id: str,
    imports: list[str] | None = None,
) -> dict[str, Any]:
    """Convert an annotation to an Annotation entity dict.

    Args:
        annotation:   JavaAnnotation object or annotation string.
        target_type:  Type of annotated element (Class, Method, Field, Parameter).
        target_name:  Name of the annotated element.
        file_path:    Repository-relative file path.
        repository:   Repository name.
        module:       Module label.
        start_line:   Line number where annotation appears.
        document_id:  Document ID of the containing file.
        imports:      Import list for FQN resolution.

    Returns:
        Entity dict with type="Annotation".
    """
    normalized = normalize_annotation(annotation, imports or [])
    
    # Extract simple name without @ prefix
    simple_name = normalized["name"].lstrip("@")
    
    return {
        "type": "Annotation",
        "name": normalized["name"],
        "source": document_id,
        "uuid": str(uuid4()),
        "qualified_name": normalized["qualified_name"],
        "simple_name": simple_name,
        "attributes": normalized.get("attributes", {}),
        "target_type": target_type,
        "target_name": target_name,
        "file_path": file_path,
        "repository": repository,
        "module": module,
        "start_line": start_line,
        "end_line": start_line,  # Annotations typically span one line
    }


def extract_annotation_entities(
    annotations: list[AnnotationInput],
    target_type: str,
    target_name: str,
    file_path: str,
    repository: str,
    module: str,
    start_line: int,
    document_id: str,
    imports: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Extract Annotation entities from a list of annotations.

    Args:
        annotations:  List of JavaAnnotation objects or annotation strings.
        target_type:  Type of annotated element (Class, Method, Field, Parameter).
        target_name:  Name of the annotated element.
        file_path:    Repository-relative file path.
        repository:   Repository name.
        module:       Module label.
        start_line:   Line number where annotations appear.
        document_id:  Document ID of the containing file.
        imports:      Import list for FQN resolution.

    Returns:
        List of Annotation entity dicts.
    """
    if not annotations:
        return []
    
    return [
        annotation_to_entity(
            ann,
            target_type,
            target_name,
            file_path,
            repository,
            module,
            start_line,
            document_id,
            imports,
        )
        for ann in annotations
    ]
