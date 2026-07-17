"""Tests for the downloader module."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, call

import pytest
import requests

from berlin_group.downloader import build_session, download_file
from berlin_group.models import DownloadLink, DownloadResult


class TestBuildSession:
    def test_returns_requests_session(self):
        session = build_session()
        assert isinstance(session, requests.Session)

    def test_has_https_adapter(self):
        session = build_session()
        adapter = session.get_adapter("https://example.com")
        assert adapter is not None

    def test_has_http_adapter(self):
        session = build_session()
        adapter = session.get_adapter("http://example.com")
        assert adapter is not None

    def test_user_agent_header_set(self):
        session = build_session()
        assert "User-Agent" in session.headers
        assert len(session.headers["User-Agent"]) > 0


class TestDownloadFile:
    def test_skips_existing_file(
        self, sample_link: DownloadLink, tmp_download_dir: Path
    ):
        target = sample_link.target_path(tmp_download_dir)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"already here")

        result = download_file(sample_link, base_dir=tmp_download_dir)

        assert result.skipped is True
        assert result.success is True
        assert result.status == "skipped"

    def test_downloads_new_file(
        self, sample_link: DownloadLink, tmp_download_dir: Path
    ):
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.iter_content.return_value = [b"pdf content"]

        mock_session = MagicMock()
        mock_session.get.return_value.__enter__ = MagicMock(return_value=mock_response)
        mock_session.get.return_value = mock_response

        result = download_file(
            sample_link, base_dir=tmp_download_dir, session=mock_session
        )

        assert result.success is True
        assert result.skipped is False
        assert result.status == "success"
        assert sample_link.target_path(tmp_download_dir).exists()

    def test_creates_parent_directories(
        self, sample_link: DownloadLink, tmp_download_dir: Path
    ):
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.iter_content.return_value = [b"content"]

        mock_session = MagicMock()
        mock_session.get.return_value = mock_response

        download_file(sample_link, base_dir=tmp_download_dir, session=mock_session)

        assert sample_link.target_path(tmp_download_dir).parent.is_dir()

    def test_handles_http_error(
        self, sample_link: DownloadLink, tmp_download_dir: Path
    ):
        mock_session = MagicMock()
        mock_session.get.side_effect = requests.HTTPError("404 Not Found")

        result = download_file(
            sample_link, base_dir=tmp_download_dir, session=mock_session
        )

        assert result.success is False
        assert result.error is not None
        assert result.status == "failed"

    def test_cleans_up_partial_file_on_error(
        self, sample_link: DownloadLink, tmp_download_dir: Path
    ):
        mock_session = MagicMock()
        mock_session.get.side_effect = IOError("connection reset")

        download_file(sample_link, base_dir=tmp_download_dir, session=mock_session)

        assert not sample_link.target_path(tmp_download_dir).exists()


class TestDownloadResult:
    def test_status_skipped(self, sample_link: DownloadLink):
        result = DownloadResult(link=sample_link, success=True, skipped=True)
        assert result.status == "skipped"

    def test_status_success(self, sample_link: DownloadLink):
        result = DownloadResult(link=sample_link, success=True)
        assert result.status == "success"

    def test_status_failed(self, sample_link: DownloadLink):
        result = DownloadResult(link=sample_link, success=False)
        assert result.status == "failed"
