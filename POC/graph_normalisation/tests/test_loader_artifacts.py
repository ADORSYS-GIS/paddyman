"""Unit tests for Phase 5 input loading and artifact writing."""
from __future__ import annotations

import json

from artifacts import GraphArtifactWriter
from loader import load_extraction_results


def test_load_extraction_results_from_jsonl(tmp_path) -> None:  # type: ignore[no-untyped-def]
    record = {
        "source_id": "doc-1",
        "source_parser": "markdown_parser",
        "spacy_entities": [{"type": "concept", "name": "Payment Initiation"}],
        "triples": [{"subject": "Payment Initiation", "predicate": "documents", "object": "PaymentDTO"}],
    }
    (tmp_path / "extraction.jsonl").write_text(json.dumps(record) + "\n", encoding="utf-8")
    results, relationships = load_extraction_results(tmp_path)
    assert len(results) == 1
    assert results[0].entities[0].name == "Payment Initiation"
    assert relationships[0]["predicate"] == "documents"


def test_artifact_writer_outputs_json(tmp_path) -> None:  # type: ignore[no-untyped-def]
    writer = GraphArtifactWriter(tmp_path)
    writer.write_summary({"status": "success", "entities": 1})
    payload = json.loads((tmp_path / "neo4j_import_summary.json").read_text(encoding="utf-8"))
    assert payload == {"entities": 1, "status": "success"}