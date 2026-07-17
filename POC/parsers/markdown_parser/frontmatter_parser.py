"""Parse YAML frontmatter from markdown documents.

Extracts specification metadata from YAML blocks delimited by '---'.
"""
from __future__ import annotations

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


def parse_frontmatter(text: str) -> dict[str, Any]:
    """Extract YAML frontmatter from markdown text.

    Args:
        text: Complete markdown document text.

    Returns:
        Dictionary of frontmatter fields. Empty dict if no frontmatter found.
    """
    frontmatter = _extract_frontmatter_block(text)
    if not frontmatter:
        return {}

    try:
        import yaml
        return yaml.safe_load(frontmatter) or {}
    except ImportError:
        logger.warning("PyYAML not available; skipping frontmatter parsing")
        return {}
    except Exception as exc:
        logger.warning("Failed to parse YAML frontmatter: %s", exc)
        return {}


def _extract_frontmatter_block(text: str) -> str | None:
    """Extract raw frontmatter block from markdown text.

    Args:
        text: Complete markdown document text.

    Returns:
        Raw YAML text between delimiters, or None if not found.
    """
    # Match frontmatter at start of document: ---\n...\n---
    pattern = r"^---\s*\n(.*?)\n---\s*\n"
    match = re.match(pattern, text, re.DOTALL)
    
    if match:
        return match.group(1)
    
    return None


def extract_specification_metadata(frontmatter: dict[str, Any]) -> dict[str, Any]:
    """Extract specification fields from parsed frontmatter.

    Args:
        frontmatter: Parsed YAML frontmatter dictionary.

    Returns:
        Dictionary with standardized specification metadata fields.
    """
    metadata = {}
    
    # Map common field names to our standard schema
    field_mappings = {
        "specification_name": ["title", "specification_name", "name", "spec_name"],
        "specification_version": ["version", "specification_version", "spec_version"],
        "specification_category": ["category", "specification_category", "type", "doc_type"],
        "source_organization": ["organization", "source_organization", "org", "author"],
        "publication_date": ["published", "publication_date", "date", "pub_date"],
    }
    
    for standard_field, possible_names in field_mappings.items():
        for name in possible_names:
            if name in frontmatter:
                # Convert to string to handle numeric values from YAML
                metadata[standard_field] = str(frontmatter[name])
                break
    
    return metadata
