"""Build Reference entity dicts from markdown links and references.

Converts markdown links, image references, and reference definitions into
the flat entity format expected by the normalized JSON output schema.
"""
from __future__ import annotations

import logging
from typing import Any

from .reference_extractors import (
    extract_inline_links,
    extract_images,
    extract_reference_definitions,
    extract_autolinks,
    extract_footnotes,
)
from .cross_document_reference_extractor import extract_cross_document_references

logger = logging.getLogger(__name__)


def create_reference_entities(
    text: str,
    file_name: str,
) -> list[dict[str, Any]]:
    """Extract Reference entities from markdown text.

    Extracts all reference types: inline links, images, reference definitions,
    autolinks, and footnotes.

    Args:
        text:      Markdown text content.
        file_name: Name of the markdown file (for source identification).

    Returns:
        List of Reference entity dicts.
    """
    references: list[dict[str, Any]] = []

    # Extract all reference types
    references.extend(extract_inline_links(text, file_name))
    references.extend(extract_images(text, file_name))
    references.extend(extract_reference_definitions(text, file_name))
    references.extend(extract_autolinks(text, file_name))
    references.extend(extract_footnotes(text, file_name))
    references.extend(extract_cross_document_references(text, file_name))

    return references

