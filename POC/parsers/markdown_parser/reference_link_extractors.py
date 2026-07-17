"""Link reference extraction for markdown.

Extracts inline links and reference definitions from markdown.
"""
from __future__ import annotations

import re
from typing import Any
from uuid import uuid5, NAMESPACE_URL

from .reference_classifiers import (
    is_external_url,
    is_relative_path,
    is_anchor,
    is_cross_document,
)
from .reference_url_utils import extract_target_document

# Regex patterns
INLINE_LINK_PATTERN = re.compile(r'\[([^\]]+)\]\(([^)"\s]+)(?:\s+"([^"]+)")?\)')
REF_DEF_PATTERN = re.compile(r'^\[([^\]]+)\]:\s*(\S+)(?:\s+"([^"]+)")?', re.MULTILINE)


def extract_inline_links(text: str, file_name: str) -> list[dict[str, Any]]:
    """Extract inline link references with title and classification.

    Args:
        text:      Markdown text content.
        file_name: Name of the markdown file.

    Returns:
        List of link Reference entity dicts.
    """
    links: list[dict[str, Any]] = []
    lines = text.splitlines()

    for line_num, line in enumerate(lines, start=1):
        for match in INLINE_LINK_PATTERN.finditer(line):
            anchor_text = match.group(1)
            target_url = match.group(2)
            title = match.group(3) or None

            ref_id = str(uuid5(NAMESPACE_URL, f"link:{file_name}:{line_num}:{anchor_text}:{target_url}"))
            source = f"markdown_parser:{file_name}:link:{line_num}"

            properties = {
                "ref_type": "link",
                "target_url": target_url,
                "anchor_text": anchor_text,
                "start_line": line_num,
                "reference_id": ref_id,
                "file_path": file_name,
                "is_external": is_external_url(target_url),
                "is_relative": is_relative_path(target_url),
                "is_anchor": is_anchor(target_url),
            }

            if title:
                properties["title"] = title

            if is_cross_document(target_url):
                properties["target_document"] = extract_target_document(target_url)

            links.append({
                "id": ref_id,
                "type": "Reference",
                "name": anchor_text,
                "source": source,
                "properties": properties,
            })

    return links


def extract_reference_definitions(
    text: str,
    file_name: str,
) -> list[dict[str, Any]]:
    """Extract reference definitions ([id]: url "title").

    Args:
        text:      Markdown text content.
        file_name: Name of the markdown file.

    Returns:
        List of reference definition Reference entity dicts.
    """
    definitions: list[dict[str, Any]] = []
    lines = text.splitlines()

    for line_num, line in enumerate(lines, start=1):
        match = REF_DEF_PATTERN.match(line)
        if match:
            ref_label = match.group(1)
            ref_url = match.group(2)
            title = match.group(3) or None

            ref_id = str(uuid5(NAMESPACE_URL, f"refdef:{file_name}:{line_num}:{ref_label}:{ref_url}"))
            source = f"markdown_parser:{file_name}:refdef:{line_num}"

            properties = {
                "ref_type": "reference_definition",
                "target_url": ref_url,
                "anchor_text": ref_label,
                "start_line": line_num,
                "reference_id": ref_id,
                "file_path": file_name,
                "is_external": is_external_url(ref_url),
                "is_relative": is_relative_path(ref_url),
                "is_anchor": is_anchor(ref_url),
            }

            if title:
                properties["title"] = title

            if is_cross_document(ref_url):
                properties["target_document"] = extract_target_document(ref_url)

            definitions.append({
                "id": ref_id,
                "type": "Reference",
                "name": ref_label,
                "source": source,
                "properties": properties,
            })

    return definitions
