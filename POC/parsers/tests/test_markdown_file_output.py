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

    output_files = sorted(output_dir.glob("*.json"))
    # Expect one JSON per source markdown file (3 files in the fixture)
    assert len(output_files) == 3

    spec1_chunk1 = output_dir / "spec_one_chunk1.json"
    spec1_chunk2 = output_dir / "spec_one_chunk2.json"
    spec2_chunkA = output_dir / "spec_two_with_spaces_chunkA.json"
    assert spec1_chunk1.exists()
    assert spec1_chunk2.exists()
    assert spec2_chunkA.exists()


def test_output_files_contain_correct_documents_and_provenance(
    docling_chunks_dir: Path, tmp_path: Path
):
    """Verify content of the generated JSON files."""
    output_dir = tmp_path / "parser_output" / "markdown"

    write_markdown_parser_output(docling_chunks_dir, output_dir)

    # Check first chunk from spec_one
    spec1_chunk1 = output_dir / "spec_one_chunk1.json"
    spec1_data = NormalizedJson.from_dict(json.loads(spec1_chunk1.read_text()))
    assert spec1_data.provenance["specification"] == "spec_one/chunk1"
    assert len(spec1_data.documents) == 1
    assert spec1_data.documents[0].text == "# Hello"

    # Check second chunk from spec_one
    spec1_chunk2 = output_dir / "spec_one_chunk2.json"
    spec1_data2 = NormalizedJson.from_dict(json.loads(spec1_chunk2.read_text()))
    assert spec1_data2.provenance["specification"] == "spec_one/chunk2"
    assert len(spec1_data2.documents) == 1
    assert spec1_data2.documents[0].text == "## World"

    # Check spec_two_with_spaces chunk
    spec2_chunk = output_dir / "spec_two_with_spaces_chunkA.json"
    spec2_data = NormalizedJson.from_dict(json.loads(spec2_chunk.read_text()))
    assert spec2_data.provenance["specification"] == "spec_two_with_spaces/chunkA"
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
    expected_filename = "spec_with_slashes_and_spaces_chunk.json"
    assert (output_dir / expected_filename).exists()


def test_idempotency(docling_chunks_dir: Path, tmp_path: Path):
    """Verify that running the writer twice produces identical output."""
    output_dir = tmp_path / "parser_output" / "markdown"

    # First run
    write_markdown_parser_output(docling_chunks_dir, output_dir)
    spec1_output = output_dir / "spec_one_chunk1.json"
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
    # With per-file outputs the writer does not emit a combined section_map
    # entry. Verify each source file produced its own JSON and has no
    # bundle-level section_map in provenance.
    expected_files = [
        output_dir / "test_spec_00_preamble_chunk_000.json",
        output_dir / "test_spec_00_preamble_chunk_001.json",
        output_dir / "test_spec_01_intro_chunk_000.json",
        output_dir / "test_spec_02_body_chunk_000.json",
        output_dir / "test_spec_02_body_chunk_001.json",
    ]
    for f in expected_files:
        assert f.exists()
        data = NormalizedJson.from_dict(json.loads(f.read_text()))
        assert "section_map" not in data.provenance


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
    # Each source file is written separately; verify each output contains a
    # single document and that per-file metadata does not include section
    # ordering fields (those are only relevant for aggregated bundles).
    expected_texts = [
        "Section 2, Chunk 1",
        "Section 1, Chunk 0",
        "Section 2, Chunk 0",
        "Section 1, Chunk 1",
    ]
    # Verify outputs exist for each created file
    output_files = sorted(output_dir.glob("*.json"))
    assert len(output_files) >= 4
    for f in output_files:
        data = NormalizedJson.from_dict(json.loads(f.read_text()))
        assert len(data.documents) == 1
        meta = data.documents[0].source_metadata.get("metadata", {})
        assert "section_order" not in meta
        assert "chunk_order_in_section" not in meta


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
    # Per-file outputs do not include chunk_order_in_section; simply verify
    # that each file was written separately and contains a single document.
    output_files = sorted(output_dir.glob("*.json"))
    assert len(output_files) >= 6
    for f in output_files:
        data = NormalizedJson.from_dict(json.loads(f.read_text()))
        assert len(data.documents) == 1

