"""Unit tests for section hierarchy relationships."""
from markdown_parser.section_hierarchy import (
    build_parent_relationships,
    build_sibling_relationships,
    build_first_child_relationships,
    enrich_section_depth_and_path,
)


def test_parent_section_relationship():
    """Verify child sections linked to parents."""
    sections = [
        {
            "id": "section-1",
            "name": "Main",
            "type": "Section",
            "properties": {"level": 1, "start_line": 1, "parent_section_id": None},
        },
        {
            "id": "section-2",
            "name": "Subsection",
            "type": "Section",
            "properties": {"level": 2, "start_line": 5, "parent_section_id": None},
        },
    ]

    relationships = build_parent_relationships(sections)

    assert len(relationships) == 1
    rel = relationships[0]
    assert rel["type"] == "PARENT_SECTION"
    assert rel["source_entity_id"] == "section-2"
    assert rel["target_entity_id"] == "section-1"
    assert rel["properties"]["child_level"] == 2
    assert rel["properties"]["parent_level"] == 1
    assert sections[1]["properties"]["parent_section_id"] == "section-1"


def test_multiple_levels():
    """Verify three-level hierarchy."""
    sections = [
        {"id": "s1", "name": "A", "type": "Section", "properties": {"level": 1, "start_line": 1}},
        {"id": "s2", "name": "B", "type": "Section", "properties": {"level": 2, "start_line": 5}},
        {"id": "s3", "name": "C", "type": "Section", "properties": {"level": 3, "start_line": 10}},
    ]

    relationships = build_parent_relationships(sections)

    assert len(relationships) == 2
    assert relationships[0]["source_entity_id"] == "s2"
    assert relationships[0]["target_entity_id"] == "s1"
    assert relationships[1]["source_entity_id"] == "s3"
    assert relationships[1]["target_entity_id"] == "s2"


def test_level_skip_handling():
    """Verify skipped levels handled gracefully."""
    sections = [
        {"id": "s1", "name": "Main", "type": "Section", "properties": {"level": 1, "start_line": 1}},
        {"id": "s2", "name": "Deep", "type": "Section", "properties": {"level": 3, "start_line": 5}},
    ]

    relationships = build_parent_relationships(sections)

    assert len(relationships) == 1
    assert relationships[0]["source_entity_id"] == "s2"
    assert relationships[0]["target_entity_id"] == "s1"


def test_next_sibling_relationship():
    """Verify sibling sections linked."""
    sections = [
        {"id": "s1", "name": "A", "type": "Section", "properties": {"level": 1, "start_line": 1}},
        {"id": "s2", "name": "A1", "type": "Section", "properties": {"level": 2, "start_line": 5}},
        {"id": "s3", "name": "A2", "type": "Section", "properties": {"level": 2, "start_line": 10}},
        {"id": "s4", "name": "B", "type": "Section", "properties": {"level": 1, "start_line": 15}},
    ]

    parent_rels = build_parent_relationships(sections)
    sibling_rels = build_sibling_relationships(sections, parent_rels)

    assert len(sibling_rels) == 2
    
    sibling_pairs = {(r["source_entity_id"], r["target_entity_id"]) for r in sibling_rels}
    assert ("s2", "s3") in sibling_pairs  # A1 -> A2
    assert ("s1", "s4") in sibling_pairs  # A -> B


def test_first_child_relationship():
    """Verify parent linked to first child."""
    sections = [
        {"id": "s1", "name": "Main", "type": "Section", "properties": {"level": 1, "start_line": 1}},
        {"id": "s2", "name": "Child2", "type": "Section", "properties": {"level": 2, "start_line": 10}},
        {"id": "s3", "name": "Child1", "type": "Section", "properties": {"level": 2, "start_line": 5}},
    ]

    parent_rels = build_parent_relationships(sections)
    first_child_rels = build_first_child_relationships(sections, parent_rels)

    assert len(first_child_rels) == 1
    rel = first_child_rels[0]
    assert rel["type"] == "FIRST_CHILD"
    assert rel["source_entity_id"] == "s1"
    assert rel["target_entity_id"] == "s3"  # Child1 comes first (line 5)


def test_section_depth():
    """Verify section depth calculated."""
    sections = [
        {"id": "s1", "name": "A", "type": "Section", "properties": {"level": 1, "start_line": 1}},
        {"id": "s2", "name": "B", "type": "Section", "properties": {"level": 2, "start_line": 5}},
        {"id": "s3", "name": "C", "type": "Section", "properties": {"level": 3, "start_line": 10}},
    ]

    parent_rels = build_parent_relationships(sections)
    enrich_section_depth_and_path(sections, parent_rels)

    assert sections[0]["properties"]["depth"] == 0
    assert sections[1]["properties"]["depth"] == 1
    assert sections[2]["properties"]["depth"] == 2


def test_section_path():
    """Verify section path shows ancestors."""
    sections = [
        {"id": "s1", "name": "A", "type": "Section", "properties": {"level": 1, "start_line": 1}},
        {"id": "s2", "name": "B", "type": "Section", "properties": {"level": 2, "start_line": 5}},
        {"id": "s3", "name": "C", "type": "Section", "properties": {"level": 3, "start_line": 10}},
    ]

    parent_rels = build_parent_relationships(sections)
    enrich_section_depth_and_path(sections, parent_rels)

    assert sections[0]["properties"]["path"] == ""
    assert sections[1]["properties"]["path"] == "A"
    assert sections[2]["properties"]["path"] == "A / B"


def test_no_parent_sections():
    """Verify top-level sections have no relationships."""
    sections = [
        {"id": "s1", "name": "A", "type": "Section", "properties": {"level": 1, "start_line": 1}},
        {"id": "s2", "name": "B", "type": "Section", "properties": {"level": 1, "start_line": 5}},
    ]

    parent_rels = build_parent_relationships(sections)

    assert len(parent_rels) == 0


def test_complex_hierarchy():
    """Verify complex nested structure."""
    sections = [
        {"id": "s1", "name": "Intro", "type": "Section", "properties": {"level": 1, "start_line": 1}},
        {"id": "s2", "name": "Overview", "type": "Section", "properties": {"level": 2, "start_line": 3}},
        {"id": "s3", "name": "Details", "type": "Section", "properties": {"level": 2, "start_line": 7}},
        {"id": "s4", "name": "Subsection", "type": "Section", "properties": {"level": 3, "start_line": 10}},
        {"id": "s5", "name": "Conclusion", "type": "Section", "properties": {"level": 1, "start_line": 15}},
    ]

    parent_rels = build_parent_relationships(sections)
    sibling_rels = build_sibling_relationships(sections, parent_rels)
    first_child_rels = build_first_child_relationships(sections, parent_rels)
    enrich_section_depth_and_path(sections, parent_rels)

    assert len(parent_rels) == 3  # s2->s1, s3->s1, s4->s3
    assert len(sibling_rels) == 2  # s2->s3, s1->s5
    assert len(first_child_rels) == 2  # s1->s2, s3->s4

    assert sections[3]["properties"]["path"] == "Intro / Details"
    assert sections[3]["properties"]["depth"] == 2
