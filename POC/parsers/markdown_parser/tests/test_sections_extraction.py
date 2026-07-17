"""Tests for sections/headings extraction in the markdown parser."""
from pathlib import Path

from markdown_parser.parser import markdown_to_normalized_docs


def test_sections_and_locations(tmp_path: Path):
    content = """# Title

Intro paragraph.

## Subheading

- item1
- item2

| A | B |
|---|---|
| 1 | 2 |
"""
    md_file = tmp_path / "spec.md"
    md_file.write_text(content, encoding="utf-8")

    docs = markdown_to_normalized_docs(md_file)
    assert len(docs) == 1
    doc = docs[0]
    meta = doc.source_metadata["metadata"]

    assert "headings" in meta
    assert "sections" in meta
    assert isinstance(meta["sections"], list)

    # There should be one top-level heading
    top_headings = [h for h in meta["headings"] if h.get("level") == 1]
    assert len(top_headings) == 1

    # Tables should include start/end line metadata
    tables = meta.get("tables")
    assert isinstance(tables, list) and len(tables) >= 1
    tbl = tables[0]
    assert "start_line" in tbl and "end_line" in tbl

    # The table should be referenced from one of the sections' children
    referenced = False
    for s in meta["sections"]:
        for c in s.get("children", []):
            if c.get("type") == "table" and c.get("index") == 0:
                referenced = True
    assert referenced
