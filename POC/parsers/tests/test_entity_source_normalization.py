"""Tests to ensure every entity's `source` equals a document's `document_id`.

Coverage: OpenAPI, Markdown, Java parser outputs.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_POC_ROOT = Path(__file__).resolve().parents[2]
_PARSERS_ROOT = _POC_ROOT / "2_Parsers"
for _path in (str(_POC_ROOT), str(_PARSERS_ROOT)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from parsers.openapi_file_output import write_openapi_file_normalized_jsons
from markdown_file_output import process_specification_file
from java_module_output import write_java_module_normalized_jsons


def _assert_entities_reference_documents(payload: dict) -> None:
    docs = payload.get("documents") or []
    doc_ids = {d.get("document_id") for d in docs}
    assert doc_ids, "Bundle must contain at least one document"
    for ent in payload.get("entities") or []:
        assert ent.get("source") in doc_ids, f"Entity source {ent.get('source')} not in documents"


def test_openapi_entity_sources_normalized(tmp_path: Path) -> None:
    spec_dir = tmp_path / "specs"
    spec_dir.mkdir(parents=True)
    spec_content = """openapi: 3.0.1
info:
  title: Test API
  version: 1.0.0
paths:
  /ping:
    get:
      summary: ping
      responses:
        '200':
          description: OK
"""
    (spec_dir / "test.yaml").write_text(spec_content, encoding="utf-8")

    out_dir = tmp_path / "output"
    paths = write_openapi_file_normalized_jsons(source_dir=spec_dir, output_dir=out_dir)
    assert paths, "No output files produced"
    payload = json.loads(paths[0].read_text(encoding="utf-8"))
    _assert_entities_reference_documents(payload)


def test_markdown_entity_sources_normalized(tmp_path: Path) -> None:
    md = tmp_path / "spec.md"
    md.write_text("# Title\n\nParagraph text\n", encoding="utf-8")
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    process_specification_file(md, out_dir)
    outputs = list(out_dir.glob("*.json"))
    assert outputs, "Markdown output not written"
    payload = json.loads(outputs[0].read_text(encoding="utf-8"))
    _assert_entities_reference_documents(payload)


def test_java_entity_sources_normalized(tmp_path: Path) -> None:
    # create minimal java repo layout used by tests elsewhere
    repo = tmp_path / "code" / "repo-a"
    java_dir = repo / "src" / "main" / "java" / "com"
    java_dir.mkdir(parents=True)
    (repo / "pom.xml").write_text("<project></project>", encoding="utf-8")
    (java_dir / "Example.java").write_text("package com; class Example {}", encoding="utf-8")

    out_dir = tmp_path / "parsed" / "java_code"
    paths = write_java_module_normalized_jsons(source_dir=tmp_path / "code", output_dir=out_dir)
    assert paths, "Java output not produced"
    payload = json.loads(paths[0].read_text(encoding="utf-8"))
    _assert_entities_reference_documents(payload)
