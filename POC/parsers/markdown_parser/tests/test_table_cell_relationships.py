"""Unit tests for TableCell relationship building."""
from __future__ import annotations

from markdown_parser.table_cell_entity_builder import (
    create_table_cell_entities,
    create_table_cell_relationships,
)


def _make_table(tid: str, headers: list[str], rows: list[list[str]]) -> dict:
    return {
        "id": tid,
        "type": "Table",
        "properties": {
            "headers": headers,
            "rows": rows,
            "file_path": "spec.md",
            "start_line": 1,
        },
    }


class TestTableCellRelationships:
    """Tests for create_table_cell_relationships."""

    def test_has_cell_created_for_each_cell(self):
        """HAS_CELL relationship created from table to every cell."""
        table = _make_table("t1", ["A", "B"], [["a", "b"]])
        cells = create_table_cell_entities([table])
        rels = create_table_cell_relationships([table], cells)

        has_cell = [r for r in rels if r["type"] == "HAS_CELL"]
        assert len(has_cell) == len(cells)  # 4 cells total
        for rel in has_cell:
            assert rel["source_entity_id"] == "t1"

    def test_in_row_links_cells_sequentially(self):
        """IN_ROW links adjacent cells within each row."""
        table = _make_table("t1", ["A", "B", "C"], [])
        cells = create_table_cell_entities([table])
        rels = create_table_cell_relationships([table], cells)

        in_row = [r for r in rels if r["type"] == "IN_ROW"]
        # 3 columns → 2 IN_ROW links per row; header row only here
        assert len(in_row) == 2

    def test_in_column_links_cells_sequentially(self):
        """IN_COLUMN links adjacent cells within each column."""
        table = _make_table("t1", ["A"], [["r1"], ["r2"], ["r3"]])
        cells = create_table_cell_entities([table])
        rels = create_table_cell_relationships([table], cells)

        in_col = [r for r in rels if r["type"] == "IN_COLUMN"]
        # 1 column with 4 cells (header + 3 data) → 3 IN_COLUMN links
        assert len(in_col) == 3

    def test_relationship_structure(self):
        """Each relationship has required fields."""
        table = _make_table("t1", ["X"], [["v"]])
        cells = create_table_cell_entities([table])
        rels = create_table_cell_relationships([table], cells)

        for rel in rels:
            assert "id" in rel
            assert "source_entity_id" in rel
            assert "target_entity_id" in rel
            assert "type" in rel

    def test_multiple_tables_isolated(self):
        """Relationships for each table reference only that table's cells."""
        t1 = _make_table("t1", ["A"], [["x"]])
        t2 = _make_table("t2", ["B"], [["y"]])
        cells = create_table_cell_entities([t1, t2])
        rels = create_table_cell_relationships([t1, t2], cells)

        t1_has_cell = [
            r for r in rels
            if r["type"] == "HAS_CELL" and r["source_entity_id"] == "t1"
        ]
        t2_has_cell = [
            r for r in rels
            if r["type"] == "HAS_CELL" and r["source_entity_id"] == "t2"
        ]
        assert len(t1_has_cell) == 2  # 1 header + 1 data
        assert len(t2_has_cell) == 2

    def test_no_in_row_for_single_column(self):
        """Single-column tables have no IN_ROW relationships."""
        table = _make_table("t1", ["Only"], [["v1"], ["v2"]])
        cells = create_table_cell_entities([table])
        rels = create_table_cell_relationships([table], cells)

        assert not any(r["type"] == "IN_ROW" for r in rels)

    def test_empty_tables_produce_no_rels(self):
        """Table with no headers or rows produces no relationships."""
        table = _make_table("t1", [], [])
        cells = create_table_cell_entities([table])
        rels = create_table_cell_relationships([table], cells)

        assert rels == []

    def test_no_tables_returns_empty(self):
        """Empty inputs yield empty output."""
        assert create_table_cell_relationships([], []) == []
