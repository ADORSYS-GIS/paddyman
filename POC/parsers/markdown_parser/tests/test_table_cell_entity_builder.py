"""Unit tests for TableCell entity extraction."""
from __future__ import annotations

from markdown_parser.table_cell_entity_builder import create_table_cell_entities


def _make_table(
    table_id: str,
    headers: list[str],
    rows: list[list[str]],
    file_path: str = "spec.md",
    start_line: int = 10,
) -> dict:
    return {
        "id": table_id,
        "type": "Table",
        "properties": {
            "headers": headers,
            "rows": rows,
            "file_path": file_path,
            "start_line": start_line,
        },
    }
class TestCreateTableCellEntities:
    """Tests for create_table_cell_entities."""

    def test_simple_2x2_table(self):
        table = _make_table("t1", ["A", "B"], [["a1", "b1"]])
        cells = create_table_cell_entities([table])
        assert len(cells) == 4  # 2 header + 2 data

    def test_header_cells_have_is_header_true(self):
        table = _make_table("t1", ["Name", "Value"], [])
        cells = create_table_cell_entities([table])
        header_cells = [c for c in cells if c["properties"]["is_header"]]
        assert len(header_cells) == 2
        contents = {c["properties"]["content"] for c in header_cells}
        assert contents == {"Name", "Value"}

    def test_data_cells_have_is_header_false(self):
        table = _make_table("t1", ["A"], [["val1"], ["val2"]])
        cells = create_table_cell_entities([table])
        data_cells = [c for c in cells if not c["properties"]["is_header"]]
        assert len(data_cells) == 2
        assert all(not c["properties"]["is_header"] for c in data_cells)

    def test_row_column_indices_zero_based(self):
        """Header is row 0; data rows start at row 1; columns are 0-based."""
        table = _make_table("t1", ["X", "Y"], [["a", "b"]])
        cells = create_table_cell_entities([table])

        header_cells = sorted(
            [c for c in cells if c["properties"]["is_header"]],
            key=lambda c: c["properties"]["column"],
        )
        assert header_cells[0]["properties"]["row"] == 0
        assert header_cells[0]["properties"]["column"] == 0
        assert header_cells[1]["properties"]["column"] == 1

        data_cells = sorted(
            [c for c in cells if not c["properties"]["is_header"]],
            key=lambda c: c["properties"]["column"],
        )
        assert data_cells[0]["properties"]["row"] == 1

    def test_column_header_associated(self):
        """Data cells carry their column header name."""
        table = _make_table("t1", ["Param", "Required"], [["X-ID", "true"]])
        cells = create_table_cell_entities([table])

        data_cells = {
            c["properties"]["column"]: c
            for c in cells
            if not c["properties"]["is_header"]
        }
        assert data_cells[0]["properties"]["column_header"] == "Param"
        assert data_cells[1]["properties"]["column_header"] == "Required"

    def test_empty_cell_content_type(self):
        table = _make_table("t1", ["A"], [[""]]) 
        cells = create_table_cell_entities([table])
        data = [c for c in cells if not c["properties"]["is_header"]]
        assert data[0]["properties"]["content_type"] == "empty"
        assert data[0]["properties"]["content"] == ""

    def test_cell_content_preserved_exactly(self):
        text = "X-Request-ID"
        table = _make_table("t1", ["Param"], [[text]])
        cells = create_table_cell_entities([table])
        data = [c for c in cells if not c["properties"]["is_header"]]
        assert data[0]["properties"]["content"] == text

    def test_link_detection(self):
        """Cells with [text](url) links have content_type='text_with_link'."""
        table = _make_table("t1", ["Ref"], [["See [Section 4.2](#s4) for details"]])
        cells = create_table_cell_entities([table])

        data = [c for c in cells if not c["properties"]["is_header"]]
        assert data[0]["properties"]["content_type"] == "text_with_link"
        assert "Section 4.2" in data[0]["properties"]["links"]

    def test_code_cell_detection(self):
        """Backtick-wrapped content has content_type='code'."""
        table = _make_table("t1", ["Example"], [["`application/json`"]])
        cells = create_table_cell_entities([table])

        data = [c for c in cells if not c["properties"]["is_header"]]
        assert data[0]["properties"]["content_type"] == "code"

    def test_entity_structure(self):
        """TableCell entities have required top-level fields."""
        table = _make_table("t1", ["A"], [])
        cells = create_table_cell_entities([table])

        for cell in cells:
            assert cell["type"] == "TableCell"
            assert "id" in cell
            assert "name" in cell
            assert "source" in cell

    def test_source_format(self):
        """Source follows expected format."""
        table = _make_table("t1", ["A"], [], file_path="spec.md", start_line=50)
        cells = create_table_cell_entities([table])

        assert cells[0]["source"].startswith("markdown_parser:spec.md:table:50:cell:")

    def test_table_id_in_cell_properties(self):
        """Each cell carries its parent table_id."""
        table = _make_table("my-table-id", ["A"], [["x"]])
        cells = create_table_cell_entities([table])

        for cell in cells:
            assert cell["properties"]["table_id"] == "my-table-id"

    def test_multiple_tables_independent(self):
        """Cells from different tables are extracted independently."""
        t1 = _make_table("t1", ["A"], [["a"]])
        t2 = _make_table("t2", ["B", "C"], [["b", "c"]])
        cells = create_table_cell_entities([t1, t2])

        t1_cells = [c for c in cells if c["properties"]["table_id"] == "t1"]
        t2_cells = [c for c in cells if c["properties"]["table_id"] == "t2"]
        assert len(t1_cells) == 2   # 1 header + 1 data
        assert len(t2_cells) == 4   # 2 header + 2 data

    def test_no_tables_returns_empty(self):
        """Empty table list yields no cells."""
        assert create_table_cell_entities([]) == []
