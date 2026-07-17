"""Build Parameter entities and relationships from Java method/constructor parameters.

Extracts method and constructor parameters as first-class entities with
HAS_PARAMETER and OF_TYPE relationships.
"""
from __future__ import annotations

import logging
from typing import Any
from uuid import uuid4

from java_parser.members.models import JavaParameter
from java_parser.annotation_normalizer import normalize_annotations

logger = logging.getLogger(__name__)


def parameter_to_entity(
    param: JavaParameter,
    method_name: str,
    method_qualified_name: str,
    file_path: str,
    repository: str,
    module: str,
    start_line: int,
    document_id: str,
    imports: list[str] | None = None,
) -> dict[str, Any]:
    """Convert a JavaParameter to a Parameter entity dict.

    Args:
        param:                 Extracted parameter declaration.
        method_name:           Name of the owning method/constructor.
        method_qualified_name: Fully qualified name of the owning method/constructor.
        file_path:             Repository-relative file path.
        repository:            Repository name.
        module:                Module label.
        start_line:            Line number where parameter is defined.
        document_id:           Document ID of the containing file.
        imports:               Import list for annotation resolution.

    Returns:
        Entity dict with type="Parameter".
    """
    return {
        "type": "Parameter",
        "name": param.name,
        "parameter_type": param.type,
        "position": param.position,
        "is_vararg": param.is_vararg,
        "annotation_count": len(param.annotations),
        "annotations": normalize_annotations(param.annotations, imports or []),
        "uuid": str(uuid4()),
        "method_name": method_name,
        "method_qualified_name": method_qualified_name,
        "file_path": file_path,
        "repository": repository,
        "module": module,
        "start_line": start_line,
        "source": document_id,
    }


def extract_parameter_entities(
    parameters: list[JavaParameter],
    method_name: str,
    method_qualified_name: str,
    file_path: str,
    repository: str,
    module: str,
    start_line: int,
    document_id: str,
    imports: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Extract Parameter entities from a method or constructor's parameter list.

    Args:
        parameters:            List of JavaParameter objects.
        method_name:           Name of the owning method/constructor.
        method_qualified_name: Fully qualified name of the method/constructor.
        file_path:             Repository-relative file path.
        repository:            Repository name.
        module:                Module label.
        start_line:            Line number where parameters are defined.
        document_id:           Document ID of the containing file.
        imports:               Import list for annotation resolution.

    Returns:
        List of Parameter entity dicts.
    """
    return [
        parameter_to_entity(
            param,
            method_name,
            method_qualified_name,
            file_path,
            repository,
            module,
            start_line,
            document_id,
            imports,
        )
        for param in parameters
    ]


def build_has_parameter_relationships(
    method_entity: dict[str, Any],
    parameter_entities: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Create HAS_PARAMETER relationships from method/constructor to parameters.

    Args:
        method_entity:      Method or Constructor entity dict.
        parameter_entities: List of Parameter entity dicts.

    Returns:
        List of relationship dicts with type="HAS_PARAMETER".
    """
    method_uuid = str(method_entity.get("uuid") or uuid4())
    relationships: list[dict[str, Any]] = []

    for param_entity in parameter_entities:
        param_uuid = str(param_entity.get("uuid") or uuid4())
        relationships.append({
            "type": "HAS_PARAMETER",
            "source": method_uuid,
            "target": param_uuid,
            "properties": {"position": param_entity.get("position", 0)},
        })

    return relationships

