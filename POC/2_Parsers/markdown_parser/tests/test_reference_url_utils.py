"""Unit tests for reference URL utilities."""
import pytest
from markdown_parser.reference_url_utils import (
    extract_target_document,
    extract_anchor_from_url,
)


class TestExtractTargetDocument:
    """Test extract_target_document function."""

    def test_simple_markdown_file(self):
        assert extract_target_document("../docs/other.md") == "../docs/other.md"

    def test_markdown_file_with_anchor(self):
        assert extract_target_document("./spec.md#section") == "./spec.md"

    def test_external_url(self):
        assert extract_target_document("https://example.com") is None

    def test_image_file(self):
        assert extract_target_document("image.png") is None

    def test_anchor_only(self):
        assert extract_target_document("#section") is None


class TestExtractAnchorFromUrl:
    """Test extract_anchor_from_url function."""

    def test_simple_anchor(self):
        assert extract_anchor_from_url("#section-heading") == "section-heading"

    def test_file_with_anchor(self):
        assert extract_anchor_from_url("./doc.md#intro") == "intro"

    def test_url_with_anchor(self):
        assert extract_anchor_from_url("https://example.com#faq") == "faq"

    def test_no_anchor(self):
        assert extract_anchor_from_url("https://example.com") is None

    def test_empty_anchor(self):
        assert extract_anchor_from_url("file.md#") is None

    def test_multiple_hashes(self):
        # Should only split on first #
        assert extract_anchor_from_url("doc.md#section#subsection") == "section#subsection"
