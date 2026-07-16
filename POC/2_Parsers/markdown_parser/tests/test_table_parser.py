"""Unit tests for markdown table parser."""
from markdown_parser.table_parser import (
    is_table_row,
    parse_table,
    _parse_table_row,
    _is_separator_line,
    _extract_alignment,
)


def test_is_table_row_with_leading_pipe():
    """Test line starting with pipe is recognized as table row."""
    assert is_table_row("| Header | Value |")


def test_is_table_row_with_pipe():
    """Test line containing pipe is recognized as table row."""
    assert is_table_row("Header | Value")


def test_is_table_row_no_pipe():
    """Test line without pipe is not recognized as table row."""
    assert not is_table_row("Regular paragraph text")


def test_parse_table_row():
    """Test parsing a table row into columns."""
    result = _parse_table_row("| Name | Age | City |")
    assert result == ["Name", "Age", "City"]


def test_parse_table_row_no_leading_pipe():
    """Test parsing row without leading pipe."""
    result = _parse_table_row("Name | Age | City |")
    assert result == ["Name", "Age", "City"]


def test_parse_table_row_no_trailing_pipe():
    """Test parsing row without trailing pipe."""
    result = _parse_table_row("| Name | Age | City")
    assert result == ["Name", "Age", "City"]


def test_parse_table_row_whitespace():
    """Test parsing row with extra whitespace."""
    result = _parse_table_row("|  Name  |  Age  |  City  |")
    assert result == ["Name", "Age", "City"]


def test_is_separator_line_basic():
    """Test basic separator line."""
    assert _is_separator_line("|---|---|")


def test_is_separator_line_no_pipes():
    """Test separator without pipes."""
    assert _is_separator_line("--- | ---")


def test_is_separator_line_left_align():
    """Test separator with left alignment."""
    assert _is_separator_line("|:---|:---|")


def test_is_separator_line_right_align():
    """Test separator with right alignment."""
    assert _is_separator_line("|---:|---:|")


def test_is_separator_line_center_align():
    """Test separator with center alignment."""
    assert _is_separator_line("|:---:|:---:|")


def test_is_separator_line_mixed():
    """Test separator with mixed alignment."""
    assert _is_separator_line("|:---|:---:|---:|")


def test_is_separator_line_not_separator():
    """Test non-separator line."""
    assert not _is_separator_line("| Data | Value |")


def test_extract_alignment_left():
    """Test extracting left alignment."""
    result = _extract_alignment("|:---|:---|")
    assert result == ["left", "left"]


def test_extract_alignment_right():
    """Test extracting right alignment."""
    result = _extract_alignment("|---:|---:|")
    assert result == ["right", "right"]


def test_extract_alignment_center():
    """Test extracting center alignment."""
    result = _extract_alignment("|:---:|:---:|")
    assert result == ["center", "center"]


def test_extract_alignment_mixed():
    """Test extracting mixed alignment."""
    result = _extract_alignment("|:---|:---:|---:|")
    assert result == ["left", "center", "right"]


def test_extract_alignment_default():
    """Test default alignment (no colons)."""
    result = _extract_alignment("|---|---|")
    assert result == ["left", "left"]


def test_parse_table_valid():
    """Test parsing a valid table."""
    lines = [
        "| Name | Age |",
        "|------|-----|",
        "| Alice | 30 |",
        "| Bob | 25 |",
    ]
    result = parse_table(lines, 0, "test.md")
    
    assert result is not None
    assert result["headers"] == ["Name", "Age"]
    assert result["row_count"] == 2
    assert result["column_count"] == 2
    assert result["rows_preview"] == [["Alice", "30"], ["Bob", "25"]]
    assert result["alignment"] == ["left", "left"]


def test_parse_table_with_caption():
    """Test parsing table with caption."""
    lines = [
        "User Information",
        "| Name | Age |",
        "|------|-----|",
        "| Alice | 30 |",
    ]
    result = parse_table(lines, 1, "test.md")
    
    assert result is not None
    assert result["caption"] == "User Information"


def test_parse_table_no_caption():
    """Test parsing table without caption."""
    lines = [
        "| Name | Age |",
        "|------|-----|",
        "| Alice | 30 |",
    ]
    result = parse_table(lines, 0, "test.md")
    
    assert result is not None
    assert result["caption"] is None


def test_parse_table_with_alignment():
    """Test parsing table with alignment markers."""
    lines = [
        "| Left | Center | Right |",
        "|:-----|:------:|------:|",
        "| A | B | C |",
    ]
    result = parse_table(lines, 0, "test.md")
    
    assert result is not None
    assert result["alignment"] == ["left", "center", "right"]


def test_parse_table_insufficient_lines():
    """Test parsing table with insufficient lines."""
    lines = ["| Header |"]
    result = parse_table(lines, 0, "test.md")
    assert result is None


def test_parse_table_no_separator():
    """Test parsing table without separator."""
    lines = [
        "| Header |",
        "| Data |",
    ]
    result = parse_table(lines, 0, "test.md")
    assert result is None


def test_parse_table_empty_data():
    """Test parsing table with header but no data rows."""
    lines = [
        "| Header |",
        "|--------|",
    ]
    result = parse_table(lines, 0, "test.md")
    
    assert result is not None
    assert result["row_count"] == 0
    assert result["rows_preview"] == []


def test_parse_table_line_numbers():
    """Test parsing table line numbers."""
    lines = [
        "Some text",
        "| Name | Age |",
        "|------|-----|",
        "| Alice | 30 |",
        "More text",
    ]
    result = parse_table(lines, 1, "test.md")
    
    assert result is not None
    assert result["start_line"] == 2  # 1-based
    assert result["end_line"] == 4
