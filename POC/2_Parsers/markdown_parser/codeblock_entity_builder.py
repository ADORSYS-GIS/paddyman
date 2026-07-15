"""Build CodeBlock entity dicts from markdown code blocks.

Converts fenced code blocks (```language ... ```) into the flat entity format
expected by the normalized JSON output schema.
"""
from __future__ import annotations

import logging
from typing import Any
from uuid import uuid4

logger = logging.getLogger(__name__)


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

    # Extract language from fence line (e.g., ```python)
    language = fence_line[len(fence_marker):].strip() or "plaintext"

    # Find the closing fence
    end_idx = start_idx + 1
    while end_idx < len(lines):
        if lines[end_idx].strip().startswith(fence_marker):
            break
        end_idx += 1

    # If no closing fence found, invalid code block
    if end_idx >= len(lines):
        return None

    # Extract code content (between fences)
    code_lines = lines[start_idx + 1:end_idx]
    line_count = len(code_lines)

    # Create preview (first 5 lines)
    code_preview = "\n".join(code_lines[:5])
    if line_count > 5:
        code_preview += "\n..."

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
            "code_preview": code_preview,
            "line_count": line_count,
            "start_line": start_line,
            "end_line": end_line,
            "code_block_id": code_block_id,
        },
    }
