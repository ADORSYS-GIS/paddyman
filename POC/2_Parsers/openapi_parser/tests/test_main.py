"""Unit tests for openapi_parser.main — pipeline orchestration.

Covers:
- stage ordering: load → split → endpoint/schema/ref extraction
- summary counts (specs, chunks, endpoints, schemas, dtos, enums, refs)
- settings used when source_dir is None
- empty document list → zero-count summary
- large documents skipped by _docs_to_raw_specs size guard
- semantic splitting failure recorded in errors, pipeline continues
- per-extraction-stage failure captured in errors
- missing source directory handled gracefully
- summary contains all expected keys including chunks_produced
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

import openapi_parser.main as main_mod


# ---------------------------------------------------------------------------
# Shared fixture helpers
# ---------------------------------------------------------------------------

def _make_meta(title: str = "Pay API", spec_file: str = "/spec.yaml") -> Any:
    from openapi_parser.models import OpenApiMetadata
    return OpenApiMetadata(title=title, version="1.0.0", spec_file=spec_file)


def _make_ep(method: str = "GET", path: str = "/x") -> Any:
    from openapi_parser.models import EndpointMetadata
    return EndpointMetadata(
        type="endpoint", method=method, path=path,
        api_title="Pay API", spec_source="/spec.yaml",
    )


def _make_schema(name: str = "Foo", schema_type: str | None = "object") -> Any:
    from openapi_parser.models import SchemaMetadata
    return SchemaMetadata(type="schema", name=name, spec_source="/spec.yaml",
                          schema_type=schema_type)


def _make_enum_schema(name: str = "Status") -> Any:
    from openapi_parser.models import SchemaMetadata
    return SchemaMetadata(type="schema", name=name, spec_source="/spec.yaml",
                          schema_type="string", enum_values=["A", "B"])


def _make_rel(rel: str = "RETURNS") -> Any:
    from openapi_parser.models import RelationshipMetadata
    return RelationshipMetadata(
        type="relationship", source="GET /x", target="Foo",
        relationship=rel, spec_source="/spec.yaml",
    )


_MINIMAL_YAML = (
    'openapi: "3.0.1"\ninfo:\n  title: Pay API\n  version: "1.0.0"\n'
    'paths:\n  /payments:\n    get:\n      responses:\n        "200":\n          description: OK\n'
)


def _make_doc(text: str = _MINIMAL_YAML, file_path: str = "/spec.yaml") -> Any:
    """Create a LlamaIndex Document with file_path metadata."""
    try:
        from llama_index.core import Document
        return Document(text=text, metadata={"file_path": file_path})
    except ImportError:
        try:
            from llama_index import Document  # type: ignore
            return Document(text=text, extra_info={"file_path": file_path})
        except ImportError:
            pytest.skip("llama_index not available")


# ---------------------------------------------------------------------------
# Stage ordering and counts
# ---------------------------------------------------------------------------

class TestPipelineOrchestration:
    def test_stage_order_load_split_extract(self, monkeypatch, tmp_path: Path):
        """Stages execute in order: load → split → endpoint/schema/ref extraction."""
        doc = _make_doc()
        calls: list[str] = []

        monkeypatch.setattr(main_mod, "load_documents_fn",
                            lambda d: (calls.append("load"), [doc])[1])
        monkeypatch.setattr(main_mod, "extract_endpoints_fn",
                            lambda r, t, s: (calls.append("endpoints"), [_make_ep()])[1])
        monkeypatch.setattr(main_mod, "extract_schemas_fn",
                            lambda r, s: (calls.append("schemas"), [_make_schema()])[1])
        monkeypatch.setattr(main_mod, "resolve_refs_fn",
                            lambda r, e, sc, s: (calls.append("refs"), [_make_rel()])[1])

        summary = main_mod.run_pipeline(tmp_path)

        assert calls == ["load", "endpoints", "schemas", "refs"]
        assert summary["specs_loaded"] == 1
        assert summary["endpoints_extracted"] == 1
        assert summary["schemas_extracted"] == 1
        assert summary["refs_resolved"] == 1
        assert summary["errors"] == []

    def test_dtos_and_enums_counted_separately(self, monkeypatch, tmp_path: Path):
        doc = _make_doc()
        schemas = [_make_schema("A", "object"), _make_schema("B", "string"), _make_enum_schema()]

        monkeypatch.setattr(main_mod, "load_documents_fn", lambda d: [doc])
        monkeypatch.setattr(main_mod, "extract_endpoints_fn", lambda r, t, s: [])
        monkeypatch.setattr(main_mod, "extract_schemas_fn", lambda r, s: schemas)
        monkeypatch.setattr(main_mod, "resolve_refs_fn", lambda r, e, sc, s: [])

        summary = main_mod.run_pipeline(tmp_path)
        assert summary["schemas_extracted"] == 3
        assert summary["dtos_extracted"] == 1
        assert summary["enums_extracted"] == 1

    def test_endpoint_schema_rels_is_returns_plus_accepts(self, monkeypatch, tmp_path: Path):
        doc = _make_doc()
        rels = [_make_rel("RETURNS"), _make_rel("ACCEPTS"), _make_rel("REFERENCES")]

        monkeypatch.setattr(main_mod, "load_documents_fn", lambda d: [doc])
        monkeypatch.setattr(main_mod, "extract_endpoints_fn", lambda r, t, s: [])
        monkeypatch.setattr(main_mod, "extract_schemas_fn", lambda r, s: [])
        monkeypatch.setattr(main_mod, "resolve_refs_fn", lambda r, e, sc, s: rels)

        summary = main_mod.run_pipeline(tmp_path)
        assert summary["refs_resolved"] == 3
        assert summary["endpoint_schema_rels"] == 2

    def test_apis_discovered_deduplicates_titles(self, monkeypatch, tmp_path: Path):
        docs = [
            _make_doc(_MINIMAL_YAML.replace("Pay API", "Same Title"), "/a.yaml"),
            _make_doc(_MINIMAL_YAML.replace("Pay API", "Same Title"), "/b.yaml"),
            _make_doc(_MINIMAL_YAML.replace("Pay API", "Other Title"), "/c.yaml"),
        ]

        monkeypatch.setattr(main_mod, "load_documents_fn", lambda d: docs)
        monkeypatch.setattr(main_mod, "extract_endpoints_fn", lambda r, t, s: [])
        monkeypatch.setattr(main_mod, "extract_schemas_fn", lambda r, s: [])
        monkeypatch.setattr(main_mod, "resolve_refs_fn", lambda r, e, sc, s: [])

        summary = main_mod.run_pipeline(tmp_path)
        assert summary["specs_loaded"] == 3
        assert summary["apis_discovered"] == 2

    def test_summary_contains_all_required_keys(self, monkeypatch, tmp_path: Path):
        monkeypatch.setattr(main_mod, "load_documents_fn", lambda d: [])

        summary = main_mod.run_pipeline(tmp_path)
        expected = {
            "specs_loaded", "apis_discovered", "endpoints_extracted",
            "schemas_extracted", "dtos_extracted", "enums_extracted",
            "refs_resolved", "endpoint_schema_rels", "errors",
        }
        assert expected.issubset(summary.keys())


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

class TestConfiguration:
    def test_uses_settings_yaml_spec_dir_when_no_path_given(self, monkeypatch, tmp_path: Path):
        class FakeSettings:
            yaml_spec_dir = tmp_path

        monkeypatch.setattr("shared.config.settings", FakeSettings())
        monkeypatch.setattr(main_mod, "load_documents_fn", lambda d: [])

        summary = main_mod.run_pipeline(None)
        assert summary["specs_loaded"] == 0

    def test_explicit_path_overrides_settings(self, monkeypatch, tmp_path: Path):
        recorded: list[Path] = []

        def fake_load(d: Path):
            recorded.append(d)
            return []

        monkeypatch.setattr(main_mod, "load_documents_fn", fake_load)
        main_mod.run_pipeline(tmp_path)
        assert recorded == [tmp_path]


# ---------------------------------------------------------------------------
# Edge cases and error handling
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_empty_document_list_returns_zero_summary(self, monkeypatch, tmp_path: Path):
        monkeypatch.setattr(main_mod, "load_documents_fn", lambda d: [])

        summary = main_mod.run_pipeline(tmp_path)
        assert summary["specs_loaded"] == 0
        assert summary["errors"] == []

    def test_missing_directory_returns_error_summary(self):
        summary = main_mod.run_pipeline(Path("/nonexistent/totally/missing"))
        assert summary["specs_loaded"] == 0
        assert len(summary["errors"]) >= 1

    def test_all_valid_docs_parsed_regardless_of_size(self, monkeypatch, tmp_path: Path):
        """CSafeLoader handles large files — no size guard drops valid specs."""
        # A doc whose text is well over 300 KB but still valid YAML
        large_text = _MINIMAL_YAML + ("# padding\n" * 30_000)
        docs = [_make_doc(large_text, "/huge.yaml"), _make_doc(_MINIMAL_YAML, "/small.yaml")]

        monkeypatch.setattr(main_mod, "load_documents_fn", lambda d: docs)
        monkeypatch.setattr(main_mod, "extract_endpoints_fn", lambda r, t, s: [])
        monkeypatch.setattr(main_mod, "extract_schemas_fn", lambda r, s: [])
        monkeypatch.setattr(main_mod, "resolve_refs_fn", lambda r, e, sc, s: [])

        summary = main_mod.run_pipeline(tmp_path)
        assert summary["specs_loaded"] == 2  # both docs parsed

    def test_endpoint_stage_failure_pipeline_continues(self, monkeypatch, tmp_path: Path):
        doc = _make_doc()
        monkeypatch.setattr(main_mod, "load_documents_fn", lambda d: [doc])

        monkeypatch.setattr(main_mod, "extract_endpoints_fn",
                            lambda r, t, s: (_ for _ in ()).throw(RuntimeError("boom")))
        monkeypatch.setattr(main_mod, "extract_schemas_fn", lambda r, s: [_make_schema()])
        monkeypatch.setattr(main_mod, "resolve_refs_fn", lambda r, e, sc, s: [])

        summary = main_mod.run_pipeline(tmp_path)
        assert any("endpoint extraction" in e for e in summary["errors"])
        assert summary["schemas_extracted"] == 1

    def test_real_yaml_spec_structural_extraction(self, monkeypatch, tmp_path: Path):
        """Integration smoke: well-formed YAML doc runs all structural stages."""
        yaml_content = (
            'openapi: "3.0.1"\n'
            'info:\n  title: Smoke API\n  version: "1.0"\n'
            'paths:\n'
            '  /items:\n'
            '    get:\n'
            '      responses:\n'
            '        "200":\n'
            '          content:\n'
            '            application/json:\n'
            '              schema:\n'
            '                $ref: "#/components/schemas/Item"\n'
            'components:\n'
            '  schemas:\n'
            '    Item:\n'
            '      type: object\n'
            '      properties:\n'
            '        id:\n'
            '          type: string\n'
        )
        doc = _make_doc(yaml_content, str(tmp_path / "smoke.yaml"))

        monkeypatch.setattr(main_mod, "load_documents_fn", lambda d: [doc])
        monkeypatch.setattr(main_mod, "extract_schemas_fn", None)
        monkeypatch.setattr(main_mod, "resolve_refs_fn", None)

        summary = main_mod.run_pipeline(tmp_path)
        assert summary["specs_loaded"] == 1
        assert summary["endpoints_extracted"] == 1
        assert summary["schemas_extracted"] == 1
        assert summary["errors"] == []

