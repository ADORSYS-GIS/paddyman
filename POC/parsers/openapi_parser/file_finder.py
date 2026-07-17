"""Finds OpenAPI specification files for processing."""
from __future__ import annotations

import logging
from pathlib import Path

from shared.config import settings

log = logging.getLogger(__name__)


def find_openapi_specs(source_dir: Path) -> list[Path]:
    """Find all OpenAPI specification files in the source directory."""
    if not source_dir.exists():
        log.warning("Source directory %s does not exist", source_dir)
        return []

    # Collect both .yml and .yaml files, then filter out files that are inside
    # any directory named 'archive' (case-insensitive).
    raw_files = set(source_dir.rglob("*.yml")) | set(source_dir.rglob("*.yaml"))

    def _is_in_archive(path: Path) -> bool:
        return any(part.lower() == "archive" for part in path.parts)

    spec_files = sorted(p for p in raw_files if not _is_in_archive(p))
    log.info("Found %d OpenAPI specification files (excluding archive dirs).", len(spec_files))
    return spec_files
