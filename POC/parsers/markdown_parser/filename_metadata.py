"""Extract specification metadata from filenames.

Parses common filename patterns to extract specification name, version, and
category when frontmatter is unavailable.
"""
from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def extract_from_filename(file_path: Path) -> dict[str, Any]:
    """Extract specification metadata from filename.

    Args:
        file_path: Path to the markdown file.

    Returns:
        Dictionary with extracted metadata fields.
    """
    filename = file_path.stem
    
    # Remove common suffixes
    filename = _remove_common_suffixes(filename)
    
    metadata = {}
    
    # Extract version number
    version = _extract_version(filename)
    if version:
        metadata["specification_version"] = version
        # Remove version from filename for name extraction
        filename = re.sub(r"_v?\d+[._]\d+[._]?\d*", "", filename, flags=re.IGNORECASE)
    
    # Extract specification name
    spec_name = _extract_specification_name(filename)
    if spec_name:
        metadata["specification_name"] = spec_name
    
    # Infer category from filename patterns
    category = _infer_category(filename)
    if category:
        metadata["specification_category"] = category
    
    return metadata


def _remove_common_suffixes(filename: str) -> str:
    """Remove common file suffixes from filename.

    Args:
        filename: Base filename without extension.

    Returns:
        Filename with common suffixes removed.
    """
    suffixes = ["_clean", "_final", "_draft", "_v1", "_v2", "_v3"]
    for suffix in suffixes:
        if filename.lower().endswith(suffix):
            filename = filename[: -len(suffix)]
    return filename


def _extract_version(filename: str) -> str | None:
    """Extract version string from filename.

    Args:
        filename: Base filename without extension.

    Returns:
        Version string if found, None otherwise.
    """
    # Match patterns like: 1_3, 1.3, v1.3, v1_3, 1_3_2, etc.
    patterns = [
        r"_v?(\d+[._]\d+(?:[._]\d+)?)",  # _1_3, _v1.3, _1.3.2
        r"v(\d+[._]\d+(?:[._]\d+)?)",    # v1.3, v1_3_2
    ]
    
    for pattern in patterns:
        match = re.search(pattern, filename, re.IGNORECASE)
        if match:
            version = match.group(1)
            # Normalize separators to dots
            return version.replace("_", ".")
    
    return None


def _extract_specification_name(filename: str) -> str | None:
    """Extract human-readable specification name from filename.

    Args:
        filename: Cleaned filename without version and suffixes.

    Returns:
        Specification name if extracted, None otherwise.
    """
    if not filename:
        return None
    
    # Replace underscores with spaces and title case
    name = filename.replace("_", " ").strip()
    
    # Title case each word
    words = name.split()
    
    # Preserve known acronyms
    acronyms = {"api", "psd2", "ais", "pis", "xs2a", "http", "json", "xml"}
    title_words = []
    for word in words:
        if word.lower() in acronyms:
            title_words.append(word.upper())
        else:
            title_words.append(word.capitalize())
    
    return " ".join(title_words)


def _infer_category(filename: str) -> str | None:
    """Infer specification category from filename patterns.

    Args:
        filename: Cleaned filename.

    Returns:
        Inferred category if pattern matches, None otherwise.
    """
    filename_lower = filename.lower()
    
    if "implementation" in filename_lower or "guidelines" in filename_lower:
        return "Implementation Guidelines"
    elif "operational" in filename_lower or "rules" in filename_lower:
        return "Operational Rules"
    elif "specification" in filename_lower or "spec" in filename_lower:
        return "API Specification"
    elif "reference" in filename_lower or "manual" in filename_lower:
        return "Reference Manual"
    
    return None
