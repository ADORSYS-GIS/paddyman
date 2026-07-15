# Markdown Parser: Expand Table Cell Detail

## Priority

**Low**

## Goal

Extract individual table cells as entities with row/column metadata.

## Current Issue

Table entities are currently extracted, but individual cells are not exposed as separate queryable entities.

Example current table entity:

```json
{
  "type": "Table",
  "name": "Table at line 150",
  "properties": {
    "row_count": 5,
    "column_count": 3,
    "has_header": true
  }
}
```

Without cell-level entities:
- Cannot query specific table values
- Cannot extract structured data from tables
- Cannot build relationships from table content to other entities
- Cannot perform cell-level semantic search

Tables in specifications contain critical information:
- Parameter definitions (name, type, required, description)
- Status codes (code, meaning, usage)
- Error codes (code, category, description)
- Data mappings (source field, target field, transformation)

## Expected Behavior

Table cells should be extracted as `TableCell` entities:

```json
{
  "type": "TableCell",
  "name": "Cell [1,0]: Parameter Name",
  "source": "markdown_parser:nextgenpsd2_implementation_guidelines_1_3:table:150:cell:1:0",
  "properties": {
    "table_id": "uuid-of-parent-table",
    "row": 1,
    "column": 0,
    "is_header": false,
    "column_header": "Parameter Name",
    "content": "X-Request-ID",
    "content_type": "text"
  }
}
```

For cells with links:

```json
{
  "type": "TableCell",
  "name": "Cell [2,3]: Description with link",
  "properties": {
    "table_id": "uuid-of-parent-table",
    "row": 2,
    "column": 3,
    "is_header": false,
    "column_header": "Description",
    "content": "See [Section 4.2] for details",
    "content_type": "text_with_link",
    "links": ["Section 4.2"]
  }
}
```

Relationships to create:
- `HAS_CELL` from Table to TableCell
- `IN_ROW` grouping cells by row
- `IN_COLUMN` grouping cells by column

## Required Implementation

1. Create `TableCellExtractor` in `POC/2_Parsers/markdown_parser/`
2. For each table:
   - Parse table structure
   - Extract header row
   - Extract each data row
   - Build TableCell entities for each cell
3. Capture cell position (row, column)
4. Associate each cell with its column header
5. Detect cell content type (text, link, code, empty)
6. Build `HAS_CELL` relationships
7. Build row and column grouping relationships

## Validation Checklist

- [ ] Header cells extracted with `is_header: true`
- [ ] Data cells extracted with row/column position
- [ ] Column headers associated with data cells
- [ ] Cell content preserved exactly
- [ ] Empty cells handled
- [ ] Cells with links detected
- [ ] Multi-line cell content handled
- [ ] `HAS_CELL` relationships created
- [ ] Row and column indices are zero-based and accurate

## Testing Requirements

1. Unit test: simple 2x2 table
2. Unit test: table with header row
3. Unit test: table with empty cells
4. Unit test: table with links in cells
5. Unit test: table with code in cells
6. Unit test: table with multi-line cells
7. Integration test: all tables in specifications have TableCell entities
8. Integration test: verify cell count matches table dimensions

## Documentation Updates

Update `POC/2_Parsers/markdown_parser/README.md`:
- Add TableCell to entity list
- Document HAS_CELL relationship
- Document row/column indexing
- Explain content type detection
