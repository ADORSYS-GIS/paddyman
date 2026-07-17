"""Entity extraction pipeline runner."""
from __future__ import annotations

import logging
import sys
from dataclasses import dataclass, field
from pathlib import Path

_poc_root = str(Path(__file__).resolve().parents[1])
_spacy_root = str(Path(__file__).resolve().parent / "spacy")
_llm_root = str(Path(__file__).resolve().parent / "llm")
_extractors_root = str(Path(__file__).resolve().parent)

for _p in (_poc_root, _spacy_root, _llm_root):
    if _p not in sys.path:
        sys.path.insert(0, _p)

if _extractors_root not in sys.path:
    sys.path.append(_extractors_root)

from .extraction_steps import run_chunk_embeddings, run_entity_embeddings, run_llm, run_spacy
from shared.models import Entity, ExtractionStatus

from .loader import ExtractionRecord

logger = logging.getLogger(__name__)

@dataclass
class PipelineSummary:
    """Aggregated counts from one full extraction pipeline run."""

    records_processed: int = 0
    spacy_entities: int = 0
    llm_entities: int = 0
    relationships: int = 0
    triples: int = 0
    entity_embeddings: int = 0
    chunk_embeddings: int = 0
    failures: list[str] = field(default_factory=list)

class ExtractionPipeline:
    """Orchestrates spaCy and GLM extraction for normalized records."""

    def __init__(
        self,
        spacy_pipeline,
        triple_service,
        embed_service=None,
        batch_service=None,
        writer=None,
    ) -> None:
        self._spacy = spacy_pipeline
        self._triples = triple_service
        self._batch = batch_service
        self._writer = writer

    def run(self, records: list[ExtractionRecord]) -> PipelineSummary:
        """Execute extraction over *records* and collect recoverable failures."""
        summary = PipelineSummary(records_processed=len(records))

        for record in records:
            self._process_record(record, summary)

        logger.info(
            "Pipeline complete — spaCy: %d, LLM: %d, rels: %d, "
            "triples: %d, entity_emb: %d, chunk_emb: %d, failures: %d",
            summary.spacy_entities,
            summary.llm_entities,
            summary.relationships,
            summary.triples,
            summary.entity_embeddings,
            summary.chunk_embeddings,
            len(summary.failures),
        )
        return summary

    def _process_record(
        self,
        record: ExtractionRecord,
        summary: PipelineSummary,
    ) -> None:
        source_id = record.source_metadata.source_id

        spacy_result = run_spacy(self._spacy, record)
        if spacy_result is not None:
            summary.spacy_entities += len(spacy_result.entities)
        else:
            summary.failures.append(f"spacy:{source_id}")

        triples, llm_result = run_llm(self._triples, record)
        summary.llm_entities += len(llm_result.entities)
        summary.relationships += len(llm_result.relationships)
        summary.triples += len(triples)
        if llm_result.status == ExtractionStatus.FAILED:
            summary.failures.append(f"llm:{source_id}")

        all_entities: list[Entity] = list(llm_result.entities)
        if spacy_result:
            all_entities.extend(spacy_result.entities)
        emb_results = run_entity_embeddings(self._batch, all_entities, record)
        summary.entity_embeddings += len([r for r in emb_results if r.vector])

        chunk_embs = run_chunk_embeddings(self._batch, record)
        summary.chunk_embeddings += len([r for r in chunk_embs if r.vector])

        if self._writer is not None:
            try:
                self._writer.write(
                    source_id=source_id,
                    source_parser=record.source_parser,
                    spacy_entities=spacy_result.entities if spacy_result else [],
                    llm_entities=list(llm_result.entities),
                    relationships=list(llm_result.relationships),
                    triples=triples,
                    entity_embeddings=emb_results,
                    chunk_embeddings=chunk_embs,
                    document_chunks=[{"text": record.text, "label": source_id}] if record.text.strip() else [],
                    llm_status=llm_result.status.value,
                )
            except Exception as exc:
                logger.warning("Output write failed for '%s': %s", source_id, exc)
