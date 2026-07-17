"""Unit tests for markdown list relationships."""
from markdown_parser.list_entity_builder import create_list_entities
from markdown_parser.list_relationship_builder import create_list_relationships


def test_next_list_relationship():
    """Verify NEXT_LIST relationships preserve order."""
    text = """
- First list item
- Second list item

Some text

1. Another list item
2. Another list item 2
"""
    list_entities = create_list_entities(text, "test.md")
    relationships = create_list_relationships(list_entities)

    next_list_rels = [r for r in relationships if r["type"] == "NEXT_LIST"]
    assert len(next_list_rels) == 1

    rel = next_list_rels[0]
    assert rel["source_entity_id"] == list_entities[0]["id"]
    assert rel["target_entity_id"] == list_entities[1]["id"]


def test_no_next_list_for_single_list():
    """Verify no NEXT_LIST relationship for single list."""
    text = """
- Item 1
- Item 2
"""
    list_entities = create_list_entities(text, "test.md")
    relationships = create_list_relationships(list_entities)

    next_list_rels = [r for r in relationships if r["type"] == "NEXT_LIST"]
    assert len(next_list_rels) == 0


def test_multiple_next_list_relationships():
    """Verify multiple NEXT_LIST relationships for three lists."""
    text = """
- List 1

Text

1. List 2

More text

* List 3
"""
    list_entities = create_list_entities(text, "test.md")
    relationships = create_list_relationships(list_entities)

    next_list_rels = [r for r in relationships if r["type"] == "NEXT_LIST"]
    assert len(next_list_rels) == 2


def test_sequential_order_preserved():
    """Verify NEXT_LIST relationships preserve document order."""
    text = """
- List A

Text

- List B

Text

- List C
"""
    list_entities = create_list_entities(text, "test.md")
    relationships = create_list_relationships(list_entities)

    next_list_rels = [r for r in relationships if r["type"] == "NEXT_LIST"]
    assert len(next_list_rels) == 2

    # Verify A -> B -> C order
    a_to_b = [r for r in next_list_rels if r["source_entity_id"] == list_entities[0]["id"]]
    b_to_c = [r for r in next_list_rels if r["source_entity_id"] == list_entities[1]["id"]]

    assert len(a_to_b) == 1
    assert len(b_to_c) == 1
    assert a_to_b[0]["target_entity_id"] == list_entities[1]["id"]
    assert b_to_c[0]["target_entity_id"] == list_entities[2]["id"]
