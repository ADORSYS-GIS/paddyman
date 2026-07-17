"""Unit tests for cross-document reference relationship resolution."""
from __future__ import annotations

from markdown_parser.reference_relationship_builder import create_reference_relationships


def test_internal_section_reference_resolution() -> None:
    references = [{
        "id": "ref-1",
        "properties": {"start_line": 5, "reference_type": "section", "target_section": "4.2"},
    }]
    sections = [{
        "id": "section-42",
        "properties": {"start_line": 1, "end_line": 20, "heading_text": "4.2 Authentication"},
    }]
    rels = create_reference_relationships(references, sections, [])
    target_links = [r for r in rels if r["type"] == "REFERENCES" and r["source_entity_id"] == "ref-1"]
    assert len(target_links) == 1
    assert target_links[0]["target_entity_id"] == "section-42"


def test_external_spec_tagging_relationship() -> None:
    references = [{
        "id": "ref-psd2",
        "properties": {"start_line": 2, "reference_type": "external_spec", "target_spec": "PSD2"},
    }]
    rels = create_reference_relationships(references, [], [])
    external = [r for r in rels if r["type"] == "REFERENCES_EXTERNAL"]
    assert len(external) == 1
    assert external[0]["target_entity_id"] == "external_spec:PSD2"
