"""Advanced reference extraction for autolinks and footnotes.

Extracts autolink and footnote references from markdown.
"""
from __future__ import annotations

import re
from typing import Any
from uuid import uuid4

from .reference_classifiers import is_external_url

# Regex patterns
AUTOLINK_PATTERN = re.compile(r'<((?:https?|ftp|mailto|tel):[^>]+)>')
FOOTNOTE_REF_PATTERN = re.compile(r'\[\^([^\]]+)\](?!:)')
FOOTNOTE_DEF_PATTERN = re.compile(r'^\[\^([^\]]+)\]:\s*(.+)', re.MULTILINE)


def extract_autolinks(text: str, file_name: str) -> list[dict[str, Any]]:
    """Extract autolinks (<https://example.com>).

    Args:
        text:      Markdown text content.
        file_name: Name of the markdown file.

    Returns:
        List of autolink Reference entity dicts.
    """
    autolinks: list[dict[str, Any]] = []
    lines = text.splitlines()

    for line_num, line in enumerate(lines, start=1):
        for match in AUTOLINK_PATTERN.finditer(line):
            target_url = match.group(1)

            ref_id = str(uuid4())
            source = f"markdown_parser:{file_name}:autolink:{line_num}"

            autolinks.append({
                "id": ref_id,
                "type": "Reference",
                "name": target_url,
                "source": source,
                "properties": {
                    "ref_type": "autolink",
                    "target_url": target_url,
                    "start_line": line_num,
                    "reference_id": ref_id,
                    "file_path": file_name,
                    "is_external": is_external_url(target_url),
                },
            })

    return autolinks


def extract_footnotes(text: str, file_name: str) -> list[dict[str, Any]]:
    """Extract footnote references and definitions.

    Args:
        text:      Markdown text content.
        file_name: Name of the markdown file.

    Returns:
        List of footnote Reference entity dicts.
    """
    footnotes: list[dict[str, Any]] = []
    
    # Build a map of footnote definitions
    footnote_defs: dict[str, tuple[int, str]] = {}
    lines = text.splitlines()
    
    for line_num, line in enumerate(lines, start=1):
        match = FOOTNOTE_DEF_PATTERN.match(line)
        if match:
            label = match.group(1)
            content = match.group(2)
            footnote_defs[label] = (line_num, content)
    
    # Extract footnote references
    for line_num, line in enumerate(lines, start=1):
        for match in FOOTNOTE_REF_PATTERN.finditer(line):
            label = match.group(1)
            
            ref_id = str(uuid4())
            source = f"markdown_parser:{file_name}:footnote:{line_num}"
            
            properties = {
                "ref_type": "footnote",
                "footnote_label": label,
                "start_line": line_num,
                "reference_id": ref_id,
                "file_path": file_name,
            }
            
            # Link to definition if it exists
            if label in footnote_defs:
                def_line, content = footnote_defs[label]
                properties["definition_line"] = def_line
                properties["footnote_content"] = content
            
            footnotes.append({
                "id": ref_id,
                "type": "Reference",
                "name": f"Footnote {label}",
                "source": source,
                "properties": properties,
            })
    
    return footnotes
