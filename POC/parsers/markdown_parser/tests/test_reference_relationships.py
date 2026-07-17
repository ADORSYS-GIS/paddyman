"""Unit tests for reference relationship builder."""
import pytest
from markdown_parser.reference_relationship_builder import (
    create_reference_relationships,
)


class TestReferenceRelationships:
    """Test reference relationship creation."""

    def test_references_to_section(self):
        """Test REFERENCES relationship from section to reference."""
        references = [{
            "id": "ref-1",
            "properties": {"start_line": 5}
        }]
        sections = [{
            "id": "section-1",
            "properties": {"start_line": 1, "end_line": 10}
        }]
        paragraphs = []

        rels = create_reference_relationships(references, sections, paragraphs)
        
        section_refs = [r for r in rels if r["type"] == "REFERENCES"]
        assert len(section_refs) >= 1
        assert section_refs[0]["source_entity_id"] == "section-1"
        assert section_refs[0]["target_entity_id"] == "ref-1"

    def test_references_to_paragraph(self):
        """Test REFERENCES relationship from paragraph to reference."""
        references = [{
            "id": "ref-1",
            "properties": {"start_line": 5}
        }]
        sections = []
        paragraphs = [{
            "id": "para-1",
            "properties": {"start_line": 4, "end_line": 6}
        }]

        rels = create_reference_relationships(references, sections, paragraphs)
        
        para_refs = [r for r in rels if r["type"] == "REFERENCES"]
        assert len(para_refs) >= 1

    def test_links_to_section(self):
        """Test LINKS_TO relationship from anchor reference to section."""
        references = [{
            "id": "ref-1",
            "properties": {
                "start_line": 5,
                "target_url": "#section-heading"
            }
        }]
        sections = [{
            "id": "section-1",
            "properties": {
                "start_line": 10,
                "end_line": 20,
                "heading_anchor": "section-heading"
            }
        }]
        paragraphs = []

        rels = create_reference_relationships(references, sections, paragraphs)
        
        links_to = [r for r in rels if r["type"] == "LINKS_TO"]
        assert len(links_to) == 1
        assert links_to[0]["source_entity_id"] == "ref-1"
        assert links_to[0]["target_entity_id"] == "section-1"

    def test_next_reference(self):
        """Test NEXT_REFERENCE sequential relationships."""
        references = [
            {"id": "ref-1", "properties": {"start_line": 5}},
            {"id": "ref-2", "properties": {"start_line": 10}},
            {"id": "ref-3", "properties": {"start_line": 15}},
        ]
        sections = []
        paragraphs = []

        rels = create_reference_relationships(references, sections, paragraphs)
        
        next_refs = [r for r in rels if r["type"] == "NEXT_REFERENCE"]
        assert len(next_refs) == 2
        
        # Verify sequential order
        assert next_refs[0]["source_entity_id"] == "ref-1"
        assert next_refs[0]["target_entity_id"] == "ref-2"
        assert next_refs[1]["source_entity_id"] == "ref-2"
        assert next_refs[1]["target_entity_id"] == "ref-3"

    def test_no_references(self):
        """Test with no references."""
        rels = create_reference_relationships([], [], [])
        assert len(rels) == 0

    def test_reference_outside_containers(self):
        """Test reference not in any section or paragraph."""
        references = [{
            "id": "ref-1",
            "properties": {"start_line": 100}
        }]
        sections = [{
            "id": "section-1",
            "properties": {"start_line": 1, "end_line": 10}
        }]
        paragraphs = []

        rels = create_reference_relationships(references, sections, paragraphs)
        
        # Should not create REFERENCES relationships
        refs_rels = [r for r in rels if r["type"] == "REFERENCES"]
        assert len(refs_rels) == 0

    def test_unresolved_anchor_link(self):
        """Test anchor link to non-existent section."""
        references = [{
            "id": "ref-1",
            "properties": {
                "start_line": 5,
                "target_url": "#nonexistent"
            }
        }]
        sections = [{
            "id": "section-1",
            "properties": {
                "start_line": 10,
                "end_line": 20,
                "heading_anchor": "existing"
            }
        }]

        rels = create_reference_relationships(references, sections, [])
        
        # Should not create LINKS_TO for unresolved anchor
        links_to = [r for r in rels if r["type"] == "LINKS_TO"]
        assert len(links_to) == 0
