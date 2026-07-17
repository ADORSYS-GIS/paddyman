"""Unit tests for markdown parser.py module."""
import pytest
from pathlib import Path
from markdown_parser.parser import markdown_to_normalized_docs

class TestListExtraction:
    """Test list extraction and storage in source_metadata."""

    def test_file_with_both_bullet_and_numbered_lists(self, tmp_path: Path):
        """Test that both bullet and numbered lists are extracted."""
        # Arrange
        md_file = tmp_path / "mixed_lists_chunk_001.md"
        content = """# API Features

## Authentication Methods

- Basic Authentication
- OAuth 2.0
- API Key

## Supported Versions

1. Version 1.0
2. Version 2.0
3. Version 3.0
"""
        md_file.write_text(content, encoding="utf-8")

        metadata = {
            "file_path": str(md_file),
            "source_parser": "markdown_parser",
            "specification": "test_spec",
            "section_file": "mixed_lists_chunk_001.md",
            "section_name": "mixed_lists",
            "chunk_index": 1,
            "chunk_count_in_section": 1,
        }

        # Act
        docs = markdown_to_normalized_docs(md_file)

        # Assert
        assert len(docs) == 1
        doc = docs[0]
        assert "lists" in doc.source_metadata["metadata"]
        assert len(doc.source_metadata["metadata"]["lists"]) == 2
        
        # First list should be bullet list
        bullet_list = doc.source_metadata["metadata"]["lists"][0]
        assert bullet_list["ordered"] is False
        assert len(bullet_list["items"]) == 3
        assert bullet_list["items"][0] == "Basic Authentication"
        assert bullet_list["items"][1] == "OAuth 2.0"
        assert bullet_list["items"][2] == "API Key"
        
        # Second list should be numbered list
        numbered_list = doc.source_metadata["metadata"]["lists"][1]
        assert numbered_list["ordered"] is True
        assert len(numbered_list["items"]) == 3
        assert numbered_list["items"][0] == "Version 1.0"
        assert numbered_list["items"][1] == "Version 2.0"
        assert numbered_list["items"][2] == "Version 3.0"

    def test_file_without_lists_has_empty_lists_array(self, tmp_path: Path):
        """Test that files without lists have an empty lists array."""
        # Arrange
        md_file = tmp_path / "no_lists_chunk_001.md"
        content = """# Introduction

This is a simple paragraph without any lists.

Just regular text content.
"""
        md_file.write_text(content, encoding="utf-8")

        metadata = {
            "file_path": str(md_file),
            "source_parser": "markdown_parser",
            "specification": "test_spec",
            "section_file": "no_lists_chunk_001.md",
            "section_name": "no_lists",
            "chunk_index": 1,
            "chunk_count_in_section": 1,
        }

        # Act
        docs = markdown_to_normalized_docs(md_file)

        # Assert
        assert len(docs) == 1
        doc = docs[0]
        assert "lists" in doc.source_metadata["metadata"]
        assert doc.source_metadata["metadata"]["lists"] == []

    def test_empty_file_has_empty_lists_array(self, tmp_path: Path):
        """Test that empty files have an empty lists array."""
        # Arrange
        md_file = tmp_path / "empty_chunk_001.md"
        md_file.write_text("", encoding="utf-8")

        metadata = {
            "file_path": str(md_file),
            "source_parser": "markdown_parser",
            "specification": "test_spec",
            "section_file": "empty_chunk_001.md",
            "section_name": "empty",
            "chunk_index": 1,
            "chunk_count_in_section": 1,
        }

        # Act
        docs = markdown_to_normalized_docs(md_file)

        # Assert
        assert len(docs) == 1
        doc = docs[0]
        assert "lists" in doc.source_metadata["metadata"]
        assert doc.source_metadata["metadata"]["lists"] == []

