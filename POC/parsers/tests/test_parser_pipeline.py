"""Tests for the canonical parser pipeline runner."""
from __future__ import annotations

import json
import sys
from pathlib import Path

_POC_ROOT = Path(__file__).resolve().parents[2]
_PARSERS_ROOT = _POC_ROOT / "2_Parsers"
for _path in (str(_POC_ROOT), str(_PARSERS_ROOT)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from java_module_output import write_java_module_normalized_jsons
from normalized_json import PARSER_OUTPUT_FILENAME
from POC.parsers.openapi_file_output import write_openapi_file_normalized_jsons
from parser_pipeline import run_pipeline
from shared.models import NormalizedDocument, NormalizedJson, SourceMetadata


def test_parser_pipeline_executes_all_parsers_in_order(tmp_path) -> None:
    calls: list[str] = []

    def runner(name: str):
        def _run() -> dict[str, str]:
            calls.append(name)
            return {"status": "ok"}
        return _run

    def normalizer(summaries):
        return NormalizedJson(
            documents=[
                NormalizedDocument(
                    document_id="doc-1",
                    text="Payment API",
                    source_parser="markdown_parser",
                    source_metadata={"file_path": "doc.md"},
                )
            ],
            version_metadata={"summaries": summaries},
        )

    output_path = tmp_path / PARSER_OUTPUT_FILENAME
    summary = run_pipeline(
        java_runner=runner("java_parser"),
        openapi_runner=runner("openapi_parser"),
        markdown_runner=runner("markdown_parser"),
        normalizer=normalizer,
        output_path=output_path,
    )

    assert calls == ["java_parser", "openapi_parser", "markdown_parser"]
    assert summary.documents == 1
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert set(payload) == {"entities", "relationships", "documents", "source_metadata", "provenance", "version_metadata", "method_calls", "parser_indices"}
    assert payload["documents"][0]["source_parser"] == "markdown_parser"


def test_direct_java_parser_output_is_sharded_by_module(tmp_path) -> None:  # type: ignore[no-untyped-def]
    repo = tmp_path / "code" / "repo-a"
    source = repo / "src" / "main" / "java" / "com"
    source.mkdir(parents=True)
    (repo / "pom.xml").write_text("<project><modelVersion>4.0.0</modelVersion></project>", encoding="utf-8")
    (source / "Example.java").write_text("package com; class Example {}\n", encoding="utf-8")

    paths = write_java_module_normalized_jsons(source_dir=tmp_path / "code", output_dir=tmp_path / "parsed" / "java_code")

    assert [path.name for path in paths] == ["repo-a__repo-a.json"]
    payload = json.loads(paths[0].read_text(encoding="utf-8"))
    assert payload["documents"][0]["source_parser"] == "java_parser"
    src = payload["documents"][0]["source_metadata"]
    # parser-specific attributes should live under `metadata`
    assert src["metadata"]["module"] == "repo-a"
    # ensure it can be loaded back into the dataclass
    SourceMetadata(**src)


def test_direct_openapi_parser_output_is_sharded_by_yaml_file(tmp_path) -> None:  # type: ignore[no-untyped-def]
    spec_dir = tmp_path / "yaml_spec" / "repo"
    spec_dir.mkdir(parents=True)
    (spec_dir / "accounts.yaml").write_text("openapi: 3.0.1\ninfo:\n  title: Accounts\n", encoding="utf-8")

    paths = write_openapi_file_normalized_jsons(
        source_dir=tmp_path / "yaml_spec",
        output_dir=tmp_path / "parsed" / "openapi_specs",
    )

    assert [path.name for path in paths] == ["repo_accounts.json"]
    payload = json.loads(paths[0].read_text(encoding="utf-8"))
    assert payload["documents"][0]["source_parser"] == "openapi_parser"
    src = payload["documents"][0]["source_metadata"]
    assert src["metadata"]["relative_path"] == "repo/accounts.yaml"
    SourceMetadata(**src)