"""Paragraph detection utilities for markdown.

Detects paragraph boundaries and distinguishes paragraphs from other
markdown structural elements.
"""
from __future__ import annotations

import re


def is_paragraph_start(lines: list[str], idx: int) -> bool:
    """Check if a line starts a paragraph.

    Args:
        lines: All lines of text.
        idx:   Current line index.

    Returns:
        True if the line starts a paragraph.
    """
    if idx >= len(lines):
        return False

    line = lines[idx].strip()

    # Empty line is not a paragraph
    if not line:
        return False

    # Skip headings
    if line.startswith("#"):
        return False

    # Skip list markers
    if re.match(r"^[-*+]\s+", line) or re.match(r"^\d+[.)]\s+", line):
        return False

    # Skip table rows
    if line.startswith("|") or "|" in line:
        return False

    # Skip code fence markers
    if line.startswith("```") or line.startswith("~~~"):
        return False

    # Skip blockquotes
    if line.startswith(">"):
        return False

    # Skip horizontal rules
    if re.match(r"^[-*_]{3,}$", line):
        return False

    return True


def is_paragraph_continuation(lines: list[str], idx: int) -> bool:
    """Check if a line continues the current paragraph.

    Args:
        lines: All lines of text.
        idx:   Current line index.

    Returns:
        True if the line continues the paragraph.
    """
    if idx >= len(lines):
        return False

    line = lines[idx].strip()

    # Empty line ends the paragraph
    if not line:
        return False

    # Check if it's a paragraph start (not another structural element)
    return is_paragraph_start(lines, idx)
