"""Build TableCell entity dicts and relationships from markdown Table entities.

Converts each cell of a parsed Table into a flat TableCell entity, following
the same entity format used throughout the markdown parser.
"""
from __future__ import annotations

import re
from typing import Any
from uuid import uuid5, NAMESPACE_URL

from .relationship_utils import create_relationship

_LINK_RE = re.compile(r"\[([^\]]+)\]\([^)]+\)")


def create_table_cell_entities(
    table_entities: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Return one TableCell entity per cell for every table.

    Args:
        table_entities: List of Table entity dicts (must include `rows` in properties).

    Returns:
        List of TableCell entity dicts.
    """
    cells: list[dict[str, Any]] = []
    for table in table_entities:
        cells.extend(_cells_for_table(table))
    return cells


def create_table_cell_relationships(
    table_entities: list[dict[str, Any]],
    cell_entities: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Return HAS_CELL, IN_ROW, and IN_COLUMN relationships.

    Args:
        table_entities: List of Table entity dicts.
        cell_entities:  List of TableCell entity dicts.

    Returns:
        List of relationship dicts.
    """
    rels: list[dict[str, Any]] = []
    for table in table_entities:
        tid = table["id"]
        tcells = [c for c in cell_entities if c["properties"]["table_id"] == tid]
        rels.extend(_has_cell_rels(tid, tcells))
        rels.extend(_grouping_rels(tcells))
    return rels


def _cells_for_table(table: dict[str, Any]) -> list[dict[str, Any]]:
    props = table["properties"]
    tid = table["id"]
    headers = props.get("headers", [])
    rows = props.get("rows", [])
    src = (
        f"markdown_parser:{props.get('file_path', '')}"
        f":table:{props.get('start_line', 0)}"
    )
    cells: list[dict[str, Any]] = []
    for col, content in enumerate(headers):
        cells.append(_make_cell(tid, 0, col, content, True, content, src))
    for row_idx, row in enumerate(rows, start=1):
        for col, content in enumerate(row):
            col_header = headers[col] if col < len(headers) else ""
            cells.append(_make_cell(tid, row_idx, col, content, False, col_header, src))
    return cells


def _make_cell(
    table_id: str,
    row: int,
    col: int,
    content: str,
    is_header: bool,
    column_header: str,
    source_prefix: str,
) -> dict[str, Any]:
    links = _LINK_RE.findall(content)
    content_type = _content_type(content, links)
    # Deterministic id based on table id, row, column and content snippet
    cell_id = str(uuid5(NAMESPACE_URL, f"tablecell:{table_id}:{row}:{col}:{str(content)[:200]}"))
    label = (
        f"Cell [{row},{col}]: {content[:40]}"
        if content
        else f"Cell [{row},{col}]: (empty)"
    )
    entity: dict[str, Any] = {
        "id": cell_id,
        "type": "TableCell",
        "name": label,
        "source": f"{source_prefix}:cell:{row}:{col}",
        "properties": {
            "table_id": table_id,
            "row": row,
            "column": col,
            "is_header": is_header,
            "column_header": column_header,
            "content": content,
            "content_type": content_type,
        },
    }
    if links:
        entity["properties"]["links"] = links
    return entity


def _content_type(content: str, links: list[str]) -> str:
    if not content:
        return "empty"
    if links:
        return "text_with_link"
    if content.startswith("`") and content.endswith("`"):
        return "code"
    return "text"


def _has_cell_rels(table_id: str, cells: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        create_relationship(
            table_id, c["id"], "HAS_CELL", {"relationship_type": "table_to_cell"}
        )
        for c in cells
    ]


def _grouping_rels(cells: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rels: list[dict[str, Any]] = []
    by_row: dict[int, list] = {}
    by_col: dict[int, list] = {}
    for cell in cells:
        by_row.setdefault(cell["properties"]["row"], []).append(cell)
        by_col.setdefault(cell["properties"]["column"], []).append(cell)
    for row_cells in by_row.values():
        for i in range(len(row_cells) - 1):
            rels.append(create_relationship(
                row_cells[i]["id"], row_cells[i + 1]["id"],
                "IN_ROW", {"relationship_type": "row_sequence"},
            ))
    for col_cells in by_col.values():
        for i in range(len(col_cells) - 1):
            rels.append(create_relationship(
                col_cells[i]["id"], col_cells[i + 1]["id"],
                "IN_COLUMN", {"relationship_type": "column_sequence"},
            ))
    return rels
