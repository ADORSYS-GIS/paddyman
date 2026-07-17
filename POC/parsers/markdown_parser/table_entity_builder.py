"""Build Table entity dicts from markdown tables.

Converts markdown tables into the flat entity format expected by the
normalized JSON output schema.
"""
from __future__ import annotations

import logging
from typing import Any
from uuid import uuid5, NAMESPACE_URL

from .table_parser import parse_table, is_table_row
from .relationship_utils import create_relationship

logger = logging.getLogger(__name__)


def create_table_entities(
    text: str,
    file_name: str,
) -> list[dict[str, Any]]:
    """Extract Table entities from markdown text.

    Args:
        text:      Markdown text content.
        file_name: Name of the markdown file (for source identification).

    Returns:
        List of Table entity dicts.
    """
    tables: list[dict[str, Any]] = []
    lines = text.splitlines()

    i = 0
    while i < len(lines):
        # Check if current line looks like a table row
        if is_table_row(lines[i]):
            table = parse_table(lines, i, file_name)
            if table:
                tables.append(_create_table_entity(table, file_name))
                i = table["end_line"]
            else:
                i += 1
        else:
            i += 1

    return tables


def _create_table_entity(
    table_data: dict[str, Any],
    file_name: str,
) -> dict[str, Any]:
    """Create a Table entity dict from parsed table data.

    Args:
        table_data: Parsed table data.
        file_name:  Name of the markdown file.

    Returns:
        Table entity dict.
    """
    start_line = table_data["start_line"]
    table_id = str(uuid5(NAMESPACE_URL, f"table:{file_name}:{start_line}:{str(table_data)[:200]}"))
    source = f"markdown_parser:{file_name}:table:{start_line}"

    return {
        "id": table_id,
        "type": "Table",
        "name": table_data.get("caption") or f"Table at line {start_line}",
        "source": source,
        "properties": {
            "headers": table_data["headers"],
            "row_count": table_data["row_count"],
            "column_count": table_data["column_count"],
            "start_line": start_line,
            "end_line": table_data["end_line"],
            "caption": table_data.get("caption"),
            "file_path": file_name,
            "rows_preview": table_data.get("rows_preview", []),
            "alignment": table_data.get("alignment", []),
            "table_id": table_id,
            "rows": table_data.get("rows", []),
        },
    }


def create_table_sequential_relationships(
    table_entities: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Create NEXT_TABLE relationships between consecutive tables.

    Args:
        table_entities: List of Table entity dicts in document order.

    Returns:
        List of NEXT_TABLE relationship dicts.
    """
    relationships: list[dict[str, Any]] = []

    for i in range(len(table_entities) - 1):
        current_table = table_entities[i]
        next_table = table_entities[i + 1]

        relationships.append(create_relationship(
            current_table["id"],
            next_table["id"],
            "NEXT_TABLE",
            {
                "relationship_type": "table_sequence",
                "current_line": current_table["properties"]["start_line"],
                "next_line": next_table["properties"]["start_line"],
            }
        ))

    return relationships

