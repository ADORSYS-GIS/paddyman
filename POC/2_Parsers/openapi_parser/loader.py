"""YAML loader for OpenAPI specifications (Chunk 3.1).

Responsibilities:
- Discover ``.yaml`` / ``.yml`` files under the configured ``yaml_spec_dir``.
- Parse raw YAML content using PyYAML.
- Delegate metadata extraction to :mod:`~openapi_parser.info_extractor`.

Intentionally excluded from this module:
- paths / operations extraction
- schema extraction
- API relationship analysis
"""
from __future__ import annotations

import logging
from pathlib import Path

import yaml

from openapi_parser.info_extractor import (
    InfoExtractionError,
    extract_info_metadata,
)
from openapi_parser.models import OpenApiMetadata

logger = logging.getLogger(__name__)

_YAML_EXTENSIONS: frozenset[str] = frozenset({".yaml", ".yml"})

class OpenApiLoadError(Exception):
    """Raised when a YAML file cannot be parsed as a valid OpenAPI document."""


def load_yaml_files(source_dir: Path | str | None = None) -> list[OpenApiMetadata]:
    """Discover and load all OpenAPI YAML files from *source_dir*.

    When *source_dir* is ``None`` the path is read from
    :data:`shared.config.settings.yaml_spec_dir`.

    Files that cannot be parsed are logged and skipped; the remaining files
    are still processed.

    Args:
        source_dir: Root directory to scan recursively for YAML files.

    Returns:
        List of :class:`~openapi_parser.models.OpenApiMetadata` instances,
        one per successfully parsed OpenAPI file.
    """
    from shared.config import settings  # deferred for testability

    resolved_dir = Path(source_dir) if source_dir is not None else Path(settings.yaml_spec_dir)

    if not resolved_dir.exists() or not resolved_dir.is_dir():
        logger.warning(
            "YAML spec directory does not exist or is not a directory: %s", resolved_dir
        )
        return []

    results: list[OpenApiMetadata] = []
    for yaml_path in sorted(resolved_dir.rglob("*")):
        if yaml_path.suffix.lower() not in _YAML_EXTENSIONS:
            continue
        metadata = _parse_file(yaml_path)
        if metadata is not None:
            results.append(metadata)

    logger.info(
        "Loaded %d OpenAPI specification(s) from %s", len(results), resolved_dir
    )
    return results


def _parse_file(yaml_path: Path) -> OpenApiMetadata | None:
    """Parse a single YAML file and return its metadata, or ``None`` on failure."""
    try:
        raw_text = yaml_path.read_text(encoding="utf-8")
    except OSError as exc:
        logger.warning("Cannot read file %s: %s", yaml_path, exc)
        return None

    try:
        raw = yaml.load(raw_text, Loader=yaml.CSafeLoader)
    except yaml.YAMLError as exc:
        logger.warning("Invalid YAML in %s: %s", yaml_path, exc)
        return None

    if not isinstance(raw, dict):
        logger.warning("Skipping %s: YAML root is not a mapping.", yaml_path)
        return None

    try:
        metadata_dict = extract_info_metadata(raw, str(yaml_path))
        return OpenApiMetadata(
            spec_file=str(yaml_path),
            **metadata_dict,
        )
    except InfoExtractionError as exc:
        logger.warning("Skipping %s: %s", yaml_path, exc)
        return None

