"""Build List entity dicts from markdown lists.

Converts markdown ordered and unordered lists into the flat entity format
expected by the normalized JSON output schema.
"""
from __future__ import annotations

import logging
from typing import Any

from .list_extractor import extract_list
from .list_item_utils import get_indent_level, get_list_type

logger = logging.getLogger(__name__)


def create_list_entities(
    text: str,
    file_name: str,
) -> list[dict[str, Any]]:
    """Extract List entities from markdown text with nesting support.

    Args:
        text:      Markdown text content.
        file_name: Name of the markdown file (for source identification).

    Returns:
        List of List entity dicts with nesting relationships tracked.
    """
    lists: list[dict[str, Any]] = []
    lines = text.splitlines()
    processed_lines: set[int] = set()

    i = 0
    while i < len(lines):
        if i in processed_lines:
            i += 1
            continue

        indent_level = get_indent_level(lines[i])
        list_type = get_list_type(lines[i])

        if list_type and indent_level == 0:
            list_entity, end_idx = extract_list(
                lines, i, file_name, list_type, indent_level, processed_lines
            )
            if list_entity:
                lists.append(list_entity)
                i = end_idx
            else:
                i += 1
        else:
            i += 1

    return lists
