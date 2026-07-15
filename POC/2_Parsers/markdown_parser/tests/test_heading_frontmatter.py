"""Tests for heading and frontmatter extraction.

Tests verify that:
- Headings are extracted as entities with correct properties
- Frontmatter is extracted as entities when present
- TITLED_BY relationships link sections to headings
- NEXT_HEADING relationships preserve document order
- HAS_FRONTMATTER relationships link documents to frontmatter
"""
import pytest

from markdown_parser.heading_entity_builder import (
    create_heading_entities,
    _get_heading_level,
    _generate_slug,
)
from markdown_parser.frontmatter_entity_builder import create_frontmatter_entity
from markdown_parser.heading_relationship_builder import (
    create_heading_relationships,
    _create_titled_by_relationships,
    _create_next_heading_relationships,
    _create_frontmatter_relationship,
)


class TestHeadingExtraction:
    """Test heading entity extraction."""

    def test_extract_heading_entities(self):
        """Verify headings are extracted as entities."""
        text = """# Title
## Section 1
### Subsection 1.1
## Section 2
"""
        headings = create_heading_entities(text, "test.md")

        assert len(headings) == 4
        assert headings[0]["type"] == "Heading"
        assert headings[0]["properties"]["level"] == 1
        assert headings[1]["properties"]["level"] == 2
        assert headings[2]["properties"]["level"] == 3
        assert headings[3]["properties"]["level"] == 2

    def test_heading_text_stripped(self):
        """Verify heading text has no markdown syntax."""
        text = "## My Heading\n"
        headings = create_heading_entities(text, "test.md")

        assert len(headings) == 1
        assert headings[0]["name"] == "My Heading"
        assert headings[0]["properties"]["text"] == "My Heading"
        assert "##" not in headings[0]["name"]

    def test_heading_markdown_syntax_preserved(self):
        """Verify original markdown syntax is preserved."""
        text = "### API Overview\n"
        headings = create_heading_entities(text, "test.md")

        assert len(headings) == 1
        assert headings[0]["properties"]["markdown_syntax"] == "### API Overview"

    def test_heading_slug_generation(self):
        """Verify URL-friendly slugs are generated."""
        text = """# API Overview: V1.3
## Getting Started!
### User-Management_API
"""
        headings = create_heading_entities(text, "test.md")

        assert headings[0]["properties"]["slug"] == "api-overview-v1-3"
        assert headings[1]["properties"]["slug"] == "getting-started"
        assert headings[2]["properties"]["slug"] == "user-management-api"

    def test_heading_line_numbers(self):
        """Verify line numbers are accurate."""
        text = """Line 1
# Heading on Line 2
Line 3
## Heading on Line 4
"""
        headings = create_heading_entities(text, "test.md")

        assert headings[0]["properties"]["start_line"] == 2
        assert headings[1]["properties"]["start_line"] == 4

    def test_heading_file_path(self):
        """Verify file path is included."""
        text = "# Heading\n"
        headings = create_heading_entities(text, "spec.md")

        assert headings[0]["properties"]["file_path"] == "spec.md"

    def test_no_headings(self):
        """Verify empty list when no headings present."""
        text = "Just some regular text without headings.\n"
        headings = create_heading_entities(text, "test.md")

        assert len(headings) == 0

    def test_invalid_headings_not_extracted(self):
        """Verify invalid headings are not extracted."""
        text = """#NoSpace
####### TooManyHashes
# 
"""
        headings = create_heading_entities(text, "test.md")

        # Only the empty heading (third line) might be extracted based on logic
        # but ideally none should be extracted
        assert len(headings) == 0


class TestHeadingHelpers:
    """Test heading helper functions."""

    def test_get_heading_level_valid(self):
        """Verify heading level detection for valid headings."""
        assert _get_heading_level("# Heading") == 1
        assert _get_heading_level("## Heading") == 2
        assert _get_heading_level("###### Heading") == 6

    def test_get_heading_level_invalid(self):
        """Verify invalid headings return 0."""
        assert _get_heading_level("#NoSpace") == 0
        assert _get_heading_level("####### TooMany") == 0
        assert _get_heading_level("Not a heading") == 0

    def test_generate_slug_basic(self):
        """Verify basic slug generation."""
        assert _generate_slug("Simple Heading") == "simple-heading"
        assert _generate_slug("UPPERCASE") == "uppercase"

    def test_generate_slug_special_chars(self):
        """Verify special characters are removed."""
        assert _generate_slug("API: Version 1.3") == "api-version-1-3"
        assert _generate_slug("User@Management!") == "usermanagement"

    def test_generate_slug_underscores(self):
        """Verify underscores are converted to hyphens."""
        assert _generate_slug("user_management_api") == "user-management-api"

    def test_generate_slug_multiple_spaces(self):
        """Verify multiple spaces are collapsed."""
        assert _generate_slug("Multiple   Spaces") == "multiple-spaces"


