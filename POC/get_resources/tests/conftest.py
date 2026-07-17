"""Shared pytest fixtures for the Berlin Group downloader tests."""
from __future__ import annotations

from pathlib import Path

import pytest

from berlin_group.models import DownloadLink


@pytest.fixture
def sample_link() -> DownloadLink:
    return DownloadLink(
        url="https://www.berlin-group.org/_files/ugd/c2914b_abc.pdf",
        filename="c2914b_abc.pdf",
        version="1.3.8",
        source_name="NextGenPSD2",
    )


@pytest.fixture
def another_link() -> DownloadLink:
    return DownloadLink(
        url="https://example.com/openfinance_v2.0_spec.pdf",
        filename="openfinance_v2.0_spec.pdf",
        version="2.0",
        source_name="OpenFinance",
    )


@pytest.fixture
def tmp_download_dir(tmp_path: Path) -> Path:
    base = tmp_path / "downloads"
    base.mkdir()
    return base


@pytest.fixture
def sample_row() -> dict:
    """A Tabulator row dict as returned by the JS extractor."""
    return {
        "title": "Implementation Guidelines V1.3.8 20231001.pdf",
        "href": "https://www.berlin-group.org/_files/ugd/c2914b_abc.pdf",
    }

