"""Unit tests for markdown parser.py module."""
import pytest
from pathlib import Path
from markdown_parser.parser import markdown_to_normalized_docs

class TestMarkdownToNormalizedDocs:
    """Test markdown_to_normalized_docs function."""

    def test_standard_markdown_file_parsing(self, tmp_path: Path):
        """Test parsing a complete specification markdown file."""
        # Arrange
        md_file = tmp_path / "ais_for_deposited_cheques_1_0_clean.md"
        md_file.write_text("# Introduction\n\nThis is content.", encoding="utf-8")

        # Act
        docs = markdown_to_normalized_docs(md_file)

        # Assert
        assert len(docs) == 1
        doc = docs[0]
        assert doc.document_id == "ais_for_deposited_cheques_1_0"
        assert doc.text == "# Introduction\n\nThis is content."
        assert doc.source_parser == "markdown_parser"
        assert "tables" in doc.source_metadata
        assert doc.source_metadata["tables"] == []  # No tables in this content
        assert "references" in doc.source_metadata
        assert doc.source_metadata["references"]["inline"] == []  # No references
        assert doc.source_metadata["references"]["definitions"] == []
        assert doc.source_metadata["references"]["citations"] == []
        assert doc.source_metadata["specification"] == "ais_for_deposited_cheques_1_0"
        assert doc.provenance["stage"] == "markdown_parser"

    def test_file_without_clean_suffix(self, tmp_path: Path):
        """Test parsing a file without _clean suffix."""
        # Arrange
        md_file = tmp_path / "specification.md"
        md_file.write_text("Specification content", encoding="utf-8")

        # Act
        docs = markdown_to_normalized_docs(md_file)

        # Assert
        assert len(docs) == 1
        doc = docs[0]
        assert doc.document_id == "specification"
        assert doc.text == "Specification content"
        assert doc.source_metadata["specification"] == "specification"

    def test_empty_file(self, tmp_path: Path):
        """Test parsing an empty markdown file."""
        # Arrange
        md_file = tmp_path / "empty_clean.md"
        md_file.write_text("", encoding="utf-8")

        # Act
        docs = markdown_to_normalized_docs(md_file)

        # Assert
        assert len(docs) == 1
        doc = docs[0]
        assert doc.text == ""
        assert doc.document_id == "empty"

    def test_missing_file_produces_empty_text(self, tmp_path: Path):
        """Test handling of missing file."""
        # Arrange
        md_file = tmp_path / "nonexistent.md"

        metadata = {
            "file_path": str(md_file),
            "source_parser": "markdown_parser",
            "specification": "test_spec",
            "section_file": "nonexistent.md",
            "section_name": "nonexistent",
            "chunk_index": 0,
            "chunk_count_in_section": 1,
        }

        # Act
        docs = markdown_to_normalized_docs(md_file)

        # Assert
        assert len(docs) == 1
        doc = docs[0]
        assert doc.text == ""  # Should produce empty text, not raise exception

    def test_unicode_content(self, tmp_path: Path):
        """Test parsing file with unicode characters."""
        # Arrange
        md_file = tmp_path / "unicode_chunk_001.md"
        content = "# Überschrift\n\n€ § ñ 中文"
        md_file.write_text(content, encoding="utf-8")

        metadata = {
            "file_path": str(md_file),
            "source_parser": "markdown_parser",
            "specification": "unicode_spec",
            "section_file": "unicode_chunk_001.md",
            "section_name": "unicode",
            "chunk_index": 1,
            "chunk_count_in_section": 1,
        }

        # Act
        docs = markdown_to_normalized_docs(md_file)

        # Assert
        assert len(docs) == 1
        doc = docs[0]
        assert doc.text == content

