"""Load normalized-input records from previous pipeline phases."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from shared.models import Entity, ExtractionResult, ExtractionStatus, SourceMetadata, SourceType


def load_extraction_results(input_dir: Path) -> tuple[list[ExtractionResult], list[object]]:
    """Load entities and raw relationships from JSON/JSONL artifacts in *input_dir*."""
    results: list[ExtractionResult] = []
    raw_relationships: list[object] = []
    if not input_dir.exists():
        return results, raw_relationships
    for path in sorted([*input_dir.glob("*.json"), *input_dir.glob("*.jsonl")]):
        for record in _records(path):
            result, relationships = _record_to_result(record, path)
            results.append(result)
            raw_relationships.extend(relationships)
    return results, raw_relationships


def _records(path: Path) -> list[dict[str, Any]]:
    if path.suffix == ".jsonl":
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, list) else [payload]


def _record_to_result(record: dict[str, Any], path: Path) -> tuple[ExtractionResult, list[object]]:
    source = SourceMetadata(
        source_id=str(record.get("source_id") or path.name),
        source_type=SourceType.DOCUMENT,
        location=str(path),
        metadata={"file_path": str(path), "source_parser": record.get("source_parser")},
    )
    entities = [_entity(e, record) for e in _entities(record)]
    relationships = [*_relationships(record), *_triples(record)]
    return ExtractionResult(source=source, entities=entities, status=ExtractionStatus.SUCCESS), relationships


def _entities(record: dict[str, Any]) -> list[dict[str, Any]]:
    entities: list[dict[str, Any]] = []
    for key in ("entities", "spacy_entities", "llm_entities"):
        values = record.get(key, [])
        if isinstance(values, list):
            entities.extend(v for v in values if isinstance(v, dict))
    return entities


def _relationships(record: dict[str, Any]) -> list[object]:
    values = record.get("relationships", [])
    return values if isinstance(values, list) else []


def _triples(record: dict[str, Any]) -> list[object]:
    values = record.get("triples", [])
    return values if isinstance(values, list) else []


def _entity(data: dict[str, Any], record: dict[str, Any]) -> Entity:
    properties = dict(data.get("properties") or {})
    properties.setdefault("source_parser", record.get("source_parser") or data.get("source_parser"))
    return Entity(
        type=str(data.get("type") or data.get("label") or "entity"),
        name=str(data.get("name") or data.get("text") or data.get("id") or "unknown"),
        source=str(data.get("source") or record.get("source_id") or "unknown"),
        properties=properties,
    )