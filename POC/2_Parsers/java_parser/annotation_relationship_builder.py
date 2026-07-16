"""Build HAS_ANNOTATION relationships from annotated elements to Annotation entities.

Creates relationships linking Class, Method, Field, Parameter, and Constructor
entities to their Annotation entities.
"""
from __future__ import annotations

from typing import Any
from uuid import uuid4


def build_has_annotation_relationships(
    source_entity: dict[str, Any],
    annotation_entities: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Create HAS_ANNOTATION relationships from an entity to its annotations.

    Args:
        source_entity:       Entity dict (Class, Method, Field, Parameter, Constructor).
        annotation_entities: List of Annotation entity dicts for this element.

    Returns:
        List of relationship dicts with type="HAS_ANNOTATION".
    """
    if not annotation_entities:
        return []
    
    source_uuid = source_entity.get("uuid") or str(uuid4())
    relationships: list[dict[str, Any]] = []
    
    for ann_entity in annotation_entities:
        ann_uuid = ann_entity.get("uuid") or str(uuid4())
        relationships.append({
            "type": "HAS_ANNOTATION",
            "source": source_uuid,
            "target": ann_uuid,
            "properties": {
                "target_type": ann_entity.get("target_type", ""),
            },
        })
    
    return relationships


def build_annotation_type_relationships(
    annotation_entities: list[dict[str, Any]],
    type_entities: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Create ANNOTATION_TYPE relationships from annotations to their declarations.

    Links Annotation entities to their corresponding Class/Interface declarations
    when the annotation class exists in the codebase.

    Args:
        annotation_entities: List of Annotation entity dicts.
        type_entities:       List of Class/Interface entity dicts in the codebase.

    Returns:
        List of relationship dicts with type="ANNOTATION_TYPE".
    """
    if not annotation_entities or not type_entities:
        return []
    
    # Build index of qualified names to type entities
    type_index: dict[str, str] = {}
    for type_entity in type_entities:
        qualified_name = type_entity.get("qualified_name", "")
        if qualified_name:
            type_index[qualified_name] = type_entity.get("uuid") or str(uuid4())
    
    relationships: list[dict[str, Any]] = []
    
    for ann_entity in annotation_entities:
        ann_qualified_name = ann_entity.get("qualified_name", "")
        if ann_qualified_name in type_index:
            ann_uuid = ann_entity.get("uuid") or str(uuid4())
            type_uuid = type_index[ann_qualified_name]
            relationships.append({
                "type": "ANNOTATION_TYPE",
                "source": ann_uuid,
                "target": type_uuid,
                "properties": {},
            })
    
    return relationships
