"""Artifact writer for Phase 5 graph normalisation outputs."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from entities.models import CanonicalEntity
from shared.models import Relationship


class GraphArtifactWriter:
    """Write graph normalisation JSON artifacts to the configured output dir."""

    def __init__(self, output_dir: Path) -> None:
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def write_entities(self, name: str, entities: list[CanonicalEntity]) -> None:
        self._write(name, [entity.to_dict() for entity in entities])

    def write_relationships(self, relationships: list[Relationship]) -> None:
        self._write("normalized_relationships.json", [_relationship(rel) for rel in relationships])

    def write_summary(self, summary: dict[str, Any]) -> None:
        self._write("neo4j_import_summary.json", summary)

    def write_statistics(self, stats: dict[str, Any]) -> None:
        self._write("graph_statistics.json", stats)

    def write_report(self, report: dict[str, Any]) -> None:
        self._write("pipeline_report.json", report)

    def _write(self, filename: str, payload: Any) -> None:
        path = self.output_dir / filename
        path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8")


def _relationship(rel: Relationship) -> dict[str, Any]:
    return {
        "id": str(rel.id),
        "source": rel.properties.get("source") or str(rel.source_entity_id),
        "target": rel.properties.get("target") or str(rel.target_entity_id),
        "type": rel.type,
        "original_type": rel.properties.get("original_type"),
        "confidence": rel.confidence,
        "properties": rel.properties,
    }