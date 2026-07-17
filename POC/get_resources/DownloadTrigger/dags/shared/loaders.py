"""Parse JSON-encoded source/repo lists into typed configuration objects.

Called by per-downloader config.py files.
Never reads ``os.environ`` directly — all raw strings are supplied by the
per-downloader config modules, which source values from ``poc_shared.config.settings``.

The generic JSON-list parsing logic lives in ``poc_shared.config.loader``
(``POC/shared/config/loader.py``) and is re-used here to avoid duplication.
"""
from __future__ import annotations

import logging
from typing import Any

from poc_shared.config.loader import ConfigurationError, parse_json_list as _parse_json_list  # noqa: F401
from shared.models import RepoConfig, SourceConfig

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Public loaders
# ---------------------------------------------------------------------------


def load_pdf_sources(raw: str) -> list[SourceConfig]:
    """Build :class:`SourceConfig` objects from the ``PDF_SOURCES`` JSON string."""
    entries = _parse_json_list(raw, "PDF_SOURCES")
    sources: list[SourceConfig] = []
    for i, entry in enumerate(entries):
        if "name" not in entry or "url" not in entry:
            raise ValueError(
                f"PDF_SOURCES[{i}] is missing required field 'name' or 'url': {entry}"
            )
        sources.append(
            SourceConfig(
                name=entry["name"],
                url=entry["url"],
                title_field=entry.get("title_field", "Document title and Version"),
                use_title_as_filename=bool(entry.get("use_title_as_filename", False)),
                trailing_version=bool(entry.get("trailing_version", False)),
                version_major=entry.get("version_major"),
                enabled=bool(entry.get("enabled", True)),
            )
        )
    return sources


def load_repos(raw: str, var_name: str) -> list[RepoConfig]:
    """Build :class:`RepoConfig` objects from a JSON string named *var_name*."""
    entries = _parse_json_list(raw, var_name)
    repos: list[RepoConfig] = []
    for i, entry in enumerate(entries):
        if "path" not in entry or "local_name" not in entry:
            raise ValueError(
                f"{var_name}[{i}] is missing required field 'path' or 'local_name': "
                f"{entry}"
            )
        repos.append(
            RepoConfig(
                path=entry["path"],
                local_name=entry["local_name"],
                enabled=bool(entry.get("enabled", True)),
            )
        )
    return repos
