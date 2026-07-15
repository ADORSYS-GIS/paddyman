"""Unit tests for the markdown parser document ingestion.

Tests cover:
- loading from the configured path via `shared.config.settings` fallback
- multiple documents returned
- empty directory handling
- invalid (non-existent) directory handling
- document metadata generation
"""
from __future__ import annotations

from pathlib import Path

import pytest


def test_load_documents_uses_settings_and_reads_md_files(monkeypatch, tmp_path: Path):
    # Create markdown files
    (tmp_path / "spec1_clean.md").write_text("# Spec1\ncontent", encoding="utf-8")
    (tmp_path / "spec2_clean.md").write_text("# Spec2\ncontent", encoding="utf-8")

    # Fake settings object with markdown_spec_dir pointing to tmp_path
    class FakeSettings:
        markdown_spec_dir = tmp_path

    monkeypatch.setattr("shared.config.settings", FakeSettings())

    from markdown_parser.reader import load_documents

    docs = load_documents(None)
    assert isinstance(docs, list)
    assert len(docs) == 2
    assert all(isinstance(d, dict) for d in docs)
    assert all("text" in d and "document_id" in d for d in docs)


def test_load_documents_strips_clean_suffix(monkeypatch, tmp_path: Path):
    (tmp_path / "my_spec_clean.md").write_text("# Content", encoding="utf-8")

    class FakeSettings:
        markdown_spec_dir = tmp_path

    monkeypatch.setattr("shared.config.settings", FakeSettings())

    from markdown_parser.reader import load_documents

    docs = load_documents(None)
    assert len(docs) == 1
    assert docs[0]["document_id"] == "my_spec"
    assert docs[0]["file_name"] == "my_spec_clean.md"


def test_load_multiple_documents(monkeypatch, tmp_path: Path):
    (tmp_path / "doc_a.md").write_text("first", encoding="utf-8")
    (tmp_path / "doc_b.md").write_text("second", encoding="utf-8")

    class FakeSettings:
        markdown_spec_dir = tmp_path

    monkeypatch.setattr("shared.config.settings", FakeSettings())

    from markdown_parser.reader import load_documents

    docs = load_documents(None)
    assert len(docs) == 2
    doc_ids = sorted([d["document_id"] for d in docs])
    assert doc_ids == ["doc_a", "doc_b"]


def test_empty_directory_returns_empty(monkeypatch, tmp_path: Path):
    class FakeSettings:
        markdown_spec_dir = tmp_path

    monkeypatch.setattr("shared.config.settings", FakeSettings())

    from markdown_parser.reader import load_documents

    docs = load_documents(None)
    assert docs == []


def test_nonexistent_directory_returns_empty(monkeypatch):
    class FakeSettings:
        markdown_spec_dir = Path("/nonexistent/path")

    monkeypatch.setattr("shared.config.settings", FakeSettings())

    from markdown_parser.reader import load_documents

    docs = load_documents(None)
    assert docs == []


def test_nonexistent_directory_returns_empty(tmp_path: Path):
    missing = tmp_path / "does-not-exist"

    from markdown_parser.reader import load_documents

    docs = load_documents(missing)
    assert docs == []


def test_metadata_preserved(monkeypatch, tmp_path: Path):
    class FakeSettings:
        docling_chunks_dir = tmp_path

    monkeypatch.setattr("shared.config.settings", FakeSettings())

    try:
        from llama_index import Document as LlamaDocument  # type: ignore
    except Exception:
        pytest.skip("llama_index not available")

    meta = {"file_path": "doc.md", "source": "berlin_group"}
    fake_docs = [LlamaDocument(text="x", extra_info=meta)]
    monkeypatch.setattr("llama_index.SimpleDirectoryReader", _make_fake_reader(fake_docs))

    from markdown_parser.reader import load_documents

    docs = load_documents(None)
    assert len(docs) == 1
    doc = docs[0]
    # LlamaIndex Document implementations may expose metadata via
    # `extra_info` (historical) or `metadata`. Accept either.
    if hasattr(doc, "extra_info"):
        assert doc.extra_info == meta
    elif hasattr(doc, "metadata"):
        assert doc.metadata == meta
    else:
        pytest.fail("Document has no metadata attribute")
