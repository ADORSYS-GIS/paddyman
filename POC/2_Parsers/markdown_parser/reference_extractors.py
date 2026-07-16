"""Reference extraction utilities for markdown.

This module re-exports all reference extraction functions for backward compatibility.
Actual implementations are in:
- reference_link_extractors.py - inline links and reference definitions
- reference_image_extractors.py - images
- reference_advanced_extractors.py - autolinks and footnotes
"""
from __future__ import annotations

from .reference_link_extractors import (
    extract_inline_links,
    extract_reference_definitions,
)
from .reference_image_extractors import extract_images
from .reference_advanced_extractors import extract_autolinks, extract_footnotes

__all__ = [
    "extract_inline_links",
    "extract_images",
    "extract_reference_definitions",
    "extract_autolinks",
    "extract_footnotes",
]



