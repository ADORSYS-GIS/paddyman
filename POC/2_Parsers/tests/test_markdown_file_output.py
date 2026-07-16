"""Tests for the markdown per-spec output writer."""
import json
import sys
from pathlib import Path

import pytest
from shared.models import NormalizedJson

_POC_ROOT = Path(__file__).resolve().parents[2]
_PARSERS_ROOT = _POC_ROOT / "2_Parsers"
for _path in (str(_POC_ROOT), str(_PARSERS_ROOT)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from markdown_file_output import write_markdown_parser_output


@pytest.fixture
def docling_chunks_dir(tmp_path: Path) -> Path:
    """Create a dummy docling chunks directory."""
    chunks_dir = tmp_path / "docling_chunks"
    spec1_dir = chunks_dir / "spec_one"
    spec2_dir = chunks_dir / "spec_two_with_spaces"
    spec1_dir.mkdir(parents=True)
    spec2_dir.mkdir(parents=True)

    (spec1_dir / "chunk1.md").write_text("# Hello")
    (spec1_dir / "chunk2.md").write_text("## World")
    (spec2_dir / "chunkA.md").write_text("### Foo")

    return chunks_dir


def test_write_markdown_parser_output_creates_one_file_per_spec(
    docling_chunks_dir: Path, tmp_path: Path
):
    """Verify that one JSON file is created for each specification."""
    output_dir = tmp_path / "parser_output" / "markdown"

    write_markdown_parser_output(docling_chunks_dir, output_dir)

    output_files = list(output_dir.glob("*.json"))
    assert len(output_files) == 2

    spec1_output = output_dir / "spec_one.json"
    spec2_output = output_dir / "spec_two_with_spaces.json"
    assert spec1_output.exists()
    assert spec2_output.exists()


def test_output_files_contain_correct_documents_and_provenance(
    docling_chunks_dir: Path, tmp_path: Path
):
    """Verify content of the generated JSON files."""
    output_dir = tmp_path / "parser_output" / "markdown"

    write_markdown_parser_output(docling_chunks_dir, output_dir)

    # Check spec_one.json
    spec1_output = output_dir / "spec_one.json"
    spec1_data = NormalizedJson.from_dict(json.loads(spec1_output.read_text()))
    assert spec1_data.provenance["specification"] == "spec_one"
    assert len(spec1_data.documents) == 2
    assert spec1_data.documents[0].text == "# Hello"
    assert spec1_data.documents[1].text == "## World"

    # Check spec_two_with_spaces.json
    spec2_output = output_dir / "spec_two_with_spaces.json"
    spec2_data = NormalizedJson.from_dict(json.loads(spec2_output.read_text()))
    assert spec2_data.provenance["specification"] == "spec_two_with_spaces"
    assert len(spec2_data.documents) == 1
    assert spec2_data.documents[0].text == "### Foo"


def test_filename_is_sanitized(tmp_path: Path):
    """Verify that specification names are sanitized for filenames."""
    docling_chunks_dir = tmp_path / "docling_chunks"
    spec_dir = docling_chunks_dir / "spec/with/slashes and spaces"
    spec_dir.mkdir(parents=True)
    (spec_dir / "chunk.md").write_text("# Test")

    output_dir = tmp_path / "parser_output" / "markdown"
    write_markdown_parser_output(docling_chunks_dir, output_dir)

    expected_filename = "spec_with_slashes_and_spaces.json"
    assert (output_dir / expected_filename).exists()


def test_idempotency(docling_chunks_dir: Path, tmp_path: Path):
    """Verify that running the writer twice produces identical output."""
    output_dir = tmp_path / "parser_output" / "markdown"

    # First run
    write_markdown_parser_output(docling_chunks_dir, output_dir)
    spec1_output = output_dir / "spec_one.json"
    content1 = spec1_output.read_text()
    mtime1 = spec1_output.stat().st_mtime

    # Second run
    write_markdown_parser_output(docling_chunks_dir, output_dir)
    content2 = spec1_output.read_text()
    mtime2 = spec1_output.stat().st_mtime

    assert content1 == content2
    # Timestamps might be different, so we don't assert mtime1 == mtime2
    # The content check is sufficient for idempotency in terms of output.


def test_section_map_included_in_provenance(tmp_path: Path):
    """Verify that section_map is included in the provenance."""
    # Arrange
    docling_chunks_dir = tmp_path / "docling_chunks"
    spec_dir = docling_chunks_dir / "test_spec"
    spec_dir.mkdir(parents=True)
    
    # Create files with section prefixes
    (spec_dir / "00_preamble_chunk_000.md").write_text("# Preamble")
    (spec_dir / "00_preamble_chunk_001.md").write_text("## More preamble")
    (spec_dir / "01_intro_chunk_000.md").write_text("# Introduction")
    (spec_dir / "02_body_chunk_000.md").write_text("# Body")
    (spec_dir / "02_body_chunk_001.md").write_text("## Body part 2")

    output_dir = tmp_path / "parser_output" / "markdown"

    # Act
    write_markdown_parser_output(docling_chunks_dir, output_dir)

    # Assert
    output_file = output_dir / "test_spec.json"
    data = NormalizedJson.from_dict(json.loads(output_file.read_text()))
    
    assert "section_map" in data.provenance
    section_map = data.provenance["section_map"]
    
    # Verify section_map structure
    assert len(section_map) == 3
    
    # First section: 00_preamble with 2 chunks
    assert section_map[0]["section_file_prefix"] == "00_preamble"
    assert section_map[0]["section_order"] == 0
    assert section_map[0]["chunk_count"] == 2
    
    # Second section: 01_intro with 1 chunk
    assert section_map[1]["section_file_prefix"] == "01_intro"
    assert section_map[1]["section_order"] == 1
    assert section_map[1]["chunk_count"] == 1
    
    # Third section: 02_body with 2 chunks
    assert section_map[2]["section_file_prefix"] == "02_body"
    assert section_map[2]["section_order"] == 2
    assert section_map[2]["chunk_count"] == 2


def test_documents_have_section_order_metadata(tmp_path: Path):
    """Verify that each document has section_order and chunk_order_in_section."""
    # Arrange
    docling_chunks_dir = tmp_path / "docling_chunks"
    spec_dir = docling_chunks_dir / "test_spec"
    spec_dir.mkdir(parents=True)
    
    # Create files with section prefixes in non-sorted order
    (spec_dir / "02_section2_chunk_001.md").write_text("Section 2, Chunk 1")
    (spec_dir / "01_section1_chunk_000.md").write_text("Section 1, Chunk 0")
    (spec_dir / "02_section2_chunk_000.md").write_text("Section 2, Chunk 0")
    (spec_dir / "01_section1_chunk_001.md").write_text("Section 1, Chunk 1")

    output_dir = tmp_path / "parser_output" / "markdown"

    # Act
    write_markdown_parser_output(docling_chunks_dir, output_dir)

    # Assert
    output_file = output_dir / "test_spec.json"
    data = NormalizedJson.from_dict(json.loads(output_file.read_text()))
    
    # Should have 4 documents
    assert len(data.documents) == 4
    
    # Find documents by their text content for verification
    docs_by_text = {doc.text: doc for doc in data.documents}
    
    # Section 1, Chunk 0
    doc = docs_by_text["Section 1, Chunk 0"]
    assert doc.source_metadata["section_order"] == 0
    assert doc.source_metadata["chunk_order_in_section"] == 0
    
    # Section 1, Chunk 1
    doc = docs_by_text["Section 1, Chunk 1"]
    assert doc.source_metadata["section_order"] == 0
    assert doc.source_metadata["chunk_order_in_section"] == 1
    
    # Section 2, Chunk 0
    doc = docs_by_text["Section 2, Chunk 0"]
    assert doc.source_metadata["section_order"] == 1
    assert doc.source_metadata["chunk_order_in_section"] == 0
    
    # Section 2, Chunk 1
    doc = docs_by_text["Section 2, Chunk 1"]
    assert doc.source_metadata["section_order"] == 1
    assert doc.source_metadata["chunk_order_in_section"] == 1


def test_chunk_order_resets_per_section(tmp_path: Path):
    """Verify that chunk_order_in_section resets to 0 for each section."""
    # Arrange
    docling_chunks_dir = tmp_path / "docling_chunks"
    spec_dir = docling_chunks_dir / "test_spec"
    spec_dir.mkdir(parents=True)
    
    # Create 3 sections, each with 2 chunks
    (spec_dir / "00_sec0_chunk_000.md").write_text("S0C0")
    (spec_dir / "00_sec0_chunk_001.md").write_text("S0C1")
    (spec_dir / "01_sec1_chunk_000.md").write_text("S1C0")
    (spec_dir / "01_sec1_chunk_001.md").write_text("S1C1")
    (spec_dir / "02_sec2_chunk_000.md").write_text("S2C0")
    (spec_dir / "02_sec2_chunk_001.md").write_text("S2C1")

    output_dir = tmp_path / "parser_output" / "markdown"

    # Act
    write_markdown_parser_output(docling_chunks_dir, output_dir)

    # Assert
    output_file = output_dir / "test_spec.json"
    data = NormalizedJson.from_dict(json.loads(output_file.read_text()))
    
    docs_by_text = {doc.text: doc for doc in data.documents}
    
    # Each section's first chunk should have chunk_order_in_section=0
    assert docs_by_text["S0C0"].source_metadata["chunk_order_in_section"] == 0
    assert docs_by_text["S1C0"].source_metadata["chunk_order_in_section"] == 0
    assert docs_by_text["S2C0"].source_metadata["chunk_order_in_section"] == 0
    
    # Each section's second chunk should have chunk_order_in_section=1
    assert docs_by_text["S0C1"].source_metadata["chunk_order_in_section"] == 1
    assert docs_by_text["S1C1"].source_metadata["chunk_order_in_section"] == 1
    assert docs_by_text["S2C1"].source_metadata["chunk_order_in_section"] == 1

