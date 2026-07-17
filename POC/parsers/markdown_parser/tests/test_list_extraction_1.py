"""Unit tests for markdown parser.py module."""
import pytest
from pathlib import Path
from markdown_parser.parser import markdown_to_normalized_docs

class TestListExtraction:
    """Test list extraction and storage in source_metadata."""

    def test_file_with_bullet_list_extracts_list_metadata(self, tmp_path: Path):
        """Test that a bullet list with 3 items is extracted correctly."""
        # Arrange
        md_file = tmp_path / "bullet_list_chunk_001.md"
        content = """# SCA Approaches

The following SCA approaches are supported:

- Redirect SCA Approach
- OAuth SCA Approach
- Decoupled SCA Approach

Some text after the list.
"""
        md_file.write_text(content, encoding="utf-8")

        metadata = {
            "file_path": str(md_file),
            "source_parser": "markdown_parser",
            "specification": "test_spec",
            "section_file": "bullet_list_chunk_001.md",
            "section_name": "bullet_list",
            "chunk_index": 1,
            "chunk_count_in_section": 1,
        }

        # Act
        docs = markdown_to_normalized_docs(md_file)

        # Assert
        assert len(docs) == 1
        doc = docs[0]
        assert "lists" in doc.source_metadata["metadata"]
        assert len(doc.source_metadata["metadata"]["lists"]) == 1

        list_block = doc.source_metadata["metadata"]["lists"][0]
        assert list_block["ordered"] is False
        assert len(list_block["items"]) == 3
        assert list_block["items"][0] == "Redirect SCA Approach"
        assert list_block["items"][1] == "OAuth SCA Approach"
        assert list_block["items"][2] == "Decoupled SCA Approach"

    def test_file_with_numbered_list_extracts_list_metadata(self, tmp_path: Path):
        """Test that a numbered list with 4 items is extracted correctly."""
        # Arrange
        md_file = tmp_path / "numbered_list_chunk_001.md"
        content = """# Payment Types

The API supports the following payment types:

1. payments
2. bulk-payments
3. periodic-payments
4. standing-orders

Additional content follows.
"""
        md_file.write_text(content, encoding="utf-8")

        metadata = {
            "file_path": str(md_file),
            "source_parser": "markdown_parser",
            "specification": "test_spec",
            "section_file": "numbered_list_chunk_001.md",
            "section_name": "numbered_list",
            "chunk_index": 1,
            "chunk_count_in_section": 1,
        }

        # Act
        docs = markdown_to_normalized_docs(md_file)

        # Assert
        assert len(docs) == 1
        doc = docs[0]
        assert "lists" in doc.source_metadata["metadata"]
        assert len(doc.source_metadata["metadata"]["lists"]) == 1

        list_block = doc.source_metadata["metadata"]["lists"][0]
        assert list_block["ordered"] is True
        assert len(list_block["items"]) == 4
        assert list_block["items"][0] == "payments"
        assert list_block["items"][1] == "bulk-payments"
        assert list_block["items"][2] == "periodic-payments"
        assert list_block["items"][3] == "standing-orders"

