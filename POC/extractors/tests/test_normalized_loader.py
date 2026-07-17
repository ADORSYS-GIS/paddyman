"""Tests for normalized JSON extraction loading."""
from __future__ import annotations

import json
import sys
from pathlib import Path

_POC_ROOT = Path(__file__).resolve().parents[2]
_EXTRACTORS_ROOT = _POC_ROOT / "4_Extractors"
for _path in (str(_POC_ROOT), str(_EXTRACTORS_ROOT)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from loader import load_all_records


def test_load_all_records_consumes_normalized_json_only(tmp_path) -> None:
    payload = {
        "entities": [],
        "relationships": [],
        "documents": [
            {
                "document_id": "openapi_parser:spec.yaml",
                "text": "openapi: 3.0.1",
                "source_parser": "openapi_parser",
                "source_metadata": {"file_path": "spec.yaml"},
                "chunks": ["openapi: 3.0.1"],
                "provenance": {"stage": "parser_pipeline"},
            }
        ],
        "source_metadata": [],
        "provenance": {},
        "version_metadata": {"contract": "normalized-json", "version": "1.0"},
    }
    path = tmp_path / "java_openapi_markdown_parser_output.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    records = load_all_records(tmp_path)

    assert len(records) == 1
    assert records[0].source_parser == "openapi_parser"
    assert records[0].text == "openapi: 3.0.1"
    assert records[0].source_metadata.metadata["source_parser"] == "openapi_parser"


def test_load_all_records_recurses_into_java_code_dir(tmp_path) -> None:  # type: ignore[no-untyped-def]
    java_dir = tmp_path / "java_code"
    java_dir.mkdir()
    payload = {
        "entities": [],
        "relationships": [],
        "documents": [
            {
                "document_id": "java_parser:repo:module:Example.java",
                "text": "class Example {}",
                "source_parser": "java_parser",
                "source_metadata": {"file_path": "Example.java", "module": "module"},
                "chunks": ["class Example {}"],
                "provenance": {"stage": "java_parser"},
            }
        ],
        "source_metadata": [],
        "provenance": {},
        "version_metadata": {"contract": "parser-json", "version": "1.0"},
    }
    (java_dir / "repo__module.json").write_text(json.dumps(payload), encoding="utf-8")

    records = load_all_records(tmp_path)

    assert len(records) == 1
    assert records[0].source_parser == "java_parser"


def test_load_all_records_recurses_into_openapi_specs_dir(tmp_path) -> None:  # type: ignore[no-untyped-def]
    specs_dir = tmp_path / "openapi_specs"
    specs_dir.mkdir()
    payload = {
        "entities": [],
        "relationships": [],
        "documents": [
            {
                "document_id": "openapi_parser:accounts.yaml",
                "text": "openapi: 3.0.1",
                "source_parser": "openapi_parser",
                "source_metadata": {"file_path": "accounts.yaml"},
                "chunks": [],
                "provenance": {"stage": "openapi_parser"},
            }
        ],
        "source_metadata": [],
        "provenance": {},
        "version_metadata": {"contract": "parser-json", "version": "1.0"},
    }
    (specs_dir / "accounts.json").write_text(json.dumps(payload), encoding="utf-8")

    records = load_all_records(tmp_path)

    assert len(records) == 1
    assert records[0].source_parser == "openapi_parser"