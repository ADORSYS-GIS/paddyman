"""Extraction output writer — persists pipeline results to JSONL for inspection.

Writes one JSON line per processed record to a JSONL file.  Vectors are
omitted by default (they are large and not useful for human inspection);
set ``include_vectors=True`` if downstream tooling needs them.

Activated only when ``settings.extraction_output_dir`` is set.
"""
from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

_poc_root = str(Path(__file__).resolve().parents[1])
if _poc_root not in sys.path:
    sys.path.insert(0, _poc_root)

from shared.config import settings
from output_serializers import embedding_dict, entity_dict, relationship_dict, triple_dict

logger = logging.getLogger(__name__)


class ExtractionOutputWriter:
    """Writes one JSONL record per pipeline result to *output_dir*.

    Args:
        output_dir:         Directory where the JSONL file is written.
        include_vectors:    Include full embedding vectors in the output.
                            Defaults to ``False`` (vectors are large).
        skip_llm_failures:  When ``True``, records where the LLM failed
                            entirely (``llm_status == "failed"``) are not
                            written.  Defaults to ``False``.
    """

    def __init__(
        self,
        output_dir: Path,
        include_vectors: bool = False,
        skip_llm_failures: bool = False,
    ) -> None:
        output_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(tz=timezone.utc).strftime("%Y%m%dT%H%M%S")
        self._path = output_dir / f"extraction_{ts}.jsonl"
        self._include_vectors = include_vectors
        self._skip_llm_failures = skip_llm_failures
        self._fh = self._path.open("w", encoding="utf-8")
        logger.info("Extraction output: %s", self._path)

    # ------------------------------------------------------------------

    def write(
        self,
        source_id: str,
        source_parser: str,
        spacy_entities: list,
        llm_entities: list,
        relationships: list,
        triples: list,
        entity_embeddings: list,
        chunk_embeddings: list,
        document_chunks: list[dict[str, str]] | None = None,
        llm_status: str = "success",
    ) -> None:
        """Append one JSON line for the given record.

        Args:
            llm_status: ``"success"``, ``"failed"``, or ``"partial"``.
                        Mirrors :attr:`~shared.models.ExtractionStatus` values.
                        Used to distinguish a genuine empty extraction from an
                        LLM failure.
        """
        if self._skip_llm_failures and llm_status == "failed":
            logger.debug("Skipping failed LLM record: %s", source_id)
            return
        record: dict[str, Any] = {
            "source_id": source_id,
            "source_parser": source_parser,
            "llm_status": llm_status,
            "spacy_entities": [entity_dict(e) for e in spacy_entities],
            "llm_entities": [entity_dict(e) for e in llm_entities],
            "relationships": [relationship_dict(r) for r in relationships],
            "triples": [triple_dict(t) for t in triples],
            "document_chunks": document_chunks or [],
            "entity_embeddings": [embedding_dict(e, self._include_vectors) for e in entity_embeddings],
            "chunk_embeddings": [embedding_dict(e, self._include_vectors) for e in chunk_embeddings],
        }
        self._fh.write(json.dumps(record, ensure_ascii=False) + "\n")
        self._fh.flush()

    def close(self) -> None:
        """Flush and close the output file."""
        self._fh.close()
        logger.info("Extraction output closed: %s", self._path)

    def __enter__(self) -> "ExtractionOutputWriter":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def open_writer() -> ExtractionOutputWriter | None:
    """Return a configured writer, or ``None`` when output is disabled."""
    if not settings.extraction_output_dir:
        return None
    return ExtractionOutputWriter(settings.extraction_output_dir)
