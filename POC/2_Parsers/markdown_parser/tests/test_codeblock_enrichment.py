"""Unit tests for enrich_codeblock_parent_sections."""
from __future__ import annotations

from markdown_parser.codeblock_entity_builder import enrich_codeblock_parent_sections


def _make_section(name: str, start: int, end: int) -> dict:
    return {
        "id": f"sec-{name}",
        "type": "Section",
        "name": name,
        "properties": {"start_line": start, "end_line": end},
    }


def _make_codeblock(start_line: int) -> dict:
    return {
        "id": f"cb-{start_line}",
        "type": "CodeBlock",
        "properties": {"start_line": start_line, "parent_section": None},
    }


class TestEnrichCodeblockParentSections:
    """Tests for enrich_codeblock_parent_sections."""

    def test_associates_with_containing_section(self):
        """Code block gets the name of its containing section."""
        sections = [_make_section("API Overview", 1, 20)]
        codeblocks = [_make_codeblock(5)]

        enrich_codeblock_parent_sections(codeblocks, sections)

        assert codeblocks[0]["properties"]["parent_section"] == "API Overview"

    def test_none_when_no_containing_section(self):
        """parent_section is None when no section contains the code block."""
        sections = [_make_section("Section A", 10, 20)]
        codeblocks = [_make_codeblock(5)]

        enrich_codeblock_parent_sections(codeblocks, sections)

        assert codeblocks[0]["properties"]["parent_section"] is None

    def test_picks_smallest_containing_section(self):
        """Nested sections: innermost (latest-starting) section wins."""
        sections = [
            _make_section("Chapter 1", 1, 50),
            _make_section("Section 1.1", 10, 30),
        ]
        codeblocks = [_make_codeblock(15)]

        enrich_codeblock_parent_sections(codeblocks, sections)

        assert codeblocks[0]["properties"]["parent_section"] == "Section 1.1"

    def test_multiple_codeblocks_different_sections(self):
        """Each code block maps to its own parent section."""
        sections = [
            _make_section("Intro", 1, 10),
            _make_section("Details", 11, 20),
        ]
        codeblocks = [_make_codeblock(3), _make_codeblock(15)]

        enrich_codeblock_parent_sections(codeblocks, sections)

        assert codeblocks[0]["properties"]["parent_section"] == "Intro"
        assert codeblocks[1]["properties"]["parent_section"] == "Details"

    def test_empty_inputs_no_error(self):
        """Empty inputs do not raise."""
        enrich_codeblock_parent_sections([], [])

    def test_empty_sections_yields_none(self):
        """No sections means all code blocks get parent_section=None."""
        codeblocks = [_make_codeblock(5)]
        enrich_codeblock_parent_sections(codeblocks, [])

        assert codeblocks[0]["properties"]["parent_section"] is None

    def test_codeblock_on_section_boundary(self):
        """Code block exactly on section start line is contained."""
        sections = [_make_section("Boundary", 5, 10)]
        codeblocks = [_make_codeblock(5)]

        enrich_codeblock_parent_sections(codeblocks, sections)

        assert codeblocks[0]["properties"]["parent_section"] == "Boundary"
