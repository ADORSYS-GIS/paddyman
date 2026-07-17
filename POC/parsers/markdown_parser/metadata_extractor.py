"""Orchestrate specification metadata extraction.

Combines frontmatter, filename, and content extraction with fallback hierarchy.
"""
from __future__ import annotations

import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .frontmatter_parser import (
    parse_frontmatter,
    extract_specification_metadata as extract_from_frontmatter,
)
from .filename_metadata import extract_from_filename
from .content_metadata import extract_from_content

logger = logging.getLogger(__name__)


def extract_specification_metadata(
    file_path: Path, text: str, base_dir: Path | None = None
) -> dict[str, Any]:
    """Extract complete specification metadata using fallback hierarchy.

    Extraction hierarchy:
    1. YAML frontmatter (highest priority)
    2. Filename patterns
    3. Content analysis
    4. Default values (lowest priority)

    Args:
        file_path: Path to the markdown file.
        text: Complete document text.
        base_dir: Base directory for computing relative paths.

    Returns:
        Complete specification metadata dictionary.
    """
    metadata = _initialize_metadata(file_path, base_dir)
    
    # Extract from frontmatter (highest priority)
    frontmatter = parse_frontmatter(text)
    if frontmatter:
        frontmatter_metadata = extract_from_frontmatter(frontmatter)
        metadata.update(frontmatter_metadata)
        logger.debug("Extracted metadata from frontmatter for %s", file_path.name)
    
    # Extract from filename (fill gaps)
    filename_metadata = extract_from_filename(file_path)
    for key, value in filename_metadata.items():
        if key not in metadata or not metadata.get(key):
            metadata[key] = value
    if filename_metadata:
        logger.debug("Extracted metadata from filename for %s", file_path.name)
    
    # Extract from content (fallback)
    content_metadata = extract_from_content(text)
    for key, value in content_metadata.items():
        if key not in metadata or not metadata.get(key):
            metadata[key] = value
    if content_metadata:
        logger.debug("Extracted metadata from content for %s", file_path.name)
    
    # Apply defaults for missing fields
    _apply_defaults(metadata, file_path)
    
    return metadata


def _initialize_metadata(file_path: Path, base_dir: Path | None) -> dict[str, Any]:
    """Initialize metadata with file provenance.

    Args:
        file_path: Path to the markdown file.
        base_dir: Base directory for relative path computation.

    Returns:
        Initialized metadata dictionary.
    """
    relative_path = file_path.name
    if base_dir and file_path.is_relative_to(base_dir):
        relative_path = str(file_path.relative_to(base_dir))
    
    return {
        "file_path": str(file_path.absolute()),
        "relative_path": relative_path,
        "file_name": file_path.name,
        "source_parser": "markdown_parser",
        "parsed_at": datetime.now(UTC).isoformat(),
    }


def _apply_defaults(metadata: dict[str, Any], file_path: Path) -> None:
    """Apply default values for missing required fields.

    Args:
        metadata: Metadata dictionary to update in-place.
        file_path: Path to the markdown file.
    """
    if "specification_name" not in metadata or not metadata["specification_name"]:
        metadata["specification_name"] = file_path.stem
        logger.debug("Using filename as specification_name: %s", file_path.stem)
    
    if "specification_version" not in metadata or not metadata["specification_version"]:
        metadata["specification_version"] = "unknown"
    
    if "specification_category" not in metadata or not metadata["specification_category"]:
        metadata["specification_category"] = "Specification"
