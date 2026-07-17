"""Integration test for the Phase 5 graph normalisation runner."""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from types import SimpleNamespace

_POC_ROOT = Path(__file__).resolve().parents[1]
_GRAPH_ROOT = _POC_ROOT / "graph_normalisation"
for _p in (str(_POC_ROOT), str(_GRAPH_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from main import run_pipeline


class FakeGraphWriter:
    def __init__(self, fail: bool = False) -> None:
        self.fail = fail
        self.entities_written = 0
        self.relationships_written = 0

    async def setup_schema(self) -> None:
        if self.fail:
            raise RuntimeError("neo4j unavailable")

    async def write_graph(self, entities, relationships):  # type: ignore[no-untyped-def]
        self.entities_written = len(entities)
        self.relationships_written = len(relationships)
        return {"entities": len(entities), "relationships": len(relationships)}


def _settings(input_dir: Path, output_dir: Path) -> SimpleNamespace:
    return SimpleNamespace(
        graph_normalisation_input_dir=input_dir,
        graph_normalisation_output_dir=output_dir,
    )


def test_complete_phase5_pipeline_execution(tmp_path) -> None:  # type: ignore[no-untyped-def]
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()
    record = {
        "source_id": "payment-doc",
        "source_parser": "markdown_parser",
        "spacy_entities": [
            {"type": "controller", "name": "PaymentController", "properties": {"source_parser": "java_parser"}},
            {"type": "endpoint", "name": "POST /payments", "properties": {"source_parser": "openapi_parser"}},
            {"type": "concept", "name": "Payment Initiation", "properties": {"source_parser": "markdown_parser"}},
        ],
        "triples": [{"subject": "PaymentController", "predicate": "calls", "object": "Payment Initiation"}],
    }
    (input_dir / "extraction.jsonl").write_text(json.dumps(record) + "\n", encoding="utf-8")
    result = asyncio.run(run_pipeline(_settings(input_dir, output_dir), FakeGraphWriter()))
    assert result["neo4j"]["status"] == "success"
    assert (output_dir / "canonical_entities.json").exists()
    assert (output_dir / "deduplicated_entities.json").exists()
    assert (output_dir / "normalized_relationships.json").exists()
    assert (output_dir / "graph_statistics.json").exists()
    assert (output_dir / "pipeline_report.json").exists()
    stats = json.loads((output_dir / "graph_statistics.json").read_text(encoding="utf-8"))
    assert stats["canonical_entities_created"] >= 1
    assert stats["relationships_normalized"] == 1
    report = json.loads((output_dir / "pipeline_report.json").read_text(encoding="utf-8"))
    assert "persist_to_neo4j" in report["stages_executed"]


def test_phase5_pipeline_records_persistence_failure(tmp_path) -> None:  # type: ignore[no-untyped-def]
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()
    (input_dir / "empty.json").write_text(json.dumps({}), encoding="utf-8")
    result = asyncio.run(run_pipeline(_settings(input_dir, output_dir), FakeGraphWriter(fail=True)))
    assert result["neo4j"]["status"] == "failed"
    report = json.loads((output_dir / "pipeline_report.json").read_text(encoding="utf-8"))
    assert report["warnings"]