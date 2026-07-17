"""Unit tests for markdown reference extraction."""
import pytest
from markdown_parser.structure import _extract_links


class TestExtractLinks:
    """Test _extract_links function."""

    def test_inline_links(self):
        """Test extraction of inline markdown links."""
        text = "Visit [Berlin Group](https://www.berlin-group.org) for more info."
        result = _extract_links(text)
        
        assert len(result["inline"]) == 1
        assert result["inline"][0]["text"] == "Berlin Group"
        assert result["inline"][0]["url"] == "https://www.berlin-group.org"
        assert result["definitions"] == []
        assert result["citations"] == []

    def test_multiple_inline_links(self):
        """Test extraction of multiple inline links."""
        text = "[Link1](url1) some text [Link2](url2) more text [Link3](url3)"
        result = _extract_links(text)
        
        assert len(result["inline"]) == 3
        assert result["inline"][0]["text"] == "Link1"
        assert result["inline"][0]["url"] == "url1"
        assert result["inline"][1]["text"] == "Link2"
        assert result["inline"][2]["text"] == "Link3"

    def test_reference_definitions(self):
        """Test extraction of reference-style link definitions."""
        text = """
[XS2A-OR]: https://berlin-group.org/xs2a-implementation-guidelines
[HAL]: https://stateless.co/hal_specification.html
"""
        result = _extract_links(text)
        
        assert len(result["definitions"]) == 2
        assert result["definitions"][0]["id"] == "XS2A-OR"
        assert result["definitions"][0]["url"] == "https://berlin-group.org/xs2a-implementation-guidelines"
        assert result["definitions"][1]["id"] == "HAL"
        assert result["definitions"][1]["url"] == "https://stateless.co/hal_specification.html"
        assert result["inline"] == []
        # Reference IDs that match citation pattern are also captured as citations
        assert result["citations"] == ["HAL", "XS2A-OR"]

    def test_normative_citations(self):
        """Test extraction of normative citations."""
        text = "This follows [RFC6749] and [PSD2] standards."
        result = _extract_links(text)
        
        assert len(result["citations"]) == 2
        assert result["citations"] == ["PSD2", "RFC6749"]  # Sorted
        assert result["inline"] == []
        assert result["definitions"] == []

    def test_citations_sorted_and_deduplicated(self):
        """Test that citations are sorted and deduplicated."""
        text = "See [RFC6749], [PSD2], [XS2A-OR], and [RFC6749] again."
        result = _extract_links(text)
        
        assert result["citations"] == ["PSD2", "RFC6749", "XS2A-OR"]  # Sorted, no duplicates

    def test_citations_with_hyphens_and_numbers(self):
        """Test citations with hyphens and numbers."""
        text = "[XS2A-OR], [ISO20022], [SEPA-1], [PSD2-V2]"
        result = _extract_links(text)
        
        assert result["citations"] == ["ISO20022", "PSD2-V2", "SEPA-1", "XS2A-OR"]

    def test_mixed_links_definitions_citations(self):
        """Test text with all three types of references."""
        text = """
# Specification

See [Berlin Group](https://berlin-group.org) for details.

This implements [RFC6749] and [PSD2].

[XS2A-OR]: https://berlin-group.org/xs2a
[HAL]: https://stateless.co/hal_specification.html

Reference [RFC6749] again for clarity.
"""
        result = _extract_links(text)
        
        assert len(result["inline"]) == 1
        assert result["inline"][0]["text"] == "Berlin Group"
        
        assert len(result["definitions"]) == 2
        assert result["definitions"][0]["id"] == "XS2A-OR"
        assert result["definitions"][1]["id"] == "HAL"
        
        # All citations including those in reference definitions
        assert result["citations"] == ["HAL", "PSD2", "RFC6749", "XS2A-OR"]  # Sorted

    def test_no_references(self):
        """Test text with no references."""
        text = "Just plain text with no links, citations, or references."
        result = _extract_links(text)
        
        assert result["inline"] == []
        assert result["definitions"] == []
        assert result["citations"] == []

    def test_empty_text(self):
        """Test empty text."""
        result = _extract_links("")
        
        assert result["inline"] == []
        assert result["definitions"] == []
        assert result["citations"] == []

    def test_lowercase_citation_not_matched(self):
        """Test that lowercase citations are not matched (to avoid false positives)."""
        text = "This is [json] data and [regex] pattern."
        result = _extract_links(text)
        
        assert result["citations"] == []  # Lowercase not matched

    def test_citation_too_long_not_matched(self):
        """Test that very long citations are not matched."""
        text = "[THISISAVERYLONGCITATIONKEYTHATEXCEEDSTHELIMIT]"
        result = _extract_links(text)
        
        # Should not match because it exceeds 30 characters
        assert result["citations"] == []

    def test_citation_starting_with_number_not_matched(self):
        """Test that citations starting with numbers are not matched."""
        text = "[123ABC] and [9XYZ]"
        result = _extract_links(text)
        
        assert result["citations"] == []  # Must start with uppercase letter

    def test_valid_citation_edge_cases(self):
        """Test valid citations at boundaries."""
        text = "[AB] [ABC] [X-Y] [ISO9001]"
        result = _extract_links(text)
        
        # Citation pattern requires at least 2 characters: [A-Z][A-Z0-9\-]{1,30}
        # Single letter [A] won't match
        assert "AB" in result["citations"]
        assert "ABC" in result["citations"]
        assert "ISO9001" in result["citations"]
        assert "X-Y" in result["citations"]
        assert len(result["citations"]) == 4

    def test_inline_link_with_special_characters_in_text(self):
        """Test inline links with special characters in link text."""
        text = "[Link with spaces & special!](http://example.com)"
        result = _extract_links(text)
        
        assert len(result["inline"]) == 1
        assert result["inline"][0]["text"] == "Link with spaces & special!"

    def test_reference_definition_with_query_params(self):
        """Test reference definition with complex URL."""
        text = "[API]: https://api.example.com/v1/resource?param=value&other=123"
        result = _extract_links(text)
        
        assert len(result["definitions"]) == 1
        assert result["definitions"][0]["id"] == "API"
        assert result["definitions"][0]["url"] == "https://api.example.com/v1/resource?param=value&other=123"

    def test_deterministic_ordering(self):
        """Test that multiple runs produce the same order."""
        text = "[ZEBRA] [ALPHA] [BETA] [GAMMA]"
        
        result1 = _extract_links(text)
        result2 = _extract_links(text)
        result3 = _extract_links(text)
        
        assert result1["citations"] == result2["citations"] == result3["citations"]
        assert result1["citations"] == ["ALPHA", "BETA", "GAMMA", "ZEBRA"]
