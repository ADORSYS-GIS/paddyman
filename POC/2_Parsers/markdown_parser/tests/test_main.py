"""Unit tests for the markdown_parser pipeline entrypoint.

Tests verify orchestration, configuration loading, stage ordering, and
handling of empty/invalid inputs. All external stage behavior is monkeypatched
so tests remain fast and deterministic.
"""
from __future__ import annotations

from pathlib import Path


def test_pipeline_stage_ordering_and_counts(monkeypatch):
    calls: list[str] = []

    def fake_load(path):
        calls.append("load")
        return [{"text": "# H1\ncontent", "document_id": "doc1", "file_path": "/tmp/doc1.md"}]

    def fake_structure(docs):
        calls.append("structure")
        return [
            {
                "document_id": "doc1",
                "text": "# H1\ncontent",
                "headings": [{"level": 1, "text": "H1"}],
                "sections": [{"heading": "H1", "level": 1, "content": "# H1\ncontent"}],
                "references": {"inline": [], "definitions": [], "citations": []},
                "tables": [],
            }
        ]

    import markdown_parser.main as main_mod

    monkeypatch.setattr(main_mod, "load_documents", fake_load)
    monkeypatch.setattr(main_mod, "extract_structure_from_documents", fake_structure)

    summary = main_mod.run_pipeline("/tmp/anything")

    assert calls == ["load", "structure"]
    assert summary["documents_loaded"] == 1
    assert summary["sections_extracted"] == 1
    assert summary["headings_found"] == 1


def test_configuration_loading_uses_settings(monkeypatch, tmp_path: Path):
    # Provide a fake settings object to ensure the pipeline reads it when
    # source_dir is omitted.
    class FakeSettings:
        markdown_spec_dir = tmp_path

    import markdown_parser.main as main_mod

    recorded: dict = {}

    def fake_load(path):
        recorded["path"] = path
        return []

    monkeypatch.setattr(main_mod, "settings", FakeSettings())
    monkeypatch.setattr(main_mod, "load_documents", fake_load)

    summary = main_mod.run_pipeline(None)
    assert recorded["path"] == tmp_path
    assert summary["documents_loaded"] == 0


def test_empty_input_directory_skips_subsequent_stages(monkeypatch):
    import markdown_parser.main as main_mod

    def fake_load(path):
        return []

    def should_not_be_called(*args, **kwargs):
        raise AssertionError("This stage should not be invoked for empty input")

    monkeypatch.setattr(main_mod, "load_documents", fake_load)
    monkeypatch.setattr(main_mod, "extract_structure_from_documents", should_not_be_called)

    summary = main_mod.run_pipeline("/tmp/none")
    assert summary["documents_loaded"] == 0


def test_invalid_documents_record_errors(monkeypatch):
    import markdown_parser.main as main_mod

    def fake_load(path):
        return [{"text": "doc", "document_id": "doc1", "file_path": "/tmp/doc1.md"}]

    def bad_structure(docs):
        raise RuntimeError("structure extraction failed")

    monkeypatch.setattr(main_mod, "load_documents", fake_load)
    monkeypatch.setattr(main_mod, "extract_structure_from_documents", bad_structure)

    summary = main_mod.run_pipeline("/tmp/whatever")
    assert summary["documents_loaded"] == 1
    assert any("structure" in e for e in summary["errors"])
