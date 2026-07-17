"""Low-level list extraction logic for markdown parser.

Handles the core algorithm for extracting list structures with proper
nesting detection and item counting.
"""
from __future__ import annotations

from typing import Any
from uuid import uuid5, NAMESPACE_URL

from .list_item_utils import (
    extract_list_item_text,
    get_indent_level,
    get_list_type,
    get_ordered_start,
)


def extract_list(
    lines: list[str],
    start_idx: int,
    file_name: str,
    list_type: str,
    parent_indent: int,
    processed_lines: set[int],
) -> tuple[dict[str, Any] | None, int]:
    """Extract a complete list with nested items."""
    end_idx = start_idx
    item_count = 0
    total_item_count = 0
    items_preview: list[str] = []
    current_indent = get_indent_level(lines[start_idx])
    nesting_level = current_indent // 2
    ordered_start = get_ordered_start(lines[start_idx]) if list_type == "ordered" else None

    # Collect all list items at this level
    while end_idx < len(lines):
        if end_idx in processed_lines:
            end_idx += 1
            continue

        line = lines[end_idx]
        line_indent = get_indent_level(line)
        line_type = get_list_type(line)

        # Item at current level
        if line_type and line_indent == current_indent:
            item_count += 1
            total_item_count += 1
            processed_lines.add(end_idx)
            if len(items_preview) < 3:
                items_preview.append(extract_list_item_text(line))
            end_idx += 1
        # Nested list - count nested items
        elif line_type and line_indent > current_indent:
            nested_count = count_nested_items(lines, end_idx, processed_lines)
            total_item_count += nested_count
            end_idx += 1
        # Empty line - might continue
        elif line.strip() == "":
            if end_idx + 1 < len(lines) and get_list_type(lines[end_idx + 1]):
                end_idx += 1
            else:
                break
        # Non-list content - end of list
        else:
            break

    if item_count == 0:
        return None, end_idx + 1

    start_line = start_idx + 1  # 1-based line numbers
    end_line = end_idx  # Next line to process
    list_id = str(uuid5(NAMESPACE_URL, f"list:{file_name}:{start_line}:{' '.join(items_preview)[:200]}"))

    list_entity = {
        "id": list_id,
        "type": "List",
        "name": f"{list_type.capitalize()} list at line {start_line}",
        "source": f"markdown_parser:{file_name}:list:{start_line}",
        "properties": {
            "list_type": list_type,
            "item_count": item_count,
            "total_item_count": total_item_count,
            "start_line": start_line,
            "end_line": end_line,
            "file_path": file_name,
            "is_nested": nesting_level > 0,
            "nesting_level": nesting_level,
            "items_preview": items_preview,
            "ordered_start": ordered_start,
            "list_id": list_id,
        },
    }

    return list_entity, end_idx


def count_nested_items(
    lines: list[str],
    start_idx: int,
    processed_lines: set[int],
) -> int:
    """Count items in a nested list without extracting it."""
    count = 0
    base_indent = get_indent_level(lines[start_idx])
    idx = start_idx

    while idx < len(lines):
        if idx in processed_lines:
            idx += 1
            continue

        line = lines[idx]
        line_indent = get_indent_level(line)
        line_type = get_list_type(line)

        if line_type and line_indent >= base_indent:
            count += 1
            processed_lines.add(idx)
            idx += 1
        elif line.strip() == "":
            idx += 1
        else:
            break

    return count
