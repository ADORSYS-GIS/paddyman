"""Unit tests for enhanced reference extraction features."""
import pytest
from markdown_parser.reference_link_extractors import (
    extract_inline_links,
    extract_reference_definitions,
)
from markdown_parser.reference_image_extractors import extract_images
from markdown_parser.reference_advanced_extractors import (
    extract_autolinks,
    extract_footnotes,
)


class TestInlineLinksTitleExtraction:
    """Test title attribute extraction for inline links."""

    def test_link_with_title(self):
        text = '[Example](https://example.com "Example Site")'
        links = extract_inline_links(text, "test.md")
        assert len(links) == 1
        assert links[0]["properties"]["title"] == "Example Site"

    def test_link_without_title(self):
        text = "[Example](https://example.com)"
        links = extract_inline_links(text, "test.md")
        assert len(links) == 1
        assert "title" not in links[0]["properties"]


class TestInlineLinksClassification:
    """Test URL classification for inline links."""

    def test_external_link(self):
        text = "[Example](https://example.com)"
        links = extract_inline_links(text, "test.md")
        assert links[0]["properties"]["is_external"] is True
        assert links[0]["properties"]["is_relative"] is False
        assert links[0]["properties"]["is_anchor"] is False

    def test_relative_link(self):
        text = "[Docs](../docs/readme.md)"
        links = extract_inline_links(text, "test.md")
        assert links[0]["properties"]["is_external"] is False
        assert links[0]["properties"]["is_relative"] is True
        assert links[0]["properties"]["is_anchor"] is False

    def test_anchor_link(self):
        text = "[Section](#heading)"
        links = extract_inline_links(text, "test.md")
        assert links[0]["properties"]["is_external"] is False
        assert links[0]["properties"]["is_relative"] is False
        assert links[0]["properties"]["is_anchor"] is True

    def test_cross_document_link(self):
        text = "[Other](./other.md)"
        links = extract_inline_links(text, "test.md")
        assert links[0]["properties"]["target_document"] == "./other.md"


class TestImageExtraction:
    """Test image reference extraction."""

    def test_image_with_alt_text(self):
        text = "![Logo](logo.png)"
        images = extract_images(text, "test.md")
        assert len(images) == 1
        assert images[0]["properties"]["alt_text"] == "Logo"
        assert images[0]["name"] == "Logo"

    def test_image_without_alt_text(self):
        text = "![](image.png)"
        images = extract_images(text, "test.md")
        assert len(images) == 1
        assert images[0]["properties"]["alt_text"] == ""
        assert images[0]["name"] == "Image"

    def test_image_with_title(self):
        text = '![Logo](logo.png "Company Logo")'
        images = extract_images(text, "test.md")
        assert len(images) == 1
        assert images[0]["properties"]["title"] == "Company Logo"

    def test_image_classification(self):
        text = "![External](https://example.com/image.png)"
        images = extract_images(text, "test.md")
        assert images[0]["properties"]["is_external"] is True

        text2 = "![Local](./images/logo.png)"
        images2 = extract_images(text2, "test.md")
        assert images2[0]["properties"]["is_relative"] is True


class TestAutolinks:
    """Test autolink extraction."""

    def test_https_autolink(self):
        text = "Visit <https://example.com> for more."
        autolinks = extract_autolinks(text, "test.md")
        assert len(autolinks) == 1
        assert autolinks[0]["properties"]["target_url"] == "https://example.com"
        assert autolinks[0]["properties"]["ref_type"] == "autolink"

    def test_mailto_autolink(self):
        text = "Contact <mailto:test@example.com>"
        autolinks = extract_autolinks(text, "test.md")
        assert len(autolinks) == 1
        assert autolinks[0]["properties"]["target_url"] == "mailto:test@example.com"

    def test_multiple_autolinks(self):
        text = "<https://example.com> and <ftp://files.example.com>"
        autolinks = extract_autolinks(text, "test.md")
        assert len(autolinks) == 2


class TestFootnotes:
    """Test footnote extraction."""

    def test_footnote_reference(self):
        text = """
This has a footnote[^1].

[^1]: Footnote content here.
"""
        footnotes = extract_footnotes(text, "test.md")
        assert len(footnotes) == 1
        assert footnotes[0]["properties"]["footnote_label"] == "1"
        assert footnotes[0]["properties"]["footnote_content"] == "Footnote content here."

    def test_footnote_without_definition(self):
        text = "This has a footnote[^1]."
        footnotes = extract_footnotes(text, "test.md")
        assert len(footnotes) == 1
        assert "footnote_content" not in footnotes[0]["properties"]

    def test_multiple_footnotes(self):
        text = """
First[^1] and second[^2].

[^1]: First note.
[^2]: Second note.
"""
        footnotes = extract_footnotes(text, "test.md")
        assert len(footnotes) == 2
        assert footnotes[0]["properties"]["footnote_label"] == "1"
        assert footnotes[1]["properties"]["footnote_label"] == "2"

    def test_named_footnote(self):
        text = """
Custom label[^note].

[^note]: Custom footnote.
"""
        footnotes = extract_footnotes(text, "test.md")
        assert len(footnotes) == 1
        assert footnotes[0]["properties"]["footnote_label"] == "note"


class TestReferenceDefinitions:
    """Test reference definition extraction."""

    def test_definition_with_title(self):
        text = '[ref]: https://example.com "Example"'
        defs = extract_reference_definitions(text, "test.md")
        assert len(defs) == 1
        assert defs[0]["properties"]["title"] == "Example"

    def test_definition_classification(self):
        text = "[ref]: ../docs/other.md"
        defs = extract_reference_definitions(text, "test.md")
        assert defs[0]["properties"]["is_relative"] is True
        assert defs[0]["properties"]["target_document"] == "../docs/other.md"
