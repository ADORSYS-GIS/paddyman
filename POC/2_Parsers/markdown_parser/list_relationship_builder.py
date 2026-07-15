"""List relationship builder for markdown parser.

Creates list-specific relationships: NESTED_IN for parent-child lists
and NEXT_LIST for sequential ordering.
"""
from __future__ import annotations

import logging
from typing import Any

from .relationship_utils import create_relationship

logger = logging.getLogger(__name__)


def create_list_relationships(
    list_entities: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Create list-specific relationships.

    Creates:
    - NESTED_IN: Links nested lists to their parent lists
    - NEXT_LIST: Links top-level lists sequentially

    Args:
        list_entities: List of List entity dicts.

    Returns:
        List of relationship dicts.
    """
    relationships: list[dict[str, Any]] = []

    # Create NESTED_IN relationships for nested lists
    for list_entity in list_entities:
        if list_entity["properties"]["is_nested"]:
            parent = _find_parent_list(list_entity, list_entities)
            if parent:
                relationships.append(
                    create_relationship(
                        list_entity["id"],
                        parent["id"],
                        "NESTED_IN",
                        {
                            "relationship_type": "list_nesting",
                            "nesting_level": list_entity["properties"]["nesting_level"],
                        },
                    )
                )

    # Create NEXT_LIST relationships for sequential top-level lists
    top_level_lists = [
        lst for lst in list_entities if not lst["properties"]["is_nested"]
    ]
    top_level_lists.sort(key=lambda x: x["properties"]["start_line"])

    for i in range(len(top_level_lists) - 1):
        relationships.append(
            create_relationship(
                top_level_lists[i]["id"],
                top_level_lists[i + 1]["id"],
                "NEXT_LIST",
                {"relationship_type": "list_sequence"},
            )
        )

    logger.debug(
        f"Created {len(relationships)} list relationships: "
        f"{sum(1 for r in relationships if r['type'] == 'NESTED_IN')} NESTED_IN, "
        f"{sum(1 for r in relationships if r['type'] == 'NEXT_LIST')} NEXT_LIST"
    )

    return relationships


def _find_parent_list(
    nested_list: dict[str, Any],
    all_lists: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """Find the parent list for a nested list.

    Args:
        nested_list: The nested list entity.
        all_lists: All list entities.

    Returns:
        Parent list entity or None if not found.
    """
    nested_start = nested_list["properties"]["start_line"]
    nested_level = nested_list["properties"]["nesting_level"]

    # Find lists that could be parents (lower nesting level, start before this list)
    candidates = [
        lst
        for lst in all_lists
        if lst["properties"]["nesting_level"] == nested_level - 1
        and lst["properties"]["start_line"] < nested_start
        and lst["properties"]["end_line"] >= nested_start
    ]

    # Return the closest parent (most recent one before this list)
    if candidates:
        candidates.sort(key=lambda x: x["properties"]["start_line"], reverse=True)
        return candidates[0]

    return None
