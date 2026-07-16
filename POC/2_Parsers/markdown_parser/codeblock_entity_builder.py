"""Build CodeBlock entity dicts from markdown code blocks.

Converts fenced code blocks (```language ... ```) into the flat entity format
expected by the normalized JSON output schema.
"""
from __future__ import annotations

import logging
from typing import Any
from uuid import uuid4

logger = logging.getLogger(__name__)

_EXAMPLE_LANGUAGES = frozenset({"json", "xml", "yaml", "yml", "jsonc", "csv", "toml"})


def create_codeblock_entities(
    text: str,
    file_name: str,
) -> list[dict[str, Any]]:
    """Extract CodeBlock entities from markdown text.

    Args:
        text:      Markdown text content.
        file_name: Name of the markdown file (for source identification).

    Returns:
        List of CodeBlock entity dicts.
    """
    code_blocks: list[dict[str, Any]] = []
    lines = text.splitlines()

    i = 0
    while i < len(lines):
        if _is_code_fence_start(lines[i]):
            code_block = _extract_code_block(lines, i, file_name)
            if code_block:
                code_blocks.append(code_block)
                i = code_block["properties"]["end_line"]
            else:
                i += 1
        else:
            i += 1

    return code_blocks


def _is_code_fence_start(line: str) -> bool:
    """Check if a line starts a code fence.

    Args:
        line: Line of text.

    Returns:
        True if the line is a code fence start marker.
    """
    stripped = line.strip()
    return stripped.startswith("```") or stripped.startswith("~~~")


def _extract_code_block(
    lines: list[str],
    start_idx: int,
    file_name: str,
) -> dict[str, Any] | None:
    """Extract a complete code block starting from the given line index.

    Args:
        lines:     All lines of text.
        start_idx: Starting line index (0-based).
        file_name: Name of the markdown file.

    Returns:
        CodeBlock entity dict or None if extraction fails.
    """
    fence_line = lines[start_idx].strip()
    fence_marker = "```" if fence_line.startswith("```") else "~~~"
    language = fence_line[len(fence_marker):].strip() or "plaintext"

    # Find the closing fence
    end_idx = start_idx + 1
    while end_idx < len(lines):
        if lines[end_idx].strip().startswith(fence_marker):
            break
        end_idx += 1

    if end_idx >= len(lines):
        return None

    # Extract code content
    code_lines = lines[start_idx + 1:end_idx]
    line_count = len(code_lines)
    code_content = "\n".join(code_lines)

    lang_lower = language.lower()
    is_example = lang_lower in _EXAMPLE_LANGUAGES
    is_request = lang_lower == "http"

    code_block_id = str(uuid4())
    start_line = start_idx + 1  # Convert to 1-based
    end_line = end_idx + 2  # Include closing fence + move to next line
    source = f"markdown_parser:{file_name}:codeblock:{start_line}"

    return {
        "id": code_block_id,
        "type": "CodeBlock",
        "name": f"{language} code at line {start_line}",
        "source": source,
        "properties": {
            "language": language,
            "code": code_content,
            "line_count": line_count,
            "start_line": start_line,
            "end_line": end_line,
            "caption": None,
            "is_example": is_example,
            "is_request": is_request,
            "parent_section": None,
            "code_block_id": code_block_id,
        },
    }


def enrich_codeblock_parent_sections(
    codeblock_entities: list[dict[str, Any]],
    section_entities: list[dict[str, Any]],
) -> None:
    """Set parent_section on each CodeBlock entity in-place."""
    for codeblock in codeblock_entities:
        cb_line = codeblock["properties"]["start_line"]
        codeblock["properties"]["parent_section"] = _find_parent_section(
            cb_line, section_entities
        )


def _find_parent_section(
    line: int,
    section_entities: list[dict[str, Any]],
) -> str | None:
    """Return name of the smallest containing section for a line number."""
    best: dict[str, Any] | None = None
    best_start = -1
    for section in section_entities:
        s_start = section["properties"]["start_line"]
        s_end = section["properties"]["end_line"]
        if s_start <= line <= s_end and s_start > best_start:
            best = section
            best_start = s_start
    return best["name"] if best else None
