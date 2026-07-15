"""Utility functions for parsing markdown list items.

Provides helper functions for detecting list types, extracting indentation,
and parsing list item content.
"""
from __future__ import annotations

import re


def get_indent_level(line: str) -> int:
    """Calculate indentation level (spaces/tabs).
    
    Args:
        line: Line of text.
        
    Returns:
        Indentation level (0 for no indent).
    """
    stripped = line.lstrip()
    if not stripped:
        return 0
    indent = len(line) - len(stripped)
    return indent // 2  # Assuming 2 spaces per level


def get_list_type(line: str) -> str | None:
    """Determine if a line starts a list and return its type.

    Args:
        line: Line of text.

    Returns:
        "ordered" for numbered lists, "unordered" for bullet lists, or None.
    """
    stripped = line.strip()

    # Check for task list (GitHub Flavored Markdown)
    task_pattern = re.compile(r"^[-*+]\s+\[[ xX]\]\s+")
    if task_pattern.match(stripped):
        return "unordered"

    # Check for bullet list markers: -, *, +
    bullet_pattern = re.compile(r"^[-*+]\s+")
    if bullet_pattern.match(stripped):
        return "unordered"

    # Check for ordered list markers: 1. or 1)
    ordered_pattern = re.compile(r"^\d+[.)]\s+")
    if ordered_pattern.match(stripped):
        return "ordered"

    return None


def get_ordered_start(line: str) -> int:
    """Extract starting number from ordered list.
    
    Args:
        line: Line containing ordered list marker.
        
    Returns:
        Starting number (default 1).
    """
    match = re.match(r"^\s*(\d+)[.)]\s+", line)
    return int(match.group(1)) if match else 1


def extract_list_item_text(line: str) -> str:
    """Extract the text content from a list item line.
    
    Args:
        line: List item line.
        
    Returns:
        First 50 characters of item text.
    """
    stripped = line.strip()
    # Remove list markers and task checkboxes
    text = re.sub(r"^[-*+]\s+(\[[ xX]\]\s+)?", "", stripped)
    text = re.sub(r"^\d+[.)]\s+", "", text)
    return text[:50]  # Preview first 50 chars
