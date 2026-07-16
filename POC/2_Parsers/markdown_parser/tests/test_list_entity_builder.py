"""Unit tests for markdown list entity extraction."""
from markdown_parser.list_entity_builder import create_list_entities


def test_extract_unordered_list():
    """Verify unordered lists extracted."""
    text = """
- Item 1
- Item 2
- Item 3
"""
    result = create_list_entities(text, "test.md")
    assert len(result) == 1

    list_entity = result[0]
    assert list_entity["type"] == "List"
    assert list_entity["properties"]["list_type"] == "unordered"
    assert list_entity["properties"]["item_count"] == 3
    assert list_entity["properties"]["is_nested"] is False
    assert list_entity["properties"]["nesting_level"] == 0


def test_extract_ordered_list():
    """Verify ordered lists extracted."""
    text = """
1. First item
2. Second item
3. Third item
"""
    result = create_list_entities(text, "test.md")
    assert len(result) == 1

    list_entity = result[0]
    assert list_entity["type"] == "List"
    assert list_entity["properties"]["list_type"] == "ordered"
    assert list_entity["properties"]["item_count"] == 3
    assert list_entity["properties"]["ordered_start"] == 1


def test_nested_list():
    """Verify nested lists detected."""
    text = """
- Item 1
- Item 2
  - Nested item 2.1
  - Nested item 2.2
- Item 3
"""
    result = create_list_entities(text, "test.md")
    assert len(result) == 1

    list_entity = result[0]
    assert list_entity["properties"]["item_count"] == 3
    assert list_entity["properties"]["total_item_count"] == 5


def test_task_list():
    """Verify task list items identified."""
    text = """
- [ ] Incomplete task
- [x] Completed task
- [ ] Another incomplete task
"""
    result = create_list_entities(text, "test.md")
    assert len(result) == 1

    list_entity = result[0]
    assert list_entity["type"] == "List"
    assert list_entity["properties"]["list_type"] == "unordered"
    assert list_entity["properties"]["item_count"] == 3


def test_multiple_separate_lists():
    """Verify multiple separate lists extracted."""
    text = """
- List 1 item 1
- List 1 item 2

Some text in between

1. List 2 item 1
2. List 2 item 2
"""
    result = create_list_entities(text, "test.md")
    assert len(result) == 2

    assert result[0]["properties"]["list_type"] == "unordered"
    assert result[1]["properties"]["list_type"] == "ordered"


def test_empty_text():
    """Verify empty text returns no lists."""
    result = create_list_entities("", "test.md")
    assert len(result) == 0


def test_no_lists():
    """Verify text without lists returns empty."""
    text = """
This is just normal text.
No lists here.
"""
    result = create_list_entities(text, "test.md")
    assert len(result) == 0


def test_mixed_list_markers():
    """Verify lists with different markers (-, *, +) are recognized."""
    text = """
- Dash item
* Asterisk item
+ Plus item
"""
    result = create_list_entities(text, "test.md")
    assert len(result) == 1

    list_entity = result[0]
    assert list_entity["properties"]["list_type"] == "unordered"
    assert list_entity["properties"]["item_count"] == 3


def test_ordered_list_with_parenthesis():
    """Verify ordered lists with parenthesis markers."""
    text = """
1) First item
2) Second item
3) Third item
"""
    result = create_list_entities(text, "test.md")
    assert len(result) == 1

    list_entity = result[0]
    assert list_entity["properties"]["list_type"] == "ordered"
    assert list_entity["properties"]["item_count"] == 3
