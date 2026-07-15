"""Test fixtures shared across the spaCy extractor test suite."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Ensure POC/ is importable so ``shared`` resolves.
_POC_ROOT = str(Path(__file__).resolve().parents[4])
if _POC_ROOT not in sys.path:
    sys.path.insert(0, _POC_ROOT)

from shared.models import SourceMetadata, SourceType


@pytest.fixture()
def basic_source() -> SourceMetadata:
    """Minimal SourceMetadata with no version information."""
    return SourceMetadata(
        source_id="test-source",
        source_type=SourceType.DOCUMENT,
        location="/docs/spec.md",
        metadata={},
    )


@pytest.fixture()
def versioned_source() -> SourceMetadata:
    """SourceMetadata with explicit version in metadata."""
    return SourceMetadata(
        source_id="aspsp-xs2a",
        source_type=SourceType.DOCUMENT,
        location="/repos/aspsp-xs2a/v2/consent.md",
        metadata={
            "repository": "aspsp-xs2a",
            "module": "consent",
            "file_path": "/repos/aspsp-xs2a/v2/consent.md",
            "document": "consent.md",
            "version": "2",
        },
    )


@pytest.fixture()
def path_versioned_source() -> SourceMetadata:
    """SourceMetadata with version derivable from file_path."""
    return SourceMetadata(
        source_id="berlin-group",
        source_type=SourceType.DOCUMENT,
        location="/specs/nextgenpsd2_1_3/api.yaml",
        metadata={
            "repository": "berlin-group",
            "file_path": "/specs/nextgenpsd2_1_3/api.yaml",
            "module": "nextgenpsd2_1_3",
        },
    )


@pytest.fixture()
def no_meta_source() -> SourceMetadata:
    """SourceMetadata with no version anywhere — version comes from content only."""
    return SourceMetadata(
        source_id="raw-doc",
        source_type=SourceType.DOCUMENT,
        location="/docs/raw.md",
        metadata={
            "repository": "docs-repo",
            "file_path": "/docs/raw.md",
        },
    )
