"""Unit tests for markdown parser.py module."""
import pytest
from pathlib import Path
from markdown_parser.parser import markdown_to_normalized_docs

class TestMarkdownToNormalizedDocs:
    """Test markdown_to_normalized_docs function."""

    def test_file_without_references_has_empty_references(self, tmp_path: Path):
        """Test that files without references have empty reference lists."""
        # Arrange
        md_file = tmp_path / "no_refs_chunk_001.md"
        content = "# Just a heading\n\nAnd some plain text with no references."
        md_file.write_text(content, encoding="utf-8")

        metadata = {
            "file_path": str(md_file),
            "source_parser": "markdown_parser",
            "specification": "test_spec",
            "section_file": "no_refs_chunk_001.md",
            "section_name": "no_refs",
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
        assert refs["citations"] == []

    def test_file_with_both_tables_and_references(self, tmp_path: Path):
        """Test that both tables and references are extracted together."""
        # Arrange
        md_file = tmp_path / "both_chunk_001.md"
        content = """# Specification [PSD2]

| Field | Type |
|-------|------|
| id    | string |

See [Berlin Group](https://berlin-group.org) for details.
"""
        md_file.write_text(content, encoding="utf-8")

        metadata = {
            "file_path": str(md_file),
            "source_parser": "markdown_parser",
            "specification": "test_spec",
            "section_file": "both_chunk_001.md",
            "section_name": "both",
            "chunk_index": 1,
            "chunk_count_in_section": 1,
        }

        # Act
        docs = markdown_to_normalized_docs(md_file)

        # Assert
        assert len(docs) == 1
        doc = docs[0]
        
        # Check tables
        assert "tables" in doc.source_metadata["metadata"]
        assert len(doc.source_metadata["metadata"]["tables"]) == 1
        
        # Check references
        assert "references" in doc.source_metadata["metadata"]
        refs = doc.source_metadata["metadata"]["references"]
        assert len(refs["inline"]) == 1
        assert refs["citations"] == ["PSD2"]


