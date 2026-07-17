"""Image reference extraction for markdown.

Extracts image references from markdown.
"""
from __future__ import annotations

import re
from typing import Any
from uuid import uuid5, NAMESPACE_URL

from .reference_classifiers import is_external_url, is_relative_path

# Regex pattern
IMAGE_PATTERN = re.compile(r'!\[([^\]]*)\]\(([^)"\s]+)(?:\s+"([^"]+)")?\)')


def extract_images(text: str, file_name: str) -> list[dict[str, Any]]:
    """Extract image references with alt text, title, and classification.

    Args:
        text:      Markdown text content.
        file_name: Name of the markdown file.

    Returns:
        List of image Reference entity dicts.
    """
    images: list[dict[str, Any]] = []
    lines = text.splitlines()

    for line_num, line in enumerate(lines, start=1):
        for match in IMAGE_PATTERN.finditer(line):
            alt_text = match.group(1) or ""
            image_url = match.group(2)
            title = match.group(3) or None

            ref_id = str(uuid5(NAMESPACE_URL, f"imgref:{file_name}:{line_num}:{alt_text}:{image_url}"))
            source = f"markdown_parser:{file_name}:image:{line_num}"

            properties = {
                "ref_type": "image",
                "target_url": image_url,
                "alt_text": alt_text,
                "start_line": line_num,
                "reference_id": ref_id,
                "file_path": file_name,
                "is_external": is_external_url(image_url),
                "is_relative": is_relative_path(image_url),
            }

            if title:
                properties["title"] = title

            images.append({
                "id": ref_id,
                "type": "Reference",
                "name": alt_text or "Image",
                "source": source,
                "properties": properties,
            })

    return images
