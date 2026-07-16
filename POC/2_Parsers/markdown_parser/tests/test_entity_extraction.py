"""Unit tests for markdown entity extraction."""
import pytest
from pathlib import Path
from markdown_parser.entity_orchestrator import extract_entities_and_relationships


class TestEntityExtraction:
    """Test entity extraction from markdown documents."""

    def test_document_entity_extracted(self, tmp_path: Path):
        """Verify Document entity is created for markdown file."""
        md_file = tmp_path / "test.md"
        content = "# Test Document\n\nThis is a test."
        md_file.write_text(content, encoding="utf-8")

        entities, relationships = extract_entities_and_relationships(
            md_file, content, "test"
        )

        # Should have at least a Document entity
        doc_entities = [e for e in entities if e["type"] == "Document"]
        assert len(doc_entities) == 1
        assert doc_entities[0]["name"] == "Test Document"

    def test_section_hierarchy_extracted(self, tmp_path: Path):
        """Verify section hierarchy is captured."""
        md_file = tmp_path / "test.md"
        content = """# Level 1
Some content.

## Level 2
More content.

### Level 3
Even more content.
"""
        md_file.write_text(content, encoding="utf-8")

        entities, relationships = extract_entities_and_relationships(
            md_file, content, "test"
        )

        section_entities = [e for e in entities if e["type"] == "Section"]
        assert len(section_entities) == 3
        assert section_entities[0]["properties"]["level"] == 1
        assert section_entities[1]["properties"]["level"] == 2
        assert section_entities[2]["properties"]["level"] == 3

    def test_table_extraction(self, tmp_path: Path):
        """Verify tables are extracted."""
        md_file = tmp_path / "test.md"
        content = """# Tables

| Column 1 | Column 2 |
|----------|----------|
| Value 1  | Value 2  |
| Value 3  | Value 4  |
"""
        md_file.write_text(content, encoding="utf-8")

        entities, relationships = extract_entities_and_relationships(
            md_file, content, "test"
        )

        table_entities = [e for e in entities if e["type"] == "Table"]
        assert len(table_entities) == 1
        assert table_entities[0]["properties"]["row_count"] == 2
        assert table_entities[0]["properties"]["column_count"] == 2

    def test_list_extraction(self, tmp_path: Path):
        """Verify lists are extracted."""
        md_file = tmp_path / "test.md"
        content = """# Lists

- Item 1
- Item 2
- Item 3

Some text in between.

1. Numbered item 1
2. Numbered item 2
"""
        md_file.write_text(content, encoding="utf-8")

        entities, relationships = extract_entities_and_relationships(
            md_file, content, "test"
        )

        list_entities = [e for e in entities if e["type"] == "List"]
        assert len(list_entities) >= 1  # At least one list
        # Verify we have at least one unordered list
        unordered = [l for l in list_entities if l["properties"]["list_type"] == "unordered"]
        assert len(unordered) >= 1

    def test_relationships_created(self, tmp_path: Path):
        """Verify relationships are created."""
        md_file = tmp_path / "test.md"
        content = """# Main Section

## Subsection

Some text.
"""
        md_file.write_text(content, encoding="utf-8")

        entities, relationships = extract_entities_and_relationships(
            md_file, content, "test"
        )

        # Should have CONTAINS and PARENT_SECTION relationships
        assert len(relationships) > 0
        contains_rels = [r for r in relationships if r["type"] == "CONTAINS"]
        parent_rels = [r for r in relationships if r["type"] == "PARENT_SECTION"]
        assert len(contains_rels) > 0
        assert len(parent_rels) > 0

    def test_codeblock_extraction(self, tmp_path: Path):
        """Verify code blocks are extracted."""
        md_file = tmp_path / "test.md"
        content = """# Code Example

```python
def hello():
    print("Hello, world!")
```
"""
        md_file.write_text(content, encoding="utf-8")

        entities, relationships = extract_entities_and_relationships(
            md_file, content, "test"
        )

        codeblock_entities = [e for e in entities if e["type"] == "CodeBlock"]
        assert len(codeblock_entities) == 1
        assert codeblock_entities[0]["properties"]["language"] == "python"

    def test_reference_extraction(self, tmp_path: Path):
        """Verify references are extracted."""
        md_file = tmp_path / "test.md"
        content = """# References

[Link text](https://example.com)

Some text with ![Image alt](image.png) embedded.
"""
        md_file.write_text(content, encoding="utf-8")

        entities, relationships = extract_entities_and_relationships(
            md_file, content, "test"
        )

        ref_entities = [e for e in entities if e["type"] == "Reference"]
        # Should have at least 2 references (link and image)
        assert len(ref_entities) >= 2
        image_refs = [r for r in ref_entities if r["properties"]["ref_type"] == "image"]
        assert len(image_refs) >= 1
