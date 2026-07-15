"""End-to-end runner for Phase 5 — Graph Normalisation."""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from time import perf_counter
from typing import Any

_GRAPH_ROOT = Path(__file__).resolve().parent
_POC_ROOT = _GRAPH_ROOT.parent
for _path in (str(_POC_ROOT), str(_GRAPH_ROOT)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from entities.deduplicator import deduplicate_entities
from entities.pipeline import normalise_entities
from neo4j.client import Neo4jClient
from neo4j.graph_writer import GraphWriter
from relationships.normalizer import normalize_relationships
from shared.config import settings

from artifacts import GraphArtifactWriter
from loader import load_extraction_results
from reporting import StageRecorder


async def run_pipeline(
    app_settings: Any = settings,
    graph_writer: GraphWriter | None = None,
) -> dict[str, Any]:
    """Execute the full Phase 5 graph normalisation pipeline."""
    recorder = StageRecorder()
    start = perf_counter()
    artifacts = GraphArtifactWriter(app_settings.graph_normalisation_output_dir)

    extraction_results, raw_relationships = recorder.run(
        "load_inputs",
        lambda: load_extraction_results(app_settings.graph_normalisation_input_dir),
    )
    canonical = recorder.run("build_canonical_entities", lambda: normalise_entities(extraction_results))
    deduplicated = recorder.run("deduplicate_entities", lambda: deduplicate_entities(canonical))
    normalized_relationships = recorder.run(
        "normalize_relationships",
        lambda: normalize_relationships(raw_relationships, deduplicated),
    )

    neo4j_summary = await _persist(graph_writer, deduplicated, normalized_relationships, recorder)

    artifacts.write_entities("canonical_entities.json", canonical)
    artifacts.write_entities("deduplicated_entities.json", deduplicated)
    artifacts.write_relationships(normalized_relationships)
    artifacts.write_summary(neo4j_summary)

    stats = _statistics(extraction_results, canonical, deduplicated, normalized_relationships, neo4j_summary, start, recorder)
    report = recorder.report(
        {"extraction_results": len(extraction_results), "raw_relationships": len(raw_relationships)},
        {"canonical_entities": len(canonical), "deduplicated_entities": len(deduplicated), "normalized_relationships": len(normalized_relationships)},
    )
    artifacts.write_statistics(stats)
    artifacts.write_report(report)
    return {"statistics": stats, "report": report, "neo4j": neo4j_summary}


async def _persist(writer: GraphWriter | None, entities, relationships, recorder: StageRecorder) -> dict[str, Any]:  # type: ignore[no-untyped-def]
    start = perf_counter()
    try:
        writer = writer or GraphWriter(Neo4jClient())
        await writer.setup_schema()
        counts = await writer.write_graph(entities, relationships)
        recorder.add_stage("persist_to_neo4j", start)
        return {"status": "success", **counts}
    except Exception as exc:  # noqa: BLE001
        recorder.warnings.append(f"Neo4j persistence failed: {exc}")
        recorder.add_stage("persist_to_neo4j", start, error=str(exc))
        return {"status": "failed", "entities": 0, "relationships": 0, "error": str(exc)}


def _statistics(results, canonical, deduplicated, relationships, neo4j_summary, start, recorder):  # type: ignore[no-untyped-def]
    processed = sum(result.entity_count for result in results)
    return {
        "entities_processed": processed,
        "canonical_entities_created": len(canonical),
        "entities_merged": max(0, len(canonical) - len(deduplicated)),
        "relationships_normalized": len(relationships),
        "graph_nodes_written": neo4j_summary.get("entities", 0),
        "graph_relationships_written": neo4j_summary.get("relationships", 0),
        "execution_time_seconds": round(perf_counter() - start, 4),
        "failures": recorder.errors + ([neo4j_summary.get("error")] if neo4j_summary.get("error") else []),
    }


def main() -> None:
    """CLI entry point for ``python main.py``."""
    asyncio.run(run_pipeline())


if __name__ == "__main__":
    main()