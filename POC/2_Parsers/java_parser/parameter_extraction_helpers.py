"""Helper functions for parameter extraction from methods and constructors."""
from __future__ import annotations

from typing import Any
from uuid import uuid4

from java_parser.parameter_annotation_extractor import extract_parameter_annotation_entities
from java_parser.parameter_entity_builder import (
    build_has_parameter_relationships,
    extract_parameter_entities,
)


def extract_from_method(
    method: Any,
    document_id: str,
    imports: list[str] | None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """Extract parameter entities, annotations, and relationships from a method."""
    if not method.parameters:
        return ([], [], [])

    method_qualified_name = (
        f"{method.package}.{method.class_name}.{method.name}"
        if method.package
        else f"{method.class_name}.{method.name}"
    )

    param_entities = extract_parameter_entities(
        method.parameters,
        method.name,
        method_qualified_name,
        method.file_path,
        method.repository,
        method.module,
        method.location.start_line + 1,
        document_id,
        imports,
    )

    for param_entity in param_entities:
        param_entity["uuid"] = str(uuid4())

    param_annotations = extract_parameter_annotation_entities(
        method.parameters,
        method.name,
        method.file_path,
        method.repository,
        method.module,
        method.location.start_line + 1,
        document_id,
        imports,
    )

    method_entity = {"name": method.name, "uuid": None}
    rels = build_has_parameter_relationships(method_entity, param_entities)
    
    return (param_entities, param_annotations, rels)


def extract_from_constructor(
    ctor: Any,
    document_id: str,
    imports: list[str] | None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """Extract parameter entities, annotations, and relationships from a constructor."""
    if not ctor.parameters:
        return ([], [], [])

    ctor_qualified_name = (
        f"{ctor.package}.{ctor.class_name}.<init>"
        if ctor.package
        else f"{ctor.class_name}.<init>"
    )

    param_entities = extract_parameter_entities(
        ctor.parameters,
        ctor.name,
        ctor_qualified_name,
        ctor.file_path,
        ctor.repository,
        ctor.module,
        ctor.location.start_line + 1,
        document_id,
        imports,
    )

    for param_entity in param_entities:
        param_entity["uuid"] = str(uuid4())

    param_annotations = extract_parameter_annotation_entities(
        ctor.parameters,
        ctor.name,
        ctor.file_path,
        ctor.repository,
        ctor.module,
        ctor.location.start_line + 1,
        document_id,
        imports,
    )

    ctor_entity = {"name": ctor.name, "uuid": None}
    rels = build_has_parameter_relationships(ctor_entity, param_entities)
    
    return (param_entities, param_annotations, rels)
