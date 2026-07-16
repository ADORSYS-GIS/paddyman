"""URL utility functions for reference extraction.

Helper functions for extracting and parsing URL components.
"""
from __future__ import annotations

from pathlib import Path


def extract_target_document(url: str) -> str | None:
    """Extract the target document path from a cross-document reference.

    Args:
        url: URL string to parse.

    Returns:
        Target document path, or None if not a cross-document reference.

    Examples:
        >>> extract_target_document("../docs/other.md")
        '../docs/other.md'
        >>> extract_target_document("./spec.md#section")
        './spec.md'
        >>> extract_target_document("https://example.com")
        None
    """
    from .reference_classifiers import is_cross_document
    
    if not is_cross_document(url):
        return None
    
    # Remove anchor if present
    return url.split("#")[0]


def extract_anchor_from_url(url: str) -> str | None:
    """Extract anchor fragment from a URL.

    Args:
        url: URL string to parse.

    Returns:
        Anchor fragment (without #), or None if no anchor.

    Examples:
        >>> extract_anchor_from_url("#section-heading")
        'section-heading'
        >>> extract_anchor_from_url("./doc.md#intro")
        'intro'
        >>> extract_anchor_from_url("https://example.com")
        None
    """
    if "#" not in url:
        return None
    
    # Split on # and return everything after it
    parts = url.split("#", 1)
    if len(parts) == 2 and parts[1]:
        return parts[1]
    
    return None
