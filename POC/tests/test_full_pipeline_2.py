"""Integration tests — Phase 4 Entity Extraction pipeline.

Tests validate complete extractor pipeline execution, parser output consumption,
spaCy/LLM/embedding integration, and failure handling. External provider calls
are mocked; spaCy uses a real minimal pipeline.
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from shared.models import (
    Entity,
    ExtractionResult,
    ExtractionStatus,
    SourceMetadata,
    SourceType,
)
from extractors.embeddings.models.embedding_result import EmbeddingInputType
from extractors.llm.client.base_client import LLMClientError

class TestFullPipelineIntegration:
    """End-to-end pipeline runs without errors given mock providers."""

    def test_pipeline_continues_on_llm_failure(self, mock_embed_client, java_source) -> None:
        from extractors.embeddings.services.embedding_service import EmbeddingService
        from extractors.embeddings.services.batch_service import BatchEmbeddingService
        from extractors.llm.services.triple_service import TripleService
        from extractors.spacy.pipeline.pipeline import SpacyExtractionPipeline
        from extractors.extractor_pipeline import ExtractionPipeline
        from extractors.loader import ExtractionRecord

        bad_llm = MagicMock()
        bad_llm.model = "m"
        bad_llm.complete.side_effect = LLMClientError("provider down")

        batch_resp = MagicMock()
        batch_resp.vector = [0.5]
        batch_resp.model = "qwen3-embedding-8b"
        batch_resp.provider = "openai_compat"
        batch_resp.dimension = 1
        mock_embed_client.embed_batch.return_value = [batch_resp]

        spacy_p = SpacyExtractionPipeline.build()
        triple_s = TripleService(client=bad_llm, max_retries=0, retry_delay=0)
        embed_s = EmbeddingService(client=mock_embed_client, retry_delay=0)
        batch_s = BatchEmbeddingService(client=mock_embed_client, batch_size=10, retry_delay=0)

        ep = ExtractionPipeline(
            spacy_pipeline=spacy_p,
            triple_service=triple_s,
            embed_service=embed_s,
            batch_service=batch_s,
        )
        record = ExtractionRecord(
            text="Payment Account",
            source_metadata=java_source,
            source_parser="java_parser",
        )
        summary = ep.run([record])

        # Pipeline must complete — LLM failure recorded, not raised
        assert summary.records_processed == 1
        assert any("llm:" in f for f in summary.failures)
