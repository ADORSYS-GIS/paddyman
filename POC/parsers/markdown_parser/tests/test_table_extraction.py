"""Unit tests for markdown table extraction."""
import pytest
from markdown_parser.structure import (
    _extract_tables,
    _parse_table_lines,
    _parse_table_row,
    _is_separator_row,
)


class TestExtractTables:
    """Test _extract_tables function."""

    def test_simple_two_column_table(self):
        """Test extraction of a simple 2-column table."""
        text = """
| Name  | Age |
|-------|-----|
| Alice | 30  |
| Bob   | 25  |
"""
        result = _extract_tables(text)
        assert len(result) == 1
        table = result[0]
        assert table["headers"] == ["Name", "Age"]
        assert table["rows"] == [["Alice", "30"], ["Bob", "25"]]

    def test_three_column_table(self):
        """Test extraction of a 3-column table."""
        text = """
| Version | Change/Note        | Approved           |
|---------|--------------------|--------------------|
| 1.0     | First publication | openFinance TF     |
| 1.1     | Minor updates     | Technical Committee|
"""
        result = _extract_tables(text)
        assert len(result) == 1
        table = result[0]
        assert table["headers"] == ["Version", "Change/Note", "Approved"]
        assert len(table["rows"]) == 2
        assert table["rows"][0] == ["1.0", "First publication", "openFinance TF"]
        assert table["rows"][1] == ["1.1", "Minor updates", "Technical Committee"]

    def test_table_with_alignment_markers(self):
        """Test table with column alignment markers (:---, ---:, :---:)."""
        text = """
| Left | Center | Right |
|:-----|:------:|------:|
| A    | B      | C     |
"""
        result = _extract_tables(text)
        assert len(result) == 1
        table = result[0]
        assert table["headers"] == ["Left", "Center", "Right"]
        assert table["rows"] == [["A", "B", "C"]]

    def test_no_tables_returns_empty_list(self):
        """Test that text without tables returns empty list."""
        text = "# Heading\n\nSome paragraph text without any tables."
        result = _extract_tables(text)
        assert result == []

    def test_two_separate_tables(self):
        """Test extraction of two separate tables."""
        text = """
| Table1 |
|--------|
| Data1  |

Some text between tables

| Table2 | Col2 |
|--------|------|
| Data2  | Val2 |
"""
        result = _extract_tables(text)
        assert len(result) == 2
        assert result[0]["headers"] == ["Table1"]
        assert result[0]["rows"] == [["Data1"]]
        assert result[1]["headers"] == ["Table2", "Col2"]
        assert result[1]["rows"] == [["Data2", "Val2"]]

    def test_table_with_empty_cells(self):
        """Test table with empty cells."""
        text = """
| Col1 | Col2 | Col3 |
|------|------|------|
| A    |      | C    |
|      | B    |      |
"""
        result = _extract_tables(text)
        assert len(result) == 1
        table = result[0]
        assert table["headers"] == ["Col1", "Col2", "Col3"]
        assert table["rows"] == [["A", "", "C"], ["", "B", ""]]

    def test_malformed_table_no_separator(self):
        """Test that table without separator is not extracted."""
        text = """
| Header |
| Data   |
"""
        result = _extract_tables(text)
        assert result == []

    def test_table_only_header_and_separator(self):
        """Test table with header and separator but no data rows."""
        text = """
| Header1 | Header2 |
|---------|---------|
"""
        result = _extract_tables(text)
        assert len(result) == 1
        table = result[0]
        assert table["headers"] == ["Header1", "Header2"]
        assert table["rows"] == []

    def test_table_with_pipes_in_content(self):
        """Test table where cell content contains text (not nested pipes)."""
        text = """
| Operator | Description |
|----------|-------------|
| AND      | Logical and |
| OR       | Logical or  |
"""
        result = _extract_tables(text)
        assert len(result) == 1
        table = result[0]
        assert table["headers"] == ["Operator", "Description"]
        assert table["rows"][0] == ["AND", "Logical and"]

    def test_table_mixed_with_other_content(self):
        """Test table mixed with headings and paragraphs."""
        text = """
# Title

Some introduction text.

| Name | Value |
|------|-------|
| Foo  | 123   |

More text after table.
"""
        result = _extract_tables(text)
        assert len(result) == 1
        table = result[0]
        assert table["headers"] == ["Name", "Value"]
        assert table["rows"] == [["Foo", "123"]]

    def test_table_with_mismatched_column_counts(self):
        """Test table where rows have different column counts - should be normalized."""
        text = """
| Col1 | Col2 | Col3 |
|------|------|------|
| A    | B    |
| X    | Y    | Z    | Extra |
"""
        result = _extract_tables(text)
        assert len(result) == 1
        table = result[0]
        assert table["headers"] == ["Col1", "Col2", "Col3"]
        # First row should be padded
        assert table["rows"][0] == ["A", "B", ""]
        # Second row should be truncated
        assert table["rows"][1] == ["X", "Y", "Z"]


