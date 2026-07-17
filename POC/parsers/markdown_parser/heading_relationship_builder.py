"""Build relationships for heading and frontmatter entities.

Creates TITLED_BY, NEXT_HEADING, and HAS_FRONTMATTER relationships.
"""
from __future__ import annotations

import logging
from typing import Any
from uuid import uuid5, NAMESPACE_URL

logger = logging.getLogger(__name__)


def create_heading_relationships(
    document_entity: dict[str, Any],
    section_entities: list[dict[str, Any]],
    heading_entities: list[dict[str, Any]],
    frontmatter_entity: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    """Create all heading and frontmatter relationships."""
    relationships: list[dict[str, Any]] = []

    titled_by_rels = _create_titled_by_relationships(section_entities, heading_entities)
    relationships.extend(titled_by_rels)

    next_heading_rels = _create_next_heading_relationships(heading_entities)
    relationships.extend(next_heading_rels)

    if frontmatter_entity:
        frontmatter_rel = _create_frontmatter_relationship(
            document_entity, frontmatter_entity
        )
        relationships.append(frontmatter_rel)

    logger.debug(
        f"Created {len(relationships)} heading relationships: "
        f"TITLED_BY={len(titled_by_rels)}, NEXT_HEADING={len(next_heading_rels)}"
    )
    return relationships


def _create_titled_by_relationships(
    section_entities: list[dict[str, Any]],
    heading_entities: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Create TITLED_BY relationships linking sections to headings."""
    relationships: list[dict[str, Any]] = []

    for section in section_entities:
        section_start = section["properties"].get("start_line")
        if not section_start:
            continue

        matching_heading = _find_heading_for_section(
            section_start, heading_entities
        )

        if matching_heading:
            rel = {
                "id": str(uuid5(NAMESPACE_URL, f"TITLED_BY:{section['id']}:{matching_heading['id']}")),
                "type": "TITLED_BY",
                "source_entity_id": section["id"],
                "target_entity_id": matching_heading["id"],
                "properties": {},
            }
            relationships.append(rel)

    return relationships


def _find_heading_for_section(
    section_start_line: int,
    heading_entities: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """Find heading matching section start line (within 2 lines tolerance)."""
    for heading in heading_entities:
        heading_line = heading["properties"].get("start_line")
        if heading_line and abs(heading_line - section_start_line) <= 2:
            return heading
    return None


def _create_next_heading_relationships(
    heading_entities: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Create NEXT_HEADING relationships linking sequential headings."""
    relationships: list[dict[str, Any]] = []

    for i in range(len(heading_entities) - 1):
        rel = {
            "id": str(uuid5(NAMESPACE_URL, f"NEXT_HEADING:{heading_entities[i]['id']}:{heading_entities[i+1]['id']}")),
            "type": "NEXT_HEADING",
            "source_entity_id": heading_entities[i]["id"],
            "target_entity_id": heading_entities[i + 1]["id"],
            "properties": {},
        }
        relationships.append(rel)

    return relationships


def _create_frontmatter_relationship(
    document_entity: dict[str, Any],
    frontmatter_entity: dict[str, Any],
) -> dict[str, Any]:
    """Create HAS_FRONTMATTER relationship linking document to frontmatter."""
    return {
        "id": str(uuid5(NAMESPACE_URL, f"HAS_FRONTMATTER:{document_entity['id']}:{frontmatter_entity['id']}")),
        "type": "HAS_FRONTMATTER",
        "source_entity_id": document_entity["id"],
        "target_entity_id": frontmatter_entity["id"],
        "properties": {},
    }
