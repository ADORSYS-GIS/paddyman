"""Extract specification metadata from document content.

Fallback extraction when frontmatter and filename parsing are insufficient.
"""
from __future__ import annotations

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


def extract_from_content(text: str) -> dict[str, Any]:
    """Extract specification metadata from document content.

    Args:
        text: Complete markdown document text.

    Returns:
        Dictionary with extracted metadata fields.
    """
    metadata = {}
    
    title = _extract_title(text)
    if title:
        metadata["specification_name"] = title
    
    version = _extract_version(text)
    if version:
        metadata["specification_version"] = version
    
    organization = _extract_organization(text)
    if organization:
        metadata["source_organization"] = organization
    
    pub_date = _extract_publication_date(text)
    if pub_date:
        metadata["publication_date"] = pub_date
    
    return metadata


def _extract_title(text: str) -> str | None:
    """Extract title from first level-1 heading."""
    for line in text.splitlines()[:50]:
        stripped = line.strip()
        if stripped.startswith("# ") and len(stripped) > 2:
            title = stripped[2:].strip()
            # Remove markdown link artifacts
            return re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", title)
    return None


def _extract_version(text: str) -> str | None:
    """Extract version from content."""
    lines = text.splitlines()[:20]
    content_snippet = "\n".join(lines)
    
    patterns = [
        r"[Vv]ersion[:\s]+(\d+\.\d+(?:\.\d+)?)",
        r"[Vv]\.?\s*(\d+\.\d+(?:\.\d+)?)",
        r"Release\s+(\d+\.\d+(?:\.\d+)?)",
    ]
    
    for pattern in patterns:
        match = re.search(pattern, content_snippet)
        if match:
            return match.group(1)
    return None


def _extract_organization(text: str) -> str | None:
    """Extract source organization from content."""
    lines = text.splitlines()[:30]
    content_snippet = "\n".join(lines)
    
    known_orgs = [
        "Berlin Group",
        "NextGenPSD2",
        "STET",
        "Open Banking",
        "European Banking Authority",
        "EBA",
    ]
    
    for org in known_orgs:
        if org in content_snippet:
            return org
    
    # Generic pattern: "by Organization Name"
    match = re.search(r"[Bb]y\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)", content_snippet)
    if match:
        return match.group(1)
    return None


def _extract_publication_date(text: str) -> str | None:
    """Extract publication date from content."""
    lines = text.splitlines()[:30]
    content_snippet = "\n".join(lines)
    
    patterns = [
        r"[Pp]ublished[:\s]+(\d{4}-\d{2}-\d{2})",
        r"[Pp]ublication [Dd]ate[:\s]+(\d{4}-\d{2}-\d{2})",
        r"[Dd]ate[:\s]+(\d{4}-\d{2}-\d{2})",
        r"(\d{2}/\d{2}/\d{4})",
        r"(\d{4}/\d{2}/\d{2})",
    ]
    
    for pattern in patterns:
        match = re.search(pattern, content_snippet)
        if match:
            return match.group(1)
    return None

