"""Build section hierarchy relationships and enrich section entities.

Creates PARENT_SECTION, NEXT_SIBLING, and FIRST_CHILD relationships to model
document outline structure. Enriches sections with depth and path properties.
"""
from __future__ import annotations

import logging
from typing import Any

from .relationship_utils import create_relationship

logger = logging.getLogger(__name__)


def build_parent_relationships(
    section_entities: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Create PARENT_SECTION relationships based on heading levels."""
    relationships: list[dict[str, Any]] = []
    parent_stack: list[dict[str, Any]] = []

    for section in section_entities:
        level = section["properties"]["level"]

        while parent_stack and parent_stack[-1]["properties"]["level"] >= level:
            parent_stack.pop()

        if parent_stack:
            parent = parent_stack[-1]
            section["properties"]["parent_section_id"] = parent["id"]

            relationships.append(
                create_relationship(
                    section["id"],
                    parent["id"],
                    "PARENT_SECTION",
                    {
                        "relationship_type": "section_hierarchy",
                        "child_level": level,
                        "parent_level": parent["properties"]["level"],
                    },
                )
            )

        parent_stack.append(section)

    return relationships


def build_sibling_relationships(
    section_entities: list[dict[str, Any]],
    parent_relationships: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Create NEXT_SIBLING relationships between sections at the same level."""
    relationships: list[dict[str, Any]] = []

    parent_lookup = {
        r["source_entity_id"]: r["target_entity_id"] for r in parent_relationships
    }

    sections_by_parent: dict[str | None, list[dict[str, Any]]] = {}
    for section in section_entities:
        parent_id = parent_lookup.get(section["id"])
        if parent_id not in sections_by_parent:
            sections_by_parent[parent_id] = []
        sections_by_parent[parent_id].append(section)

    for siblings in sections_by_parent.values():
        for i in range(len(siblings) - 1):
            relationships.append(
                create_relationship(
                    siblings[i]["id"],
                    siblings[i + 1]["id"],
                    "NEXT_SIBLING",
                    {"relationship_type": "section_sibling"},
                )
            )

    return relationships


def build_first_child_relationships(
    section_entities: list[dict[str, Any]],
    parent_relationships: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Create FIRST_CHILD relationships from parent to first child."""
    relationships: list[dict[str, Any]] = []

    children_by_parent: dict[str, list[dict[str, Any]]] = {}
    for rel in parent_relationships:
        parent_id = rel["target_entity_id"]
        child_id = rel["source_entity_id"]
        if parent_id not in children_by_parent:
            children_by_parent[parent_id] = []
        children_by_parent[parent_id].append(child_id)

    section_by_id = {s["id"]: s for s in section_entities}

    for parent_id, child_ids in children_by_parent.items():
        children = [section_by_id[cid] for cid in child_ids]
        first_child = min(children, key=lambda s: s["properties"]["start_line"])

        relationships.append(
            create_relationship(
                parent_id,
                first_child["id"],
                "FIRST_CHILD",
                {"relationship_type": "section_first_child"},
            )
        )

    return relationships


def enrich_section_depth_and_path(
    section_entities: list[dict[str, Any]],
    parent_relationships: list[dict[str, Any]],
) -> None:
    """Add depth and path properties to section entities in-place."""
    parent_lookup = {
        r["source_entity_id"]: r["target_entity_id"] for r in parent_relationships
    }
    section_by_id = {s["id"]: s for s in section_entities}

    for section in section_entities:
        depth = 0
        path: list[str] = []
        current_id = section["id"]

        while current_id in parent_lookup:
            depth += 1
            parent_id = parent_lookup[current_id]
            parent_section = section_by_id[parent_id]
            path.insert(0, parent_section["name"])
            current_id = parent_id

        section["properties"]["depth"] = depth
        section["properties"]["path"] = " / ".join(path) if path else ""

