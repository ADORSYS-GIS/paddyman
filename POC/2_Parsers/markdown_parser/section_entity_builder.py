"""Build Section entity dicts from markdown headings.

Converts markdown sections (heading-delimited blocks) into the flat entity
format expected by the normalized JSON output schema.
"""
from __future__ import annotations

import logging
from typing import Any
from uuid import uuid4

logger = logging.getLogger(__name__)


def create_section_entities(
    text: str,
    file_name: str,
) -> list[dict[str, Any]]:
    """Extract Section entities from markdown text.

    Sections are defined by headings (# to ######) and include all content
    until the next heading of equal or higher level.

    Args:
        text:      Markdown text content.
        file_name: Name of the markdown file (for source identification).

    Returns:
        List of Section entity dicts.
    """
    lines = text.splitlines()
    sections: list[dict[str, Any]] = []
    current_section: dict[str, Any] | None = None
    section_content: list[str] = []

    for line_num, line in enumerate(lines, start=1):
        stripped = line.strip()

        # Check if line is a heading
        heading_level = _get_heading_level(stripped)

        if heading_level > 0:
            # Save previous section if exists
            if current_section:
                current_section["properties"]["end_line"] = line_num - 1
                current_section["properties"]["content_preview"] = _create_preview(
                    section_content
                )
                sections.append(current_section)

            # Start new section
            heading_text = stripped.lstrip("#").strip()
            section_id = str(uuid4())
            source = f"markdown_parser:{file_name}:section:{line_num}"

            current_section = {
                "id": section_id,
                "type": "Section",
                "name": heading_text,
                "source": source,
                "properties": {
                    "heading_text": heading_text,
                    "level": heading_level,
                    "start_line": line_num,
                    "end_line": line_num,  # Will be updated later
                    "section_id": section_id,
                    "parent_section_id": None,  # Will be set by hierarchy builder
                },
            }
            section_content = []
        elif current_section:
            section_content.append(line)

    # Save last section
    if current_section:
        current_section["properties"]["end_line"] = len(lines)
        current_section["properties"]["content_preview"] = _create_preview(section_content)
        sections.append(current_section)

    return sections


def _get_heading_level(line: str) -> int:
    """Determine the heading level (1-6) of a line, or 0 if not a heading.

    Args:
        line: Markdown line (stripped).

    Returns:
        Heading level (1-6) or 0 if not a heading.
    """
    if not line.startswith("#"):
        return 0

    level = 0
    for char in line:
        if char == "#":
            level += 1
        else:
            break

    # Valid heading must have space after # markers and be 1-6 levels
    if level > 0 and level <= 6 and len(line) > level and line[level] == " ":
        return level

    return 0


def _create_preview(content_lines: list[str], max_length: int = 200) -> str:
    """Create a preview of section content.

    Args:
        content_lines: Lines of content.
        max_length:    Maximum preview length.

    Returns:
        Preview text (truncated if necessary).
    """
    text = " ".join(line.strip() for line in content_lines if line.strip())
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."
