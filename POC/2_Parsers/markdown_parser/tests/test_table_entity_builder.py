"""Unit tests for markdown table entity builder."""
from markdown_parser.table_entity_builder import (
    create_table_entities,
    create_table_sequential_relationships,
)


def test_extract_simple_table():
    """Verify tables are extracted as entities."""
    text = """
| Name | Age |
|------|-----|
| Alice | 30 |
| Bob | 25 |
"""
    result = create_table_entities(text, "test.md")
    assert len(result) == 1

    table = result[0]
    assert table["type"] == "Table"
    assert table["properties"]["headers"] == ["Name", "Age"]
    assert table["properties"]["row_count"] == 2
    assert table["properties"]["column_count"] == 2


def test_table_headers_captured():
    """Verify table headers captured."""
    text = """
| Name | Age |
|------|-----|
| Alice | 30 |
"""
    result = create_table_entities(text, "test.md")
    assert result[0]["properties"]["headers"] == ["Name", "Age"]


def test_table_row_column_counts():
    """Verify row and column counts."""
    text = """
| A | B |
|---|---|
| 1 | 2 |
| 3 | 4 |
| 5 | 6 |
"""
    result = create_table_entities(text, "test.md")
    assert result[0]["properties"]["row_count"] == 3
    assert result[0]["properties"]["column_count"] == 2


def test_table_caption():
    """Verify table caption extracted."""
    text = """
Table of users

| Name | Age |
|------|-----|
| Alice | 30 |
"""
    result = create_table_entities(text, "test.md")
    assert result[0]["properties"]["caption"] == "Table of users"
    assert result[0]["name"] == "Table of users"


def test_table_alignment_left():
    """Verify left alignment captured."""
    text = """
| Left |
|:-----|
| Data |
"""
    result = create_table_entities(text, "test.md")
    assert result[0]["properties"]["alignment"] == ["left"]


def test_table_alignment_center():
    """Verify center alignment captured."""
    text = """
| Center |
|:------:|
| Data   |
"""
    result = create_table_entities(text, "test.md")
    assert result[0]["properties"]["alignment"] == ["center"]


def test_table_alignment_right():
    """Verify right alignment captured."""
    text = """
| Right |
|------:|
| Data  |
"""
    result = create_table_entities(text, "test.md")
    assert result[0]["properties"]["alignment"] == ["right"]


def test_table_alignment_mixed():
    """Verify mixed column alignment captured."""
    text = """
| Left | Center | Right |
|:-----|:------:|------:|
| A    | B      | C     |
"""
    result = create_table_entities(text, "test.md")
    assert result[0]["properties"]["alignment"] == ["left", "center", "right"]


def test_table_file_path():
    """Verify file_path property is set."""
    text = """
| Name |
|------|
| Test |
"""
    result = create_table_entities(text, "example.md")
    assert result[0]["properties"]["file_path"] == "example.md"


def test_table_rows_preview():
    """Verify rows_preview contains first 3 rows."""
    text = """
| Col1 |
|------|
| Row1 |
| Row2 |
| Row3 |
| Row4 |
| Row5 |
"""
    result = create_table_entities(text, "test.md")
    rows_preview = result[0]["properties"]["rows_preview"]
    assert len(rows_preview) == 3
    assert rows_preview[0] == ["Row1"]
    assert rows_preview[1] == ["Row2"]
    assert rows_preview[2] == ["Row3"]


def test_table_rows_preview_less_than_three():
    """Verify rows_preview with less than 3 rows."""
    text = """
| Col1 |
|------|
| Row1 |
"""
    result = create_table_entities(text, "test.md")
    rows_preview = result[0]["properties"]["rows_preview"]
    assert len(rows_preview) == 1
    assert rows_preview[0] == ["Row1"]


def test_next_table_relationship():
    """Verify sequential table links."""
    text = """
| Table1 |
|--------|
| Data1  |

| Table2 |
|--------|
| Data2  |

| Table3 |
|--------|
| Data3  |
"""
    tables = create_table_entities(text, "test.md")
    relationships = create_table_sequential_relationships(tables)

    assert len(relationships) == 2

    # First relationship: Table1 -> Table2
    rel1 = relationships[0]
    assert rel1["type"] == "NEXT_TABLE"
    assert rel1["source_entity_id"] == tables[0]["id"]
    assert rel1["target_entity_id"] == tables[1]["id"]

    # Second relationship: Table2 -> Table3
    rel2 = relationships[1]
    assert rel2["type"] == "NEXT_TABLE"
    assert rel2["source_entity_id"] == tables[1]["id"]
    assert rel2["target_entity_id"] == tables[2]["id"]


def test_next_table_no_relationships_single_table():
    """Verify no NEXT_TABLE relationships for single table."""
    text = """
| Name |
|------|
| Test |
"""
    tables = create_table_entities(text, "test.md")
    relationships = create_table_sequential_relationships(tables)
    assert len(relationships) == 0


def test_next_table_empty_list():
    """Verify no NEXT_TABLE relationships for empty list."""
    relationships = create_table_sequential_relationships([])
    assert len(relationships) == 0


def test_table_empty_cells():
    """Verify table with empty cells."""
    text = """
| Col1 | Col2 | Col3 |
|------|------|------|
| A    |      | C    |
|      | B    |      |
"""
    result = create_table_entities(text, "test.md")
    rows_preview = result[0]["properties"]["rows_preview"]
    assert rows_preview[0] == ["A", "", "C"]
    assert rows_preview[1] == ["", "B", ""]


def test_table_only_header():
    """Verify table with header and separator but no data rows."""
    text = """
| Header1 | Header2 |
|---------|---------|
"""
    result = create_table_entities(text, "test.md")
    assert len(result) == 1
    assert result[0]["properties"]["row_count"] == 0
    assert result[0]["properties"]["rows_preview"] == []


def test_no_tables_returns_empty_list():
    """Verify text without tables returns empty list."""
    text = "# Heading\n\nSome paragraph text without any tables."
    result = create_table_entities(text, "test.md")
    assert result == []


def test_two_separate_tables():
    """Verify extraction of two separate tables."""
    text = """
| Table1 |
|--------|
| Data1  |

Some text between tables

| Table2 | Col2 |
|--------|------|
| Data2  | Val2 |
"""
    result = create_table_entities(text, "test.md")
    assert len(result) == 2
    assert result[0]["properties"]["headers"] == ["Table1"]
    assert result[1]["properties"]["headers"] == ["Table2", "Col2"]
