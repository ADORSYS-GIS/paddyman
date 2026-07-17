"""Build relationships between markdown entities.

Creates relationships like CONTAINS, HAS_HEADING, HAS_TABLE, PARENT_SECTION,
etc., to link entities in the document hierarchy.

Note: Section hierarchy relationships are now handled by section_hierarchy.py.
This module maintains the create_section_hierarchy_relationships function for
backward compatibility but delegates to the new module.
"""
from __future__ import annotations

import logging
from typing import Any

from .relationship_utils import create_relationship
from .section_hierarchy import build_parent_relationships

logger = logging.getLogger(__name__)


def create_document_relationships(
    document_entity: dict[str, Any],
    section_entities: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Create CONTAINS relationships from Document to top-level Sections.

    Args:
        document_entity:  Document entity dict.
        section_entities: List of Section entity dicts.

    Returns:
        List of CONTAINS relationship dicts.
    """
    relationships: list[dict[str, Any]] = []
    doc_id = document_entity["id"]

    # Link document to top-level sections (level 1 sections)
    for section in section_entities:
        if section["properties"]["level"] == 1:
            relationships.append(create_relationship(
                doc_id,
                section["id"],
                "CONTAINS",
                {"relationship_type": "document_to_section"}
            ))

    return relationships


def create_section_hierarchy_relationships(
    section_entities: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Create PARENT_SECTION relationships between sections based on heading levels.

    Backward compatibility wrapper. Delegates to section_hierarchy module.

    Args:
        section_entities: List of Section entity dicts (must be in document order).

    Returns:
        List of PARENT_SECTION relationship dicts.
    """
    return build_parent_relationships(section_entities)


