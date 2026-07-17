"""Unit tests for reference URL classifiers."""
import pytest
from markdown_parser.reference_classifiers import (
    is_external_url,
    is_relative_path,
    is_anchor,
    is_cross_document,
)


class TestIsExternalUrl:
    """Test is_external_url function."""

    def test_https_url(self):
        assert is_external_url("https://example.com") is True

    def test_http_url(self):
        assert is_external_url("http://example.com") is True

    def test_ftp_url(self):
        assert is_external_url("ftp://files.example.com") is True

    def test_mailto_link(self):
        assert is_external_url("mailto:test@example.com") is True

    def test_tel_link(self):
        assert is_external_url("tel:+1234567890") is True

    def test_relative_path(self):
        assert is_external_url("../docs/other.md") is False

    def test_anchor(self):
        assert is_external_url("#section") is False

    def test_empty_string(self):
        assert is_external_url("") is False


class TestIsRelativePath:
    """Test is_relative_path function."""

    def test_parent_directory_path(self):
        assert is_relative_path("../docs/other.md") is True

    def test_current_directory_path(self):
        assert is_relative_path("./file.md") is True

    def test_subdirectory_path(self):
        assert is_relative_path("images/logo.png") is True

    def test_external_url(self):
        assert is_relative_path("https://example.com") is False

    def test_anchor(self):
        assert is_relative_path("#section") is False

    def test_absolute_path(self):
        assert is_relative_path("/etc/config") is False

    def test_empty_string(self):
        assert is_relative_path("") is False


class TestIsAnchor:
    """Test is_anchor function."""

    def test_simple_anchor(self):
        assert is_anchor("#section-heading") is True

    def test_anchor_with_numbers(self):
        assert is_anchor("#section-1") is True

    def test_url_with_anchor(self):
        assert is_anchor("https://example.com#section") is False

    def test_relative_path_with_anchor(self):
        assert is_anchor("../docs/other.md#section") is False

    def test_empty_string(self):
        assert is_anchor("") is False

    def test_just_hash(self):
        assert is_anchor("#") is False


class TestIsCrossDocument:
    """Test is_cross_document function."""

    def test_markdown_file(self):
        assert is_cross_document("../docs/other.md") is True

    def test_markdown_file_current_dir(self):
        assert is_cross_document("./README.md") is True

    def test_markdown_file_with_anchor(self):
        assert is_cross_document("./spec.md#section") is True

    def test_markdown_variants(self):
        assert is_cross_document("doc.markdown") is True
        assert is_cross_document("doc.mdown") is True
        assert is_cross_document("doc.mkd") is True

    def test_external_markdown_url(self):
        assert is_cross_document("https://example.com/doc.md") is False

    def test_image_file(self):
        assert is_cross_document("image.png") is False

    def test_anchor_only(self):
        assert is_cross_document("#section") is False

    def test_empty_string(self):
        assert is_cross_document("") is False
