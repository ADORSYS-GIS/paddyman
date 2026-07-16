"""Tests for the Tabulator-based scraper module."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from berlin_group.models import DownloadLink
from berlin_group.scraper import _DEFAULT_VERSION, _extract_version, _row_to_link, scrape_source


class TestExtractVersion:
    def test_version_with_v_prefix(self):
        assert _extract_version("Data Dictionary V2.2.6 20250731.pdf") == "2.2.6"

    def test_version_lowercase_v(self):
        assert _extract_version("Framework v1.3.pdf") == "1.3"

    def test_version_three_segments(self):
        assert _extract_version("XS2A Implementation Guidelines V1.3.12.pdf") == "1.3.12"

    def test_version_two_segments(self):
        assert _extract_version("Spec V2.0 final.pdf") == "2.0"

    def test_no_version_returns_default(self):
        assert _extract_version("Document without version.pdf") == _DEFAULT_VERSION

    def test_empty_string_returns_default(self):
        assert _extract_version("") == _DEFAULT_VERSION

    def test_version_at_end_of_title(self):
        assert _extract_version("OpenFinance API V2.2") == "2.2"


class TestRowToLink:
    def test_builds_correct_download_link(self, sample_row: dict):
        link = _row_to_link(sample_row, "NextGenPSD2")
        assert link is not None
        assert link.version == "1.3.8"
        assert link.source_name == "NextGenPSD2"
        assert link.filename == "c2914b_abc.pdf"
        assert link.url == sample_row["href"]

    def test_returns_none_when_href_empty(self):
        assert _row_to_link({"title": "Doc V1.0.pdf", "href": ""}, "Src") is None

    def test_returns_none_when_title_empty(self):
        assert _row_to_link({"title": "", "href": "https://x.com/f.pdf"}, "Src") is None

    def test_version_from_title(self):
        row = {"title": "Data Dictionary V2.2.6 20250731.pdf",
               "href": "https://example.com/dict.pdf"}
        link = _row_to_link(row, "OpenFinance")
        assert link is not None
        assert link.version == "2.2.6"

    def test_filename_from_url_path(self):
        row = {"title": "Doc V1.0.pdf", "href": "https://example.com/subdir/myfile.pdf"}
        link = _row_to_link(row, "Src")
        assert link is not None
        assert link.filename == "myfile.pdf"


class TestScrapeSource:
    def test_returns_list_of_download_links(self):
        fake_rows = [
            {"title": "Guidelines V1.3.8.pdf",
             "href": "https://example.com/guidelines.pdf"},
            {"title": "OpenAPI V1.3.8.yaml",
             "href": "https://example.com/openapi.yaml"},
        ]
        with patch("berlin_group.scraper.asyncio.run", return_value=fake_rows):
            with patch("berlin_group.scraper._scrape_async", new=AsyncMock(return_value=[
                DownloadLink(url=r["href"], filename="f.pdf",
                             version="1.3.8", source_name="NextGenPSD2")
                for r in fake_rows
            ])):
                with patch("berlin_group.scraper.asyncio.run") as mock_run:
                    mock_run.return_value = [
                        DownloadLink(url=r["href"], filename="f.pdf",
                                     version="1.3.8", source_name="NextGenPSD2")
                        for r in fake_rows
                    ]
                    result = scrape_source("https://example.com", "NextGenPSD2")
        assert isinstance(result, list)