class TestParseTableLines:
    """Test _parse_table_lines helper function."""

    def test_valid_table_buffer(self):
        """Test parsing a valid table buffer."""
        lines = [
            "| Header1 | Header2 |",
            "|---------|---------|",
            "| Data1   | Data2   |",
        ]
        result = _parse_table_lines(lines)
        assert result is not None
        assert result["headers"] == ["Header1", "Header2"]
        assert result["rows"] == [["Data1", "Data2"]]

    def test_insufficient_lines(self):
        """Test that single line returns None."""
        lines = ["| Header |"]
        result = _parse_table_lines(lines)
        assert result is None

    def test_invalid_separator(self):
        """Test that invalid separator returns None."""
        lines = [
            "| Header |",
            "| NotSep |",
        ]
        result = _parse_table_lines(lines)
        assert result is None


class TestParseTableRow:
    """Test _parse_table_row helper function."""

    def test_standard_row(self):
        """Test parsing a standard table row."""
        line = "| Cell1 | Cell2 | Cell3 |"
        result = _parse_table_row(line)
        assert result == ["Cell1", "Cell2", "Cell3"]

    def test_row_without_outer_pipes(self):
        """Test row without leading/trailing pipes."""
        line = "Cell1 | Cell2 | Cell3"
        result = _parse_table_row(line)
        assert result == ["Cell1", "Cell2", "Cell3"]

    def test_row_with_extra_whitespace(self):
        """Test that whitespace is stripped from cells."""
        line = "|  Cell1  |   Cell2   |  Cell3  |"
        result = _parse_table_row(line)
        assert result == ["Cell1", "Cell2", "Cell3"]

    def test_empty_cells(self):
        """Test parsing row with empty cells."""
        line = "| Cell1 |  | Cell3 |"
        result = _parse_table_row(line)
        assert result == ["Cell1", "", "Cell3"]

    def test_invalid_row_no_pipes(self):
        """Test that row without pipes returns None."""
        line = "Not a table row"
        result = _parse_table_row(line)
        assert result is None

    def test_empty_line(self):
        """Test that empty line returns None."""
        line = ""
        result = _parse_table_row(line)
        assert result is None


class TestIsSeparatorRow:
    """Test _is_separator_row helper function."""

    def test_simple_separator(self):
        """Test simple separator row."""
        line = "|---|---|"
        assert _is_separator_row(line) is True

    def test_separator_with_whitespace(self):
        """Test separator with whitespace."""
        line = "| --- | --- | --- |"
        assert _is_separator_row(line) is True

    def test_left_aligned_separator(self):
        """Test left-aligned separator (:---)."""
        line = "|:---|:---|"
        assert _is_separator_row(line) is True

    def test_right_aligned_separator(self):
        """Test right-aligned separator (---:)."""
        line = "|---:|---:|"
        assert _is_separator_row(line) is True

    def test_center_aligned_separator(self):
        """Test center-aligned separator (:---:)."""
        line = "|:---:|:---:|"
        assert _is_separator_row(line) is True

    def test_mixed_alignment_separator(self):
        """Test separator with mixed alignment."""
        line = "|:---|:---:|---:|"
        assert _is_separator_row(line) is True

    def test_longer_separator(self):
        """Test separator with more dashes."""
        line = "|---------|----------|"
        assert _is_separator_row(line) is True

    def test_invalid_separator_no_dashes(self):
        """Test that row without dashes is not a separator."""
        line = "| abc | def |"
        assert _is_separator_row(line) is False

    def test_invalid_separator_empty(self):
        """Test that empty line is not a separator."""
        line = ""
        assert _is_separator_row(line) is False

    def test_invalid_separator_no_pipes(self):
        """Test that line without pipes is not a separator."""
        line = "------"
        assert _is_separator_row(line) is False
