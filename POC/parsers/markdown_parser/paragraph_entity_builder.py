"""Build Paragraph entity dicts from markdown paragraphs.

Converts markdown text paragraphs into the flat entity format expected by
the normalized JSON output schema.
"""
from __future__ import annotations

import logging
from typing import Any
from uuid import uuid5, NAMESPACE_URL

from .paragraph_detector import is_paragraph_start, is_paragraph_continuation

logger = logging.getLogger(__name__)


def create_paragraph_entities(
    text: str,
    file_name: str,
) -> list[dict[str, Any]]:
    """Extract Paragraph entities from markdown text.

    Paragraphs are blocks of text that are not headings, lists, tables,
    or code blocks.

    Args:
        text:      Markdown text content.
        file_name: Name of the markdown file (for source identification).

    Returns:
        List of Paragraph entity dicts.
    """
    paragraphs: list[dict[str, Any]] = []
    lines = text.splitlines()

    i = 0
    while i < len(lines):
        if is_paragraph_start(lines, i):
            paragraph = _extract_paragraph(lines, i, file_name)
            if paragraph:
                paragraphs.append(paragraph)
                i = paragraph["properties"]["end_line"]
            else:
                i += 1
        else:
            i += 1

    return paragraphs


def _extract_paragraph(
    lines: list[str],
    start_idx: int,
    file_name: str,
) -> dict[str, Any] | None:
    """Extract a complete paragraph starting from the given line index.

    Args:
        lines:     All lines of text.
        start_idx: Starting line index (0-based).
        file_name: Name of the markdown file.

    Returns:
        Paragraph entity dict or None if extraction fails.
    """
    paragraph_lines: list[str] = []
    end_idx = start_idx

    # Collect consecutive non-empty lines that form a paragraph
    while end_idx < len(lines) and is_paragraph_continuation(lines, end_idx):
        paragraph_lines.append(lines[end_idx])
        end_idx += 1

    if not paragraph_lines:
        return None

    text_content = " ".join(line.strip() for line in paragraph_lines)
    word_count = len(text_content.split())

    # Create preview (first 200 chars)
    text_preview = text_content[:200]
    if len(text_content) > 200:
        text_preview += "..."

    start_line = start_idx + 1  # Convert to 1-based
    end_line = end_idx  # Already correct for next iteration
    paragraph_id = str(uuid5(NAMESPACE_URL, f"paragraph:{file_name}:{start_line}:{text_preview}"))
    source = f"markdown_parser:{file_name}:paragraph:{start_line}"

    return {
        "id": paragraph_id,
        "type": "Paragraph",
        "name": f"Paragraph at line {start_line}",
        "source": source,
        "properties": {
            "text_preview": text_preview,
            "word_count": word_count,
            "start_line": start_line,
            "end_line": end_line,
            "paragraph_id": paragraph_id,
        },
    }

