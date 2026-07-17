"""Small stage helpers for the extraction pipeline."""
from __future__ import annotations

import logging

from .loader import ExtractionRecord
from shared.models import Entity, ExtractionResult, ExtractionStatus

logger = logging.getLogger(__name__)


def run_spacy(spacy_pipeline, record: ExtractionRecord) -> ExtractionResult | None:  # type: ignore[no-untyped-def]
    try:
        return spacy_pipeline.run(
            text=record.text,
            source_metadata=record.source_metadata,
            source_parser=record.source_parser,
        )
    except Exception as exc:
        logger.warning("spaCy failed for '%s': %s", record.source_metadata.source_id, exc)
        return None


def run_llm(triple_service, record: ExtractionRecord):  # type: ignore[no-untyped-def]
    try:
        return triple_service.run(
            text=record.text,
            source_metadata=record.source_metadata,
            source_parser=record.source_parser,
        )
    except Exception as exc:
        logger.warning("LLM failed for '%s': %s", record.source_metadata.source_id, exc)
        failed = ExtractionResult(
            source=record.source_metadata,
            status=ExtractionStatus.FAILED,
            errors=[str(exc)],
        )
        return [], failed


def run_entity_embeddings(batch_service, entities: list[Entity], record: ExtractionRecord) -> list:  # type: ignore[no-untyped-def]
    if not entities or batch_service is None:
        return []
    try:
        return batch_service.embed_entities(entities, record.source_metadata, record.source_parser)
    except Exception as exc:
        logger.warning("Entity embedding failed for '%s': %s", record.source_metadata.source_id, exc)
        return []


def run_chunk_embeddings(batch_service, record: ExtractionRecord) -> list:  # type: ignore[no-untyped-def]
    if not record.text.strip() or batch_service is None:
        return []
    try:
        chunks = [{"text": record.text, "label": record.source_metadata.source_id}]
        return batch_service.embed_chunks(chunks, record.source_metadata, record.source_parser)
    except Exception as exc:
        logger.warning("Chunk embedding failed for '%s': %s", record.source_metadata.source_id, exc)
        return []