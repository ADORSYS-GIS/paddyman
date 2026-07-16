"""Build Heading entity dicts from markdown heading lines.

Converts markdown headings (# to ######) into the flat entity format expected
by the normalized JSON output schema.
"""
from __future__ import annotations

import logging
import re
from typing import Any
from uuid import uuid4

logger = logging.getLogger(__name__)


def create_heading_entities(
    text: str,
    file_name: str,
) -> list[dict[str, Any]]:
    """Extract Heading entities from markdown text.

    Args:
        text:      Markdown text content.
        file_name: Name of the markdown file (for source identification).

    Returns:
        List of Heading entity dicts.
    """
    headings: list[dict[str, Any]] = []
    lines = text.splitlines()

    for line_num, line in enumerate(lines, start=1):
        stripped = line.strip()
        heading_level = _get_heading_level(stripped)

        if heading_level > 0:
            heading_text = stripped.lstrip("#").strip()
            heading_id = str(uuid4())
            source = f"markdown_parser:{file_name}:heading:{line_num}"
            slug = _generate_slug(heading_text)

            heading = {
                "id": heading_id,
                "type": "Heading",
                "name": heading_text,
                "source": source,
                "properties": {
                    "text": heading_text,
                    "level": heading_level,
                    "start_line": line_num,
                    "markdown_syntax": stripped,
                    "file_path": file_name,
                    "slug": slug,
                    "heading_id": heading_id,
                },
            }
            headings.append(heading)

    return headings


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


def _generate_slug(text: str) -> str:
    """Generate a URL-friendly slug from heading text.

    Args:
        text: Heading text.

    Returns:
        URL-friendly slug (lowercase, hyphenated).
    """
    # Convert to lowercase
    slug = text.lower()
    # Replace spaces, underscores, and dots with hyphens
    slug = re.sub(r"[\s_.]+", "-", slug)
    # Remove non-alphanumeric characters except hyphens
    slug = re.sub(r"[^\w-]", "", slug)
    # Remove leading/trailing hyphens
    slug = slug.strip("-")
    return slug
