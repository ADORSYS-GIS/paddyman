"""Extract cross-document style references from markdown prose lines."""
from __future__ import annotations

import re
from typing import Any
from uuid import uuid4

_SECTION_RE = re.compile(r"\b(?:Section|Sec\.?|§|Chapter)\s+(\d+(?:\.\d+)*)\b")
_CITATION_RE = re.compile(r"\[([A-Z][A-Z0-9\-]{1,30})\]")
_ARTICLE_RE = re.compile(r"\b(?:article|Article|Art\.?)\s+(\d+[A-Za-z]?)\b")


def _make_reference(
    file_name: str,
    line_number: int,
    text: str,
    ref_type: str,
    source_text: str,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    ref_id = str(uuid4())
    props: dict[str, Any] = {
        "reference_text": source_text,
        "reference_type": ref_type,
        "context": text.strip(),
        "line_number": line_number,
        "start_line": line_number,
        "target_document": None,
        "reference_id": ref_id,
        "file_path": file_name,
    }
    if extra:
        props.update(extra)
    return {
        "id": ref_id,
        "type": "Reference",
        "name": f"{source_text} reference",
        "source": f"markdown_parser:{file_name}:paragraph:{line_number}",
        "properties": props,
    }


def extract_cross_document_references(
    text: str,
    file_name: str,
) -> list[dict[str, Any]]:
    """Extract section/citation/article references from plain markdown prose."""
    refs: list[dict[str, Any]] = []
    seen: set[tuple[int, str, str]] = set()

    for idx, line in enumerate(text.splitlines(), start=1):
        line_text = line.strip()
        if not line_text:
            continue

        for match in _SECTION_RE.finditer(line_text):
            ref_text = match.group(0)
            key = (idx, "section", ref_text)
            if key in seen:
                continue
            seen.add(key)
            refs.append(
                _make_reference(
                    file_name,
                    idx,
                    line_text,
                    "section",
                    ref_text,
                    {"target_section": match.group(1)},
                )
            )

        for match in _CITATION_RE.finditer(line_text):
            ref_text = match.group(0)
            key = (idx, "external_spec", ref_text)
            if key in seen:
                continue
            seen.add(key)
            refs.append(
                _make_reference(
                    file_name,
                    idx,
                    line_text,
                    "external_spec",
                    ref_text,
                    {"target_spec": match.group(1)},
                )
            )

        for match in _ARTICLE_RE.finditer(line_text):
            ref_text = match.group(0)
            key = (idx, "article", ref_text)
            if key in seen:
                continue
            seen.add(key)
            refs.append(
                _make_reference(
                    file_name,
                    idx,
                    line_text,
                    "article",
                    ref_text,
                    {"target_article": match.group(1)},
                )
            )

    return refs
