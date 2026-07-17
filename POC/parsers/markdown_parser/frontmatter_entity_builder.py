"""Build Frontmatter entity from YAML frontmatter blocks.

Extracts YAML frontmatter from markdown documents and converts it into
the flat entity format expected by the normalized JSON output schema.
"""
from __future__ import annotations

import logging
from typing import Any
from uuid import uuid5, NAMESPACE_URL

from .frontmatter_parser import parse_frontmatter, _extract_frontmatter_block

logger = logging.getLogger(__name__)


def create_frontmatter_entity(
    text: str,
    file_name: str,
) -> dict[str, Any] | None:
    """Extract Frontmatter entity from markdown text.

    Args:
        text:      Full markdown text content.
        file_name: Name of the markdown file (for source identification).

    Returns:
        Frontmatter entity dict, or None if no frontmatter found.
    """
    raw_yaml = _extract_frontmatter_block(text)
    if not raw_yaml:
        return None

    parsed_fields = parse_frontmatter(text)
    if not parsed_fields:
        logger.warning(f"Frontmatter block found but failed to parse in {file_name}")
        return None

    frontmatter_id = str(uuid5(NAMESPACE_URL, f"frontmatter:{file_name}:{raw_yaml[:200]}"))
    source = f"markdown_parser:{file_name}:frontmatter"

    # Calculate line range (frontmatter starts at line 1)
    start_line = 1
    end_line = text[:text.find("---", 4)].count("\n") + 2 if "---" in text[4:] else 1

    entity = {
        "id": frontmatter_id,
        "type": "Frontmatter",
        "name": "Document Frontmatter",
        "source": source,
        "properties": {
            "raw_yaml": raw_yaml,
            "parsed_fields": parsed_fields,
            "file_path": file_name,
            "start_line": start_line,
            "end_line": end_line,
            "frontmatter_id": frontmatter_id,
        },
    }

    logger.debug(
        f"Extracted frontmatter with {len(parsed_fields)} fields from {file_name}"
    )
    return entity
