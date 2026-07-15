"""Unit tests for openapi_parser.splitter — semantic chunking.

Covers:
- semantic chunk generation via a monkeypatched SemanticSplitterNodeParser
- metadata and spec_source preserved in chunks
- chunk ordering and stable chunk IDs
- empty documents are skipped
- multiple documents produce combined chunk list
- missing OPENAI_API_KEY raises RuntimeError
"""
from __future__ import annotations

import pytest


_MOCK_PATH = "llama_index.core.node_parser.SemanticSplitterNodeParser"


def _make_fake_splitter(mapping):
    """Return a fake SemanticSplitterNodeParser class.

    *mapping* is a list of strings (always returned) or a dict mapping
    document text -> list of strings.
    """

    class FakeSplitter:
        def __init__(self, *args, **kwargs):
            pass

        def split(self, obj):
            text = obj if isinstance(obj, str) else getattr(obj, "text", "")
            out = mapping.get(text, []) if isinstance(mapping, dict) else list(mapping)
            return [type("N", (), {"text": t})() for t in out]

    return FakeSplitter


def _make_doc(text: str, file_path: str = "/spec.yaml"):
    try:
        from llama_index.core import Document
        return Document(text=text, metadata={"file_path": file_path})
    except ImportError:
        try:
            from llama_index import Document  # type: ignore
            return Document(text=text, extra_info={"file_path": file_path})
        except ImportError:
            pytest.skip("llama_index not available")


def _patch_settings(monkeypatch, api_key: str = "test-key"):
    class FakeSettings:
        openai_api_key = api_key
        embed_model_name = "text-embedding-3-small"
        embed_base_url = None

    monkeypatch.setattr("shared.config.settings", FakeSettings())


# ---------------------------------------------------------------------------
# Chunk generation
# ---------------------------------------------------------------------------

class TestSplitDocuments:
    def test_chunks_generated_with_text(self, monkeypatch):
        _patch_settings(monkeypatch)
        monkeypatch.setattr(_MOCK_PATH, _make_fake_splitter(["part one", "part two"]))

        from openapi_parser.splitter import split_documents

        doc = _make_doc("some yaml content", "/api/spec.yaml")
        chunks = split_documents([doc])

        assert len(chunks) == 2
        assert chunks[0]["text"] == "part one"
        assert chunks[1]["text"] == "part two"

    def test_spec_source_and_metadata_preserved(self, monkeypatch):
        _patch_settings(monkeypatch)
        monkeypatch.setattr(_MOCK_PATH, _make_fake_splitter(["chunk"]))

        from openapi_parser.splitter import split_documents

        doc = _make_doc("yaml", "/path/to/payments.yaml")
        chunks = split_documents([doc])

        assert chunks[0]["spec_source"] == "/path/to/payments.yaml"
        assert chunks[0]["source_document_path"] == "/path/to/payments.yaml"
        assert chunks[0]["metadata"]["file_path"] == "/path/to/payments.yaml"

    def test_chunk_order_is_one_based(self, monkeypatch):
        _patch_settings(monkeypatch)
        monkeypatch.setattr(_MOCK_PATH, _make_fake_splitter(["a", "b", "c"]))

        from openapi_parser.splitter import split_documents

        chunks = split_documents([_make_doc("text")])
        assert [c["chunk_order"] for c in chunks] == [1, 2, 3]

    def test_stable_chunk_ids_across_runs(self, monkeypatch):
        _patch_settings(monkeypatch)
        monkeypatch.setattr(_MOCK_PATH, _make_fake_splitter(["hello", "world"]))

        from openapi_parser import splitter as splitter_mod

        doc = _make_doc("content", "/spec.yaml")
        chunks1 = splitter_mod.split_documents([doc])
        chunks2 = splitter_mod.split_documents([doc])

        assert [c["chunk_id"] for c in chunks1] == [c["chunk_id"] for c in chunks2]

    def test_chunk_id_uses_file_stem(self, monkeypatch):
        _patch_settings(monkeypatch)
        monkeypatch.setattr(_MOCK_PATH, _make_fake_splitter(["data"]))

        from openapi_parser.splitter import split_documents

        doc = _make_doc("text", "/specs/payments.yaml")
        chunks = split_documents([doc])

        assert chunks[0]["chunk_id"].startswith("payments_")

    def test_empty_document_skipped(self, monkeypatch):
        _patch_settings(monkeypatch)
        monkeypatch.setattr(_MOCK_PATH, _make_fake_splitter(["should-not-appear"]))

        from openapi_parser.splitter import split_documents

        doc = _make_doc("   \n\t  ", "/empty.yaml")
        chunks = split_documents([doc])

        assert chunks == []

    def test_multiple_documents_combined(self, monkeypatch):
        _patch_settings(monkeypatch)
        mapping = {"doc one": ["c1"], "doc two": ["c2", "c3"]}
        monkeypatch.setattr(_MOCK_PATH, _make_fake_splitter(mapping))

        from openapi_parser.splitter import split_documents

        doc1 = _make_doc("doc one", "/a.yaml")
        doc2 = _make_doc("doc two", "/b.yaml")
        chunks = split_documents([doc1, doc2])

        assert len(chunks) == 3
        assert chunks[0]["spec_source"] == "/a.yaml"
        assert chunks[1]["spec_source"] == "/b.yaml"
        assert chunks[2]["spec_source"] == "/b.yaml"

    def test_no_api_key_raises_runtime_error(self, monkeypatch):
        _patch_settings(monkeypatch, api_key="")
        monkeypatch.setattr(_MOCK_PATH, _make_fake_splitter([]))

        from openapi_parser.splitter import split_documents

        with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
            split_documents([_make_doc("text")])
