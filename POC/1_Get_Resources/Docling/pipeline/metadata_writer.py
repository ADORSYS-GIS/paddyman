"""Per-chunk metadata extraction and writing utilities.

Public API:
- ``extract_version``       — extract version string from a PDF path.
- ``extract_heading_pages`` — called by :mod:`converter` after Docling conversion.
- ``build_section_page_map``— called by :mod:`splitter` after section files are written.
- ``write_chunk_metadata``  — called by :mod:`chunker` after each chunk file is written.
"""
from __future__ import annotations

import json
import logging
import pathlib
import re
from typing import Any

logger = logging.getLogger(__name__)


def extract_version(pdf_path: pathlib.Path) -> str:
    """Return the first semantic version found in *pdf_path* parts, or ``""``."""
    for part in reversed(pdf_path.parts):
        m = re.search(r"\b(\d+\.\d+(?:\.\d+)*)\b", part)
        if m:
            return m.group(1)
    return ""


def extract_heading_pages(doc: Any) -> list[dict[str, Any]]:
    """Return ordered ``{heading, page_no}`` dicts for every section header in *doc*.

    Supports docling_core >=2 and legacy docling <2 import paths.
    Returns an empty list when labels are unavailable or the doc has no headers.
    """
    label_cls = None
    for module in ("docling_core.types.doc", "docling.datamodel.base_models"):
        try:
            import importlib
            mod = importlib.import_module(module)
            label_cls = getattr(mod, "DocItemLabel", None)
            if label_cls is not None:
                break
        except ImportError:
            continue

    result: list[dict[str, Any]] = []
    for text_item in getattr(doc, "texts", []):
        label = getattr(text_item, "label", None)
        prov = getattr(text_item, "prov", None)
        if not prov:
            continue
        is_header = (
            label == label_cls.SECTION_HEADER
            if label_cls is not None
            else "section_header" in str(label).lower()
        )
        if is_header:
            result.append({"heading": text_item.text, "page_no": prov[0].page_no})
    return result


def build_section_page_map(
    heading_pages: list[dict[str, Any]],
    section_names: list[str],
    num_pages: int,
) -> dict[str, list[int]]:
    """Map every section stem to the list of 1-based PDF pages it spans.

    Sections are matched to Docling headings by normalising both to lowercase
    alphanumeric slugs.  Unmatched sections receive an empty page list.
    The preamble section gets all pages before the first matched heading.
    """
    def _norm(text: str) -> str:
        return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")[:80]

    heading_lookup: dict[str, int] = {}
    for item in heading_pages:
        key = _norm(item["heading"])
        if key not in heading_lookup:
            heading_lookup[key] = item["page_no"]

    ordered: list[tuple[str, int]] = []
    for name in section_names:
        slug_part = re.sub(r"^\d+_", "", name, count=1)
        page = heading_lookup.get(slug_part)
        if page is not None:
            ordered.append((name, page))

    page_map: dict[str, list[int]] = {}
    for i, (name, start_page) in enumerate(ordered):
        end_page = ordered[i + 1][1] if i + 1 < len(ordered) else num_pages
        page_map[name] = list(range(start_page, end_page + 1))

    preamble = next((n for n in section_names if n.endswith("preamble")), None)
    if preamble is not None:
        first = ordered[0][1] if ordered else 1
        page_map[preamble] = list(range(1, first)) or [1]

    return page_map


def write_chunk_metadata(
    chunk_path: pathlib.Path,
    doc_meta: dict[str, Any],
    page_numbers: list[int],
    chunk_id: int,
) -> None:
    """Write ``<stem>.metadata.json`` next to *chunk_path* (idempotent).

    The file is only written when its content differs from what is on disk.
    """
    metadata: dict[str, Any] = {
        "title": doc_meta.get("title", ""),
        "version": doc_meta.get("version", ""),
        "slug": doc_meta.get("slug", ""),
        "source_pdf": doc_meta.get("source_pdf", ""),
        "page_numbers": page_numbers,
        "chunk_id": chunk_id,
        "chunk_file": chunk_path.name,
    }
    meta_path = chunk_path.parent / (chunk_path.stem + ".metadata.json")
    content = json.dumps(metadata, indent=2, ensure_ascii=False)
    if meta_path.exists() and meta_path.read_text(encoding="utf-8") == content:
        return
    meta_path.write_text(content, encoding="utf-8")
    logger.debug("  wrote %s", meta_path.name)

