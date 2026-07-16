"""Shared configuration dataclasses used across all downloader services.

These are the canonical definitions; per-downloader config.py files
re-export them for backward compatibility with existing service imports.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SourceConfig:
    """A single PDF documentation source to scrape and download from."""

    name: str
    url: str
    title_field: str = "Document title and Version"
    use_title_as_filename: bool = False
    trailing_version: bool = False
    version_major: int | None = None
    #: Set ``enabled=False`` to exclude from the download run without removing.
    enabled: bool = True


@dataclass(frozen=True)
class RepoConfig:
    """A single Git repository to clone."""

    #: Provider-relative path, e.g. ``"group/subgroup/project"``.
    path: str
    #: Sub-directory name created under the destination directory.
    local_name: str
    #: Set ``enabled=False`` to skip this repository without removing it.
    enabled: bool = True
