"""Verify canonical provenance keys are present on parser outputs."""
from __future__ import annotations

import sys
from pathlib import Path

_POC_ROOT = Path(__file__).resolve().parents[2]
_PARSERS_ROOT = _POC_ROOT / "2_Parsers"
for _path in (str(_POC_ROOT), str(_PARSERS_ROOT)):
    if _path not in sys.path:
        sys.path.insert(0, _path)


def test_markdown_document_provenance_contains_path_and_stage(tmp_path: Path) -> None:
    md = tmp_path / "spec.md"
    md.write_text("# Title\n\nSample content", encoding="utf-8")

    from markdown_parser.parser import markdown_to_normalized_docs

    docs = markdown_to_normalized_docs(md)
    assert docs
    doc = docs[0]
    assert isinstance(doc.provenance, dict)
    assert doc.provenance.get("path")
    assert doc.provenance.get("stage") == "markdown_parser"


def test_openapi_document_provenance_contains_path_and_stage(tmp_path: Path) -> None:
    spec_dir = tmp_path / "specs"
    spec_dir.mkdir()
    spec_file = spec_dir / "api.yaml"
    spec_file.write_text(
        """openapi: 3.0.1
info:
  title: Sample API
  version: 1.0.0
paths: {}
""",
        encoding="utf-8",
    )

    from openapi_parser.document_entities_builder import build_openapi_document_with_entities

    doc, entities = build_openapi_document_with_entities(spec_dir, spec_file)
    assert isinstance(doc.provenance, dict)
    assert doc.provenance.get("path")
    assert doc.provenance.get("stage") == "openapi_parser"
