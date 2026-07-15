"""Table parsing utilities for markdown tables.

Extracts and parses markdown table structure.
"""
from __future__ import annotations

import re
from typing import Any


def is_table_row(line: str) -> bool:
    """Check if a line appears to be a markdown table row."""
    stripped = line.strip()
    return stripped.startswith("|") or "|" in stripped


def parse_table(
    lines: list[str],
    start_idx: int,
    file_name: str,
) -> dict[str, Any] | None:
    """Extract a complete table starting from the given line index.

    Args:
        lines:     All lines of text.
        start_idx: Starting line index (0-based).
        file_name: Name of the markdown file.

    Returns:
        Table data dict or None if not a valid table.
    """
    # Find the extent of the table
    end_idx = start_idx
    while end_idx < len(lines) and is_table_row(lines[end_idx]):
        end_idx += 1

    table_lines = lines[start_idx:end_idx]
    if len(table_lines) < 2:  # Need at least header + separator
        return None

    # Parse headers from first line
    headers = _parse_table_row(table_lines[0])
    if not headers:
        return None

    # Verify separator line (second line)
    if not _is_separator_line(table_lines[1]):
        return None

    # Extract column alignments from separator line
    alignment = _extract_alignment(table_lines[1])

    # Parse data rows (excluding header and separator)
    data_rows = []
    for i in range(2, len(table_lines)):
        row_data = _parse_table_row(table_lines[i])
        data_rows.append(row_data)

    row_count = len(data_rows)
    column_count = len(headers)

    # Get preview of first 3 rows
    rows_preview = data_rows[:3]

    start_line = start_idx + 1  # Convert to 1-based
    end_line = end_idx  # Already correct for next iteration

    # Look for caption: skip blank lines to find non-table text before the table
    caption = None
    check_idx = start_idx - 1
    while check_idx >= 0:
        prev_line = lines[check_idx].strip()
        if prev_line:
            # Found non-empty line - check if it's not a table row
            if not is_table_row(prev_line):
                caption = prev_line
            break
        check_idx -= 1

    return {
        "headers": headers,
        "row_count": row_count,
        "column_count": column_count,
        "start_line": start_line,
        "end_line": end_line,
        "caption": caption,
        "alignment": alignment,
        "rows_preview": rows_preview,
    }


def _parse_table_row(line: str) -> list[str]:
    """Parse a table row into column values."""
    stripped = line.strip().strip("|")
    return [cell.strip() for cell in stripped.split("|")]


def _is_separator_line(line: str) -> bool:
    """Check if a line is a table separator (e.g., |---|---|)."""
    pattern = re.compile(r"^\s*\|?\s*:?-+:?\s*(\|\s*:?-+:?\s*)*\|?\s*$")
    return bool(pattern.match(line))


def _extract_alignment(separator_line: str) -> list[str]:
    """Extract column alignment from separator line.

    Returns list of "left", "center", or "right" for each column.
    """
    stripped = separator_line.strip().strip("|")
    columns = [col.strip() for col in stripped.split("|")]

    alignments = []
    for col in columns:
        if col.startswith(":") and col.endswith(":"):
            alignments.append("center")
        elif col.endswith(":"):
            alignments.append("right")
        else:
            alignments.append("left")
    return alignments
