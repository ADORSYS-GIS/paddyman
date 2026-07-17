"""Converts complete markdown specification files to NormalizedDocument objects."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List

from shared.models import NormalizedDocument, SourceMetadata
from shared.provenance import ensure_provenance
from datetime import datetime, timezone
from uuid import uuid5, NAMESPACE_URL
from .structure import _extract_links
from .structure_helpers import _extract_headings_with_positions, _extract_table_blocks, _extract_list_blocks
from .metadata_extractor import extract_specification_metadata
from shared.id_factory import make_document_id

logger = logging.getLogger(__name__)


def markdown_to_normalized_docs(
    md_file: Path
) -> List[NormalizedDocument]:
    """
    Reads a complete markdown specification file and converts it to a NormalizedDocument.

    Args:
        md_file: Path to the markdown specification file.

    Returns:
        A list containing one NormalizedDocument for the complete specification.
    """
    try:
        text = md_file.read_text(encoding="utf-8")
    except Exception as exc:
        logger.warning(f"Failed to read {md_file}: {exc}")
        text = ""

    headings = _extract_headings_with_positions(text) if text else []
    tables = _extract_table_blocks(text) if text else []
    lists = _extract_list_blocks(text) if text else []
    references = _extract_links(text) if text else {"inline": [], "definitions": [], "citations": []}

    # Generate canonical document id. Preserve previous behaviour of
    # dropping a trailing "_clean" suffix from the stem for IDs.
    file_stem = md_file.stem
    if file_stem.endswith("_clean"):
        chosen_name = file_stem[:-6]
    else:
        chosen_name = file_stem
    # Keep the historical markdown id format (bare specification name)
    # to avoid breaking downstream consumers. This preserves backwards
    # compatibility while other parsers adopt the canonical form.
    document_id = chosen_name

    # Extract specification metadata
    spec_metadata = extract_specification_metadata(md_file, text)

    # Create metadata and include deterministic id/ingested_at so chunk-level
    # source metadata is stable across repeated runs.
    determinist_id = str(uuid5(NAMESPACE_URL, str(md_file.resolve())))
    # If file is missing (tests may pass non-existent paths) fall back to
    # current time instead of raising.
    if md_file.exists():
        determinist_ingested = datetime.fromtimestamp(md_file.stat().st_mtime, tz=timezone.utc).isoformat()
    else:
        determinist_ingested = datetime.now(timezone.utc).isoformat()

    # Create metadata (include headings and hierarchical sections)
    # Build sections from headings and assign child references to tables/lists by index
    sections: List[Dict[str, Any]] = []
    if headings:
        for idx, hdr in enumerate(headings):
            start_line = hdr.get("line", 1)
            end_line = headings[idx + 1]["line"] - 1 if idx + 1 < len(headings) else text.count("\n") + 1
            children = []
            for ti, t in enumerate(tables):
                if t.get("start_line") is not None and t["start_line"] >= start_line and t["end_line"] <= end_line:
                    children.append({"type": "table", "index": ti})
            for li, l in enumerate(lists):
                if l.get("start_line") is not None and l["start_line"] >= start_line and l["end_line"] <= end_line:
                    children.append({"type": "list", "index": li})
            sections.append({"title": hdr.get("text"), "level": hdr.get("level"), "start_line": start_line, "end_line": end_line, "children": children})
    else:
        if text.strip():
            sections.append({"title": None, "level": 0, "start_line": 1, "end_line": text.count("\n") + 1, "children": []})

    metadata = {
        "file_path": str(md_file.absolute()),
        "file_name": md_file.name,
        "specification": document_id,
        "headings": [{k: v for k, v in h.items() if k != "pos"} for h in headings],
        "sections": sections,
        "tables": tables,
        "references": references,
        "lists": lists,
        "source_parser": "markdown_parser",
        "id": determinist_id,
        "ingested_at": determinist_ingested,
    }
    # Merge specification metadata into source_metadata
    metadata.update(spec_metadata)
    # Use deterministic parsed timestamp derived from the file mtime so
    # repeated runs produce identical `parsed_at` values for idempotency
    metadata["parsed_at"] = determinist_ingested

    # Normalize path/file fields then normalise parser metadata into a
    # SourceMetadata dict for inclusion in normalized bundles.
    from shared.provenance import normalize_paths

    canonical_meta = normalize_paths(metadata, root=md_file.parent)
    src = SourceMetadata.from_parser_metadata(canonical_meta).to_dict()

    # Create the normalized document and ensure canonical provenance
    prov = ensure_provenance(None, md_file, "markdown_parser", "markdown_parser")
    doc = NormalizedDocument(
        document_id=document_id,
        text=text,
        source_parser="markdown_parser",
        source_metadata=src,
        provenance=prov,
    )

    return [doc]

