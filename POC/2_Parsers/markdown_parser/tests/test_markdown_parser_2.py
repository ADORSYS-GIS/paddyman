"""Unit tests for markdown parser.py module."""
import pytest
from pathlib import Path
from markdown_parser.parser import markdown_to_normalized_docs

class TestMarkdownToNormalizedDocs:
    """Test markdown_to_normalized_docs function."""

    def test_file_with_table_extracts_table_metadata(self, tmp_path: Path):
        """Test that tables are extracted and added to source_metadata."""
        # Arrange
        md_file = tmp_path / "table_chunk_001.md"
        content = """# Data Types

| Type | Description |
|------|-------------|
| String | Text data |
| Integer | Numeric data |

Some text after the table.
"""
        md_file.write_text(content, encoding="utf-8")

        metadata = {
            "file_path": str(md_file),
            "source_parser": "markdown_parser",
            "specification": "test_spec",
            "section_file": "table_chunk_001.md",
            "section_name": "table",
            "chunk_index": 1,
            "chunk_count_in_section": 1,
        }

        # Act
        docs = markdown_to_normalized_docs(md_file)

        # Assert
        assert len(docs) == 1
        doc = docs[0]
        assert "tables" in doc.source_metadata
        assert len(doc.source_metadata["tables"]) == 1
        
        table = doc.source_metadata["tables"][0]
        assert table["headers"] == ["Type", "Description"]
        assert len(table["rows"]) == 2
        assert table["rows"][0] == ["String", "Text data"]
        assert table["rows"][1] == ["Integer", "Numeric data"]

    def test_file_with_multiple_tables(self, tmp_path: Path):
        """Test that multiple tables are all extracted."""
        # Arrange
        md_file = tmp_path / "multi_table_chunk_001.md"
        content = """
| Table1 |
|--------|
| Data1  |

Some text.

| Table2 | Col2 |
|--------|------|
| Data2  | Val2 |
"""
        md_file.write_text(content, encoding="utf-8")

        metadata = {
            "file_path": str(md_file),
            "source_parser": "markdown_parser",
            "specification": "test_spec",
            "section_file": "multi_table_chunk_001.md",
            "section_name": "multi_table",
            "chunk_index": 1,
            "chunk_count_in_section": 1,
        }

        # Act
        docs = markdown_to_normalized_docs(md_file)

        # Assert
        assert len(docs) == 1
        doc = docs[0]
        assert "tables" in doc.source_metadata
        assert len(doc.source_metadata["tables"]) == 2
        
        assert doc.source_metadata["tables"][0]["headers"] == ["Table1"]
        assert doc.source_metadata["tables"][1]["headers"] == ["Table2", "Col2"]

    def test_file_without_tables_has_empty_tables_list(self, tmp_path: Path):
        """Test that files without tables have an empty tables list."""
        # Arrange
        md_file = tmp_path / "no_table_chunk_001.md"
        content = "# Just a heading\n\nAnd some text."
        md_file.write_text(content, encoding="utf-8")

        metadata = {
            "file_path": str(md_file),
            "source_parser": "markdown_parser",
            "specification": "test_spec",
            "section_file": "no_table_chunk_001.md",
            "section_name": "no_table",
            "chunk_index": 1,
            "chunk_count_in_section": 1,
        }

        # Act
        docs = markdown_to_normalized_docs(md_file)

        # Assert
        assert len(docs) == 1
        doc = docs[0]
        assert "tables" in doc.source_metadata
        assert doc.source_metadata["tables"] == []

