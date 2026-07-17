"""Unit tests for markdown parser.py module."""
import pytest
from pathlib import Path
from markdown_parser.parser import markdown_to_normalized_docs

class TestMarkdownToNormalizedDocs:
    """Test markdown_to_normalized_docs function."""

    def test_file_with_references_extracts_references_metadata(self, tmp_path: Path):
        """Test that references are extracted and added to source_metadata."""
        # Arrange
        md_file = tmp_path / "references_chunk_001.md"
        content = """# Specification

This implements [RFC6749] and [PSD2] standards.

Visit [Berlin Group](https://www.berlin-group.org) for more information.

[XS2A-OR]: https://berlin-group.org/xs2a-implementation-guidelines
"""
        md_file.write_text(content, encoding="utf-8")

        metadata = {
            "file_path": str(md_file),
            "source_parser": "markdown_parser",
            "specification": "test_spec",
            "section_file": "references_chunk_001.md",
            "section_name": "references",
            "chunk_index": 1,
            "chunk_count_in_section": 1,
        }

        # Act
        docs = markdown_to_normalized_docs(md_file)

        # Assert
        assert len(docs) == 1
        doc = docs[0]
        assert "references" in doc.source_metadata["metadata"]

        refs = doc.source_metadata["metadata"]["references"]
        assert "inline" in refs
        assert "definitions" in refs
        assert "citations" in refs
        
        # Check inline links
        assert len(refs["inline"]) == 1
        assert refs["inline"][0]["text"] == "Berlin Group"
        assert refs["inline"][0]["url"] == "https://www.berlin-group.org"
        
        # Check reference definitions
        assert len(refs["definitions"]) == 1
        assert refs["definitions"][0]["id"] == "XS2A-OR"
        assert refs["definitions"][0]["url"] == "https://berlin-group.org/xs2a-implementation-guidelines"
        
        # Check citations (should be sorted, includes reference definition IDs that match pattern)
        assert refs["citations"] == ["PSD2", "RFC6749", "XS2A-OR"]

    def test_file_with_only_citations(self, tmp_path: Path):
        """Test file with only citations, no inline links or definitions."""
        # Arrange
        md_file = tmp_path / "citations_chunk_001.md"
        content = "Follows [RFC6749], [PSD2], and [XS2A-OR] standards."
        md_file.write_text(content, encoding="utf-8")

        metadata = {
            "file_path": str(md_file),
            "source_parser": "markdown_parser",
            "specification": "test_spec",
            "section_file": "citations_chunk_001.md",
            "section_name": "citations",
            "chunk_index": 1,
            "chunk_count_in_section": 1,
        }

        # Act
        docs = markdown_to_normalized_docs(md_file)

        # Assert
        assert len(docs) == 1
        doc = docs[0]
        assert "references" in doc.source_metadata["metadata"]

        refs = doc.source_metadata["metadata"]["references"]
        assert refs["inline"] == []
        assert refs["definitions"] == []
        assert refs["citations"] == ["PSD2", "RFC6749", "XS2A-OR"]  # Sorted

    def test_file_with_duplicate_citations_are_deduplicated(self, tmp_path: Path):
        """Test that duplicate citations appear only once."""
        # Arrange
        md_file = tmp_path / "duplicates_chunk_001.md"
        content = "See [RFC6749] and [PSD2]. Later, [RFC6749] is mentioned again."
        md_file.write_text(content, encoding="utf-8")

        metadata = {
            "file_path": str(md_file),
            "source_parser": "markdown_parser",
            "specification": "test_spec",
            "section_file": "duplicates_chunk_001.md",
            "section_name": "duplicates",
            "chunk_index": 1,
            "chunk_count_in_section": 1,
        }

        # Act
        docs = markdown_to_normalized_docs(md_file)

        # Assert
        assert len(docs) == 1
        doc = docs[0]
        refs = doc.source_metadata["metadata"]["references"]
        assert refs["citations"] == ["PSD2", "RFC6749"]  # Deduplicated

