"""Orchestrate member entity extraction from Java class declarations."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from java_parser.field_entity_builder import extract_field_annotation_entities, field_to_entity
from java_parser.member_annotation_extractor import (
    extract_constructor_annotation_entities,
    extract_method_annotation_entities,
)
from java_parser.member_entity_builder import constructor_to_entity, method_to_entity
from java_parser.members.member_builder import parse_and_extract_members
from java_parser.members.models import ClassMembers

logger = logging.getLogger(__name__)


def entities_from_class_members(
    class_members: ClassMembers, document_id: str, imports: list[str]
) -> list[dict[str, Any]]:
    """Convert ClassMembers to entity dicts, including annotation entities.
    
    Args:
        class_members: Extracted member declarations.
        document_id:   Document ID of the containing file.
        imports:       Import list for annotation resolution.
        
    Returns:
        List of entity dicts for fields, methods, constructors, and their annotations.
    """
    entities: list[dict[str, Any]] = []
    is_interface = class_members.declaration_type == "interface"
    
    # Extract field entities and their annotations
    for fld in class_members.fields:
        entities.append(field_to_entity(fld, document_id, imports))
        entities.extend(extract_field_annotation_entities(fld, document_id, imports))
    
    # Extract method entities and their annotations
    for method in class_members.methods:
        entities.append(method_to_entity(method, document_id, imports, is_interface))
        entities.extend(extract_method_annotation_entities(method, document_id, imports))
    
    # Extract constructor entities and their annotations
    for ctor in class_members.constructors:
        entities.append(constructor_to_entity(ctor, document_id, imports))
        entities.extend(extract_constructor_annotation_entities(ctor, document_id, imports))
    
    return entities


def member_entities_for_record(
    repo_root: Path,
    record: Any,
    document_id: str,
    module_label: str,
    imports: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Extract member entity dicts for all classes in a Java file record.

    Args:
        repo_root:    Absolute path to the repository root directory.
        record:       :class:`~java_parser.discovery.models.JavaFileRecord`.
        document_id:  Document ID assigned to this file.
        module_label: Resolved module label.
        imports:      Import list for annotation resolution.

    Returns:
        List of entity dicts; empty when the file cannot be parsed.
    """
    path = repo_root / record.relative_path
    try:
        class_members_list = parse_and_extract_members(
            path,
            repository=record.repository,
            module=module_label,
            repo_root=repo_root,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("Member extraction failed for %s: %s", path, exc)
        return []

    entities: list[dict[str, Any]] = []
    for class_members in class_members_list:
        entities.extend(entities_from_class_members(class_members, document_id, imports or []))
    return entities


