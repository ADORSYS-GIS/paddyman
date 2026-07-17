"""Batch embedding service — high-throughput bulk embedding with chunked requests.

Responsibilities:
- Split input lists into provider-safe batches (``EMBED_BATCH_SIZE``).
- Delegate batch calls to the underlying embedding client.
- Assemble :class:`EmbeddingResult` objects with full provenance metadata.
- Continue on partial failures; report errors per item.
"""
from __future__ import annotations

import logging
import sys
import time
from pathlib import Path

_poc_root = str(Path(__file__).resolve().parents[3])
if _poc_root not in sys.path:
    sys.path.insert(0, _poc_root)

from shared.config import settings
from shared.models import Entity, SourceMetadata

from ..client.base_client import BaseEmbeddingClient, EmbeddingClientError
from ..models.embedding_result import EmbeddingInputType, EmbeddingResult
from .embedding_service import (
    _build_metadata,
    _entity_input_type,
    _entity_text,
    _is_non_retryable,
    _truncate,
)

logger = logging.getLogger(__name__)


class BatchEmbeddingService:
    """Bulk embedding service backed by a provider-agnostic client.

    Args:
        client:     Configured embedding client.
        batch_size: Max texts per provider call. Defaults to ``settings.embed_batch_size``.
        max_retries: Retry attempts on transient batch errors.
        retry_delay: Seconds between retries.
    """

    def __init__(
        self,
        client: BaseEmbeddingClient,
        batch_size: int | None = None,
        max_retries: int | None = None,
        retry_delay: float = 1.0,
    ) -> None:
        self._client = client
        self._batch_size = batch_size if batch_size is not None else settings.embed_batch_size
        self._max_retries = (
            max_retries if max_retries is not None else settings.embed_max_retries
        )
        self._retry_delay = retry_delay

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def embed_entities(
        self,
        entities: list[Entity],
        source_metadata: SourceMetadata,
        source_parser: str = "",
    ) -> list[EmbeddingResult]:
        """Embed a list of :class:`Entity` objects in batches.

        Continues on partial failures; items that fail get an empty vector.
        """
        if not entities:
            return []
        texts = [_truncate(_entity_text(e)) for e in entities]
        labels = [e.name for e in entities]
        input_types = [_entity_input_type(e) for e in entities]
        source_id = source_metadata.source_id
        return self._embed_batch(
            texts, labels, input_types, source_id, source_metadata, source_parser
        )

    def embed_chunks(
        self,
        chunks: list[dict],
        source_metadata: SourceMetadata,
        source_parser: str = "",
    ) -> list[EmbeddingResult]:
        """Embed a list of chunk dicts in batches.

        Each chunk dict must contain ``"text"`` and ``"label"`` keys.
        Optional ``"input_type"`` key accepts :class:`EmbeddingInputType` values.
        """
        if not chunks:
            return []
        texts = [_truncate(str(c.get("text", ""))) for c in chunks]
        labels = [str(c.get("label", "chunk")) for c in chunks]
        input_types = [
            EmbeddingInputType(c["input_type"])
            if "input_type" in c
            else EmbeddingInputType.CHUNK
            for c in chunks
        ]
        source_id = source_metadata.source_id
        return self._embed_batch(
            texts, labels, input_types, source_id, source_metadata, source_parser
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _embed_batch(
        self,
        texts: list[str],
        labels: list[str],
        input_types: list[EmbeddingInputType],
        source_id: str,
        source_metadata: SourceMetadata,
        source_parser: str,
    ) -> list[EmbeddingResult]:
        results: list[EmbeddingResult] = []
        for start in range(0, len(texts), self._batch_size):
            end = start + self._batch_size
            batch_texts = texts[start:end]
            batch_labels = labels[start:end]
            batch_types = input_types[start:end]
            responses = self._call_with_retry(batch_texts, source_id)
            for label, itype, resp in zip(batch_labels, batch_types, responses):
                vector = resp.vector if resp else []
                model = resp.model if resp else self._client.model
                provider = resp.provider if resp else self._client.provider_name
                dimension = len(vector)
                results.append(
                    EmbeddingResult(
                        entity=label,
                        input_type=itype,
                        source_id=source_id,
                        vector=vector,
                        metadata=_build_metadata(
                            model=model,
                            provider=provider,
                            dimension=dimension,
                            source_metadata=source_metadata,
                            source_parser=source_parser,
                        ),
                    )
                )
        return results

    def _call_with_retry(self, texts: list[str], source_id: str) -> list:
        """Call embed_batch with up to ``_max_retries`` retries on failure."""
        attempts = self._max_retries + 1
        for attempt in range(1, attempts + 1):
            try:
                return self._client.embed_batch(texts)
            except EmbeddingClientError as exc:
                if _is_non_retryable(exc):
                    logger.warning("Skipping non-retryable batch embed error for '%s': %s", source_id, exc)
                    return [None] * len(texts)
                logger.warning(
                    "Batch embed attempt %d/%d failed for '%s': %s",
                    attempt, attempts, source_id, exc,
                )
                if attempt < attempts:
                    time.sleep(self._retry_delay)
        return [None] * len(texts)
