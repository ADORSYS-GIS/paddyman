"""Document ingestion for the Markdown Parser.

This module provides a single function `load_documents` which reads complete
Markdown specification files from the directory configured in
`shared.config.settings.markdown_spec_dir` or from an explicitly provided path.

Each Markdown file represents a complete specification document and is returned
as a document dictionary for downstream parser stages.

Behavior:
- If *source_dir* is None the path is read from :mod:`shared.config.settings`.
- If the directory does not exist or is invalid an empty list is returned.
- Only .md files are processed.
- Specification metadata is extracted from frontmatter, filename, and content.
- Any errors from the reader are caught and result in an empty list being
  returned (logged). This keeps the ingestion stage tolerant to bad input.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterable

logger = logging.getLogger(__name__)


def load_documents(source_dir: Path | str | None = None) -> list:
    """Load complete Markdown specification files from *source_dir*.

    Args:
        source_dir: Optional path to the directory containing Markdown files.
            When omitted the value is obtained from
            :data:`shared.config.settings.markdown_spec_dir`.

    Returns:
        List of document dictionaries. Each dict contains:
            - 'text': file content as string
            - 'file_path': absolute path to the file
            - 'file_name': base filename
            - 'document_id': specification identifier derived from filename
            - 'specification_metadata': extracted metadata dict
        Returns an empty list for non-existent or invalid directories.
    """
    from shared.config import settings  # deferred import for testability
    from .metadata_extractor import extract_specification_metadata

    if source_dir is None:
        source_dir = settings.markdown_spec_dir

    source_path = Path(source_dir)

    if not source_path.exists() or not source_path.is_dir():
        logger.warning("Source directory does not exist or is not a directory: %s", source_path)
        return []

    documents = []
    
    # Read all .md files from the directory
    for md_file in source_path.glob("*.md"):
        try:
            text = md_file.read_text(encoding="utf-8")
            
            # Derive document ID from filename (remove _clean.md suffix if present)
            file_stem = md_file.stem
            if file_stem.endswith("_clean"):
                doc_id = file_stem[:-6]  # Remove '_clean' suffix
            else:
                doc_id = file_stem
            
            # Extract specification metadata
            spec_metadata = extract_specification_metadata(
                md_file, text, base_dir=source_path
            )
            
            doc = {
                "text": text,
                "file_path": str(md_file.absolute()),
                "file_name": md_file.name,
                "document_id": doc_id,
                "specification_metadata": spec_metadata,
            }
            
            documents.append(doc)
            logger.debug("Loaded document: %s", md_file.name)
            
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to read %s: %s", md_file, exc)
            continue

    logger.info("Loaded %d Markdown documents from %s", len(documents), source_path)
    return documents
