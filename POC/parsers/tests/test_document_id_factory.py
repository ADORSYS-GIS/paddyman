"""Unit tests for the document id factory helpers."""
from __future__ import annotations

from pathlib import Path

from shared.id_factory import make_document_id, normalize_document_id


def test_make_document_id_single_file(tmp_path: Path) -> None:
    root = tmp_path
    spec = root / "spec.yaml"
    spec.write_text("openapi: 3.0.1")

    doc_id = make_document_id("openapi_parser", None, root, spec)
    assert doc_id == "openapi_parser:spec.yaml"


def test_make_document_id_repo_structure(tmp_path: Path) -> None:
    root = tmp_path
    repo = root / "repo1"
    (repo / "moduleA").mkdir(parents=True)
    f = repo / "moduleA" / "Example.java"
    f.write_text("class Example {}")

    doc_id = make_document_id("java_parser", None, root, f)
    assert doc_id == "java_parser:repo1:moduleA/Example.java"


def test_normalize_document_id_old_style() -> None:
    old = "java_parser:repo1/moduleA/Example.java"
    new = normalize_document_id(old)
    assert new == "java_parser:repo1:moduleA/Example.java"
