"""Tests for the models module."""
from __future__ import annotations

from pathlib import Path

import pytest

from berlin_group.models import DownloadLink, DownloadResult


class TestDownloadLinkTargetPath:
    def test_path_structure(self, sample_link: DownloadLink):
        base = Path("/downloads")
        path = sample_link.target_path(base)
        assert path == base / "NextGenPSD2" / "1.3.8" / "c2914b_abc.pdf"

    def test_sanitises_version_slashes(self):
        link = DownloadLink(
            url="http://x.com/f.pdf",
            filename="f.pdf",
            version="1.0/rc1",
            source_name="Src",
        )
        path = link.target_path(Path("/base"))
        assert "/" not in path.parts[-2]

    def test_unknown_version_directory(self):
        link = DownloadLink(
            url="http://x.com/f.pdf",
            filename="f.pdf",
            version="unknown",
            source_name="Src",
        )
        path = link.target_path(Path("/base"))
        assert path.parent.name == "unknown"
