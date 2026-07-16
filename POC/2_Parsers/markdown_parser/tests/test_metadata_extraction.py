"""Unit tests for markdown specification metadata extraction."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from markdown_parser.frontmatter_parser import (
    parse_frontmatter,
    extract_specification_metadata,
)
from markdown_parser.filename_metadata import extract_from_filename
from markdown_parser.content_metadata import extract_from_content
from markdown_parser.metadata_extractor import (
    extract_specification_metadata as extract_full_metadata,
)


class TestFrontmatterParser:
    """Tests for YAML frontmatter parsing."""

    def test_parse_valid_frontmatter(self):
        """Verify YAML frontmatter is parsed correctly."""
        text = """---
title: NextGenPSD2 Implementation Guidelines
version: 1.3
category: Implementation Guidelines
organization: Berlin Group
published: 2021-03-15
---

# Document Content
"""
        result = parse_frontmatter(text)
        
        # YAML parser returns native types
        assert result["title"] == "NextGenPSD2 Implementation Guidelines"
        assert result["version"] == 1.3  # YAML numeric value
        assert result["category"] == "Implementation Guidelines"
        assert result["organization"] == "Berlin Group"
        # YAML parses dates as date objects
        from datetime import date
        assert result["published"] == date(2021, 3, 15)

    def test_parse_no_frontmatter(self):
        """Verify empty dict returned when no frontmatter present."""
        text = "# Document\n\nContent without frontmatter."
        result = parse_frontmatter(text)
        
        assert result == {}

    def test_parse_malformed_frontmatter(self):
        """Verify graceful handling of malformed YAML."""
        text = """---
invalid yaml: [unclosed bracket
---

# Content
"""
        result = parse_frontmatter(text)
        
        assert result == {}

    def test_extract_specification_metadata(self):
        """Verify specification fields extracted from frontmatter."""
        frontmatter = {
            "title": "API Specification",
            "version": "2.0",
            "category": "API Specification",
            "organization": "Berlin Group",
        }
        
        result = extract_specification_metadata(frontmatter)
        
        assert result["specification_name"] == "API Specification"
        assert result["specification_version"] == "2.0"
        assert result["specification_category"] == "API Specification"
        assert result["source_organization"] == "Berlin Group"


class TestFilenameMetadata:
    """Tests for filename pattern extraction."""

    def test_extract_from_filename_with_version(self):
        """Verify metadata extracted from filename with version."""
        file_path = Path("nextgenpsd2_implementation_guidelines_1_3_clean.md")
        
        result = extract_from_filename(file_path)
        
        assert result["specification_name"] == "Nextgenpsd2 Implementation Guidelines"
        assert result["specification_version"] == "1.3"

    def test_extract_version_with_underscores(self):
        """Verify version extracted with underscores normalized."""
        file_path = Path("ais_for_savings_accounts_v1_2.md")
        
        result = extract_from_filename(file_path)
        
        assert result["specification_version"] == "1.2"

    def test_extract_version_with_dots(self):
        """Verify version extracted with dots."""
        file_path = Path("api_spec_v2.1.0.md")
        
        result = extract_from_filename(file_path)
        
        assert result["specification_version"] == "2.1.0"

    def test_extract_specification_name(self):
        """Verify specification name extracted and title-cased."""
        file_path = Path("berlin_group_implementation_guidelines.md")
        
        result = extract_from_filename(file_path)
        
        assert result["specification_name"] == "Berlin Group Implementation Guidelines"

    def test_infer_category_from_filename(self):
        """Verify category inferred from filename patterns."""
        test_cases = [
            ("nextgenpsd2_implementation_guidelines.md", "Implementation Guidelines"),
            ("operational_rules_1_0.md", "Operational Rules"),
            ("api_specification_v2.md", "API Specification"),
            ("reference_manual.md", "Reference Manual"),
        ]
        
        for filename, expected_category in test_cases:
            file_path = Path(filename)
            result = extract_from_filename(file_path)
            assert result.get("specification_category") == expected_category


class TestContentMetadata:
    """Tests for content-based metadata extraction."""

    def test_extract_title_from_heading(self):
        """Verify title extracted from first heading."""
        text = """
# NextGenPSD2 Implementation Guidelines

This is the content.
"""
        result = extract_from_content(text)
        
        assert result["specification_name"] == "NextGenPSD2 Implementation Guidelines"

    def test_extract_version_from_content(self):
        """Verify version extracted from content."""
        text = """
# API Specification

Version: 1.3.2

This document describes...
"""
        result = extract_from_content(text)
        
        assert result["specification_version"] == "1.3.2"

    def test_extract_organization_from_content(self):
        """Verify organization extracted from content."""
        text = """
# Implementation Guidelines

by Berlin Group

This document...
"""
        result = extract_from_content(text)
        
        assert result["source_organization"] == "Berlin Group"

    def test_extract_publication_date(self):
        """Verify publication date extracted from content."""
        text = """
# Specification

Published: 2021-03-15

Content here.
"""
        result = extract_from_content(text)
        
        assert result["publication_date"] == "2021-03-15"


class TestMetadataExtractor:
    """Tests for orchestrated metadata extraction."""

    def test_frontmatter_takes_priority(self):
        """Verify frontmatter metadata takes priority over filename."""
        text = """---
title: Correct Title from Frontmatter
version: 2.0
---

# Content
"""
        file_path = Path("wrong_title_v1_0.md")
        
        result = extract_full_metadata(file_path, text)
        
        assert result["specification_name"] == "Correct Title from Frontmatter"
        assert result["specification_version"] == "2.0"

    def test_filename_fills_gaps(self):
        """Verify filename extraction fills missing frontmatter fields."""
        text = """---
title: API Specification
---

# Content
"""
        file_path = Path("api_specification_v1_3.md")
        
        result = extract_full_metadata(file_path, text)
        
        assert result["specification_name"] == "API Specification"
        assert result["specification_version"] == "1.3"

    def test_content_fallback(self):
        """Verify content extraction fills gaps not covered by filename."""
        text = """# API Specification

by Berlin Group

Published: 2021-03-15

This document describes the API.
"""
        # Filename provides name and version, content provides organization and date
        file_path = Path("api_spec_v1_0.md")
        
        result = extract_full_metadata(file_path, text)
        
        # Name from filename (not content heading), "api" is uppercased as acronym
        assert result["specification_name"] == "API Spec"
        # Version from filename
        assert result["specification_version"] == "1.0"
        # Organization from content (fallback)
        assert result.get("source_organization") == "Berlin Group"
        # Publication date from content (fallback)
        assert result.get("publication_date") == "2021-03-15"

    def test_defaults_applied(self):
        """Verify default values applied for missing fields."""
        text = "Some content without metadata."
        file_path = Path("simple_document.md")
        
        result = extract_full_metadata(file_path, text)
        
        # Filename is title-cased by the filename extractor
        assert result["specification_name"] == "Simple Document"
        assert result["specification_version"] == "unknown"
        assert result["specification_category"] == "Specification"

    def test_file_provenance_included(self):
        """Verify file provenance fields are included."""
        text = "# Document\n\nContent."
        file_path = Path("/path/to/document.md")
        
        result = extract_full_metadata(file_path, text)
        
        assert "file_path" in result
        assert "relative_path" in result
        assert "file_name" in result
        assert result["file_name"] == "document.md"
        assert result["source_parser"] == "markdown_parser"
        assert "parsed_at" in result