class TestFrontmatterExtraction:
    """Test frontmatter entity extraction."""

    def test_extract_frontmatter(self):
        """Verify frontmatter is extracted."""
        text = """---
title: My Document
version: 1.0
---

# Content
"""
        entity = create_frontmatter_entity(text, "test.md")

        assert entity is not None
        assert entity["type"] == "Frontmatter"
        assert entity["name"] == "Document Frontmatter"

    def test_frontmatter_parsed_fields(self):
        """Verify frontmatter YAML is parsed."""
        text = """---
title: My Doc
author: John Doe
version: 2.0
---

# Content
"""
        entity = create_frontmatter_entity(text, "test.md")

        parsed = entity["properties"]["parsed_fields"]
        assert parsed["title"] == "My Doc"
        assert parsed["author"] == "John Doe"
        assert parsed["version"] == 2.0

    def test_frontmatter_raw_yaml(self):
        """Verify raw YAML is preserved."""
        text = """---
title: Test
---

# Content
"""
        entity = create_frontmatter_entity(text, "test.md")

        assert "title: Test" in entity["properties"]["raw_yaml"]

    def test_no_frontmatter(self):
        """Verify None returned when no frontmatter."""
        text = "# Just a heading\n"
        entity = create_frontmatter_entity(text, "test.md")

        assert entity is None

    def test_frontmatter_line_range(self):
        """Verify line range is calculated."""
        text = """---
title: Test
version: 1.0
---

# Content
"""
        entity = create_frontmatter_entity(text, "test.md")

        assert entity["properties"]["start_line"] == 1
        assert entity["properties"]["end_line"] > 1


class TestHeadingRelationships:
    """Test heading relationship creation."""

    def test_next_heading_relationship(self):
        """Verify sequential heading links."""
        headings = [
            {"id": "h1", "properties": {"level": 1, "start_line": 1}},
            {"id": "h2", "properties": {"level": 2, "start_line": 3}},
            {"id": "h3", "properties": {"level": 2, "start_line": 5}},
        ]

        rels = _create_next_heading_relationships(headings)

        assert len(rels) == 2
        assert rels[0]["type"] == "NEXT_HEADING"
        assert rels[0]["source_entity_id"] == "h1"
        assert rels[0]["target_entity_id"] == "h2"
        assert rels[1]["source_entity_id"] == "h2"
        assert rels[1]["target_entity_id"] == "h3"

    def test_single_heading_no_relationships(self):
        """Verify no NEXT_HEADING for single heading."""
        headings = [{"id": "h1", "properties": {"level": 1, "start_line": 1}}]

        rels = _create_next_heading_relationships(headings)

        assert len(rels) == 0

    def test_titled_by_relationship(self):
        """Verify sections linked to headings."""
        sections = [
            {"id": "s1", "properties": {"start_line": 1}},
            {"id": "s2", "properties": {"start_line": 5}},
        ]
        headings = [
            {"id": "h1", "properties": {"start_line": 1}},
            {"id": "h2", "properties": {"start_line": 5}},
        ]

        rels = _create_titled_by_relationships(sections, headings)

        assert len(rels) == 2
        assert rels[0]["type"] == "TITLED_BY"
        assert rels[0]["source_entity_id"] == "s1"
        assert rels[0]["target_entity_id"] == "h1"


class TestFrontmatterRelationships:
    """Test frontmatter relationship creation."""

    def test_has_frontmatter_relationship(self):
        """Verify document linked to frontmatter."""
        document = {"id": "doc1"}
        frontmatter = {"id": "fm1"}

        rel = _create_frontmatter_relationship(document, frontmatter)

        assert rel["type"] == "HAS_FRONTMATTER"
        assert rel["source_entity_id"] == "doc1"
        assert rel["target_entity_id"] == "fm1"


class TestIntegratedHeadingExtraction:
    """Test integrated heading extraction workflow."""

    def test_complete_workflow(self):
        """Verify complete extraction and relationship creation."""
        text = """---
title: Test Document
---

# Main Title
## Section 1
### Subsection 1.1
## Section 2
"""
        document = {"id": "doc1"}
        sections = [
            {"id": "s1", "properties": {"start_line": 5}},
            {"id": "s2", "properties": {"start_line": 6}},
            {"id": "s3", "properties": {"start_line": 7}},
            {"id": "s4", "properties": {"start_line": 8}},
        ]

        headings = create_heading_entities(text, "test.md")
        frontmatter = create_frontmatter_entity(text, "test.md")
        relationships = create_heading_relationships(
            document, sections, headings, frontmatter
        )

        # Verify entities
        assert len(headings) == 4
        assert frontmatter is not None

        # Verify relationships
        # Should have: TITLED_BY (4), NEXT_HEADING (3), HAS_FRONTMATTER (1)
        titled_by = [r for r in relationships if r["type"] == "TITLED_BY"]
        next_heading = [r for r in relationships if r["type"] == "NEXT_HEADING"]
        has_frontmatter = [r for r in relationships if r["type"] == "HAS_FRONTMATTER"]

        assert len(titled_by) == 4
        assert len(next_heading) == 3
        assert len(has_frontmatter) == 1
