"""Unit tests for markdown list properties validation."""
from markdown_parser.list_entity_builder import create_list_entities


def test_item_count():
    """Verify item counts accurate."""
    text = """
- Item 1
- Item 2
  - Nested 2.1
  - Nested 2.2
- Item 3
"""
    result = create_list_entities(text, "test.md")
    assert len(result) == 1

    list_entity = result[0]
    assert list_entity["properties"]["item_count"] == 3
    assert list_entity["properties"]["total_item_count"] == 5


def test_line_numbers():
    """Verify line numbers are accurate."""
    text = """Some text

- Item 1
- Item 2

More text"""
    result = create_list_entities(text, "test.md")
    assert len(result) == 1

    list_entity = result[0]
    assert list_entity["properties"]["start_line"] == 3
    assert list_entity["properties"]["file_path"] == "test.md"


def test_items_preview():
    """Verify items preview captured."""
    text = """
- First item text
- Second item text
- Third item text
- Fourth item text
"""
    result = create_list_entities(text, "test.md")
    assert len(result) == 1

    list_entity = result[0]
    items_preview = list_entity["properties"]["items_preview"]
    assert len(items_preview) == 3
    assert "First item text" in items_preview[0]
    assert "Second item text" in items_preview[1]
    assert "Third item text" in items_preview[2]


def test_ordered_list_start_number():
    """Verify starting number for ordered lists."""
    text = """
5. Item five
6. Item six
7. Item seven
"""
    result = create_list_entities(text, "test.md")
    assert len(result) == 1

    list_entity = result[0]
    assert list_entity["properties"]["ordered_start"] == 5


def test_nesting_level():
    """Verify nesting level is calculated correctly."""
    text = """
- Top level
  - Nested level 1
    - Nested level 2
"""
    result = create_list_entities(text, "test.md")
    assert len(result) == 1

    list_entity = result[0]
    assert list_entity["properties"]["nesting_level"] == 0
    assert list_entity["properties"]["is_nested"] is False
