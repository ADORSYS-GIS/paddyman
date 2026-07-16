"""Converts complete markdown specification files to NormalizedDocument objects."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List

from shared.models import NormalizedDocument
from .structure import _extract_tables, _extract_links, _extract_lists
from .metadata_extractor import extract_specification_metadata

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

    # Extract tables, references, and lists from the markdown text
    tables = _extract_tables(text) if text else []
    references = _extract_links(text) if text else {"inline": [], "definitions": [], "citations": []}
    lists = _extract_lists(text) if text else []

    # Generate document ID from filename (remove _clean suffix if present)
    file_stem = md_file.stem
    if file_stem.endswith("_clean"):
        document_id = file_stem[:-6]
    else:
        document_id = file_stem

    # Extract specification metadata
    spec_metadata = extract_specification_metadata(md_file, text)

    # Create metadata
    metadata = {
        "file_path": str(md_file.absolute()),
        "file_name": md_file.name,
        "specification": document_id,
        "tables": tables,
        "references": references,
        "lists": lists,
        "source_parser": "markdown_parser",
    }
    
    # Merge specification metadata into source_metadata
    metadata.update(spec_metadata)

    # Create the normalized document
    doc = NormalizedDocument(
        document_id=document_id,
        text=text,
        source_parser="markdown_parser",
        source_metadata=metadata,
        provenance={
            "stage": "markdown_parser",
            "file": str(md_file),
        },
    )

    return [doc]

