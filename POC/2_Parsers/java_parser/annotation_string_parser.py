"""String-based annotation argument parsing.

Parses raw annotation argument strings (outside the AST pipeline) into
structured attribute dicts.  Used by :mod:`annotation_normalizer` to
process plain annotation strings and legacy ``value``-only
:class:`~java_parser.java_ast.models.JavaAnnotation` instances.
"""
from __future__ import annotations

from typing import Any


def _split_on_commas(value: str) -> list[str]:
    """Split *value* on top-level commas, respecting quotes and brackets.

    Args:
        value: Raw annotation argument string.

    Returns:
        List of trimmed, non-empty parts.
    """
    parts: list[str] = []
    depth = 0
    in_quote = False
    quote_char = ""
    start = 0
    for i, ch in enumerate(value):
        if in_quote:
            if ch == quote_char and (i == 0 or value[i - 1] != "\\"):
                in_quote = False
        elif ch in ('"', "'"):
            in_quote = True
            quote_char = ch
        elif ch in ("(", "{", "["):
            depth += 1
        elif ch in (")", "}", "]"):
            depth -= 1
        elif ch == "," and depth == 0:
            parts.append(value[start:i].strip())
            start = i + 1
    parts.append(value[start:].strip())
    return [p for p in parts if p]


def parse_single_value(text: str) -> Any:
    """Convert a single attribute value text to a Python value.

    Array literals ``{...}`` are split into lists.  String literals have
    their surrounding quotes stripped.  All other text is returned as-is,
    covering enum references, numeric and boolean literals.

    Args:
        text: Raw text of a single annotation value.

    Returns:
        ``str`` or ``list[str]``.
    """
    text = text.strip()
    if text.startswith("{") and text.endswith("}"):
        inner = text[1:-1].strip()
        return [p.strip().strip('"').strip("'") for p in _split_on_commas(inner)]
    return text.strip('"').strip("'")


def parse_attributes(value: str | None) -> dict[str, Any]:
    """Parse an annotation argument string into a key-value attribute map.

    Handles two forms:

    - Named pairs: ``value="/path", method=RequestMethod.GET``
    - Single value: ``"/path"`` → ``{"value": "/path"}``

    Args:
        value: Raw text of the annotation argument list (without parentheses).

    Returns:
        Dict of attribute names to their parsed values.
    """
    if not value:
        return {}
    value = value.strip()
    if "=" in value:
        attrs: dict[str, Any] = {}
        for part in _split_on_commas(value):
            if "=" in part:
                key, _, val = part.partition("=")
                attrs[key.strip()] = parse_single_value(val.strip())
        return attrs
    return {"value": parse_single_value(value)}
