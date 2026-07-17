"""Build Document entity dicts from markdown files.

Converts markdown document metadata into the flat entity format expected by
the normalized JSON output schema.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any
from uuid import uuid5, NAMESPACE_URL

logger = logging.getLogger(__name__)


def create_document_entity(
    file_path: Path,
    text: str,
    document_id: str,
    specification_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Convert markdown file metadata to a Document entity dict.

    Args:
        file_path:   Path to the markdown file.
        text:        Full text content of the document.
        document_id: Unique identifier for the document.
        specification_metadata: Optional specification metadata dict.

    Returns:
        Entity dict conforming to the NormalizedJson.entities schema.
    """
    if specification_metadata is None:
        specification_metadata = {}
    lines = text.splitlines()
    word_count = len(text.split())
    line_count = len(lines)

    # Extract title from first heading or use filename
    title = _extract_title_from_text(text) or file_path.stem

    entity_id = str(uuid5(NAMESPACE_URL, f"document:{document_id}:{str(file_path.resolve())}:{title}"))
    # `source` MUST point to the canonical document id for provenance resolution
    source = document_id

    properties = {
        "title": title,
        "file_path": str(file_path.absolute()),
        "relative_path": specification_metadata.get("relative_path", file_path.name),
        "source_parser": "markdown_parser",
        "word_count": word_count,
        "line_count": line_count,
        "document_id": document_id,
    }
    
    # Add specification metadata fields
    spec_fields = [
        "specification_name",
        "specification_version",
        "specification_category",
        "source_organization",
        "publication_date",
    ]
    for field in spec_fields:
        if field in specification_metadata:
            properties[field] = specification_metadata[field]

    return {
        "id": entity_id,
        "type": "Document",
        "name": title,
        "source": source,
        "properties": properties,
    }


def _extract_title_from_text(text: str) -> str | None:
    """Extract title from the first level-1 heading in the text.

    Args:
        text: Markdown text content.

    Returns:
        Title text if found, None otherwise.
    """
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("# ") and len(stripped) > 2:
            return stripped[2:].strip()
    return None
