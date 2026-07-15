"""Embedding stage runner for extraction outputs."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_EMBED_ROOT = Path(__file__).resolve().parent
_EXTRACTORS_ROOT = _EMBED_ROOT.parent
_POC_ROOT = _EXTRACTORS_ROOT.parent
for _path in (str(_POC_ROOT), str(_EXTRACTORS_ROOT), str(_EMBED_ROOT)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from shared.config import settings
from shared.models import Entity, SourceMetadata, SourceType


def run_pipeline(input_dir: Path | None = None, output_dir: Path | None = None, batch_service=None) -> Path | None:
    """Generate embeddings from extraction outputs only."""
    source_dir = input_dir or settings.extraction_output_dir or settings.graph_normalisation_input_dir
    target_dir = output_dir or settings.graph_normalisation_input_dir
    records = _load_records(source_dir)
    if not records:
        return None

    service = batch_service or _build_batch_service()
    target_dir.mkdir(parents=True, exist_ok=True)
    path = target_dir / f"embedded_extraction_{_timestamp()}.jsonl"
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            enriched = dict(record)
            source = _source_metadata(record)
            source_parser = str(record.get("source_parser") or source.metadata.get("source_parser") or "extraction_pipeline")
            entities = [_entity(item, record) for item in _entity_dicts(record)]
            chunks = _chunks(record)
            enriched["entity_embeddings"] = [_embedding_dict(item) for item in service.embed_entities(entities, source, source_parser)] if entities else []
            enriched["chunk_embeddings"] = [_embedding_dict(item) for item in service.embed_chunks(chunks, source, source_parser)] if chunks else []
            handle.write(json.dumps(enriched, ensure_ascii=False) + "\n")
    return path


def _build_batch_service():
    from embeddings.client.factory import create_client
    from embeddings.services.batch_service import BatchEmbeddingService

    return BatchEmbeddingService(client=create_client())


def _load_records(input_dir: Path) -> list[dict[str, Any]]:
    if not input_dir or not input_dir.exists():
        return []
    files = sorted([*input_dir.glob("*.json"), *input_dir.glob("*.jsonl")]) if input_dir.is_dir() else [input_dir]
    records: list[dict[str, Any]] = []
    for path in files:
        if path.name.startswith("embedded_extraction_"):
            continue
        if path.suffix == ".jsonl":
            records.extend(json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip())
        else:
            payload = json.loads(path.read_text(encoding="utf-8"))
            records.extend(payload if isinstance(payload, list) else [payload])
    return [record for record in records if isinstance(record, dict)]


def _entity_dicts(record: dict[str, Any]) -> list[dict[str, Any]]:
    values: list[dict[str, Any]] = []
    for key in ("entities", "spacy_entities", "llm_entities"):
        values.extend(item for item in record.get(key, []) if isinstance(item, dict))
    return values


def _entity(data: dict[str, Any], record: dict[str, Any]) -> Entity:
    return Entity(
        type=str(data.get("type") or "entity"),
        name=str(data.get("name") or data.get("text") or "unknown"),
        source=str(data.get("source") or record.get("source_id") or "unknown"),
        properties=dict(data.get("properties") or {}),
    )


def _chunks(record: dict[str, Any]) -> list[dict[str, str]]:
    chunks = record.get("document_chunks") or record.get("chunks") or []
    return [item for item in chunks if isinstance(item, dict) and item.get("text")]


def _source_metadata(record: dict[str, Any]) -> SourceMetadata:
    source_id = str(record.get("source_id") or "extraction-output")
    return SourceMetadata(
        source_id=source_id,
        source_type=SourceType.DOCUMENT,
        location=source_id,
        metadata={"source_parser": record.get("source_parser")},
    )


def _embedding_dict(embedding: Any) -> dict[str, Any]:
    raw_type = getattr(embedding, "input_type", "")
    input_type = raw_type.value if hasattr(raw_type, "value") else str(raw_type)
    return {
        "entity": getattr(embedding, "entity", ""),
        "input_type": input_type,
        "dimension": len(getattr(embedding, "vector", [])),
    }


def _timestamp() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y%m%dT%H%M%S")