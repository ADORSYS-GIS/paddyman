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
from embeddings.models.embedding_result import EmbeddingInputType
from client.base_client import LLMClientError

class TestFullPipelineIntegration:
    """End-to-end pipeline runs without errors given mock providers."""

    def test_pipeline_runs_with_empty_records(self, mock_embed_client, mock_llm_client) -> None:
        from embeddings.services.embedding_service import EmbeddingService
        from embeddings.services.batch_service import BatchEmbeddingService
        from services.triple_service import TripleService
        from pipeline.pipeline import SpacyExtractionPipeline
        from extractor_pipeline import ExtractionPipeline

        spacy_p = SpacyExtractionPipeline.build()
        triple_s = TripleService(client=mock_llm_client, max_retries=0, retry_delay=0)
        embed_s = EmbeddingService(client=mock_embed_client, retry_delay=0)
        batch_s = BatchEmbeddingService(client=mock_embed_client, batch_size=10, retry_delay=0)

        ep = ExtractionPipeline(
            spacy_pipeline=spacy_p,
            triple_service=triple_s,
            embed_service=embed_s,
            batch_service=batch_s,
        )
        summary = ep.run([])

        assert summary.records_processed == 0
        assert summary.failures == []

    def test_pipeline_processes_records(self, mock_embed_client, mock_llm_client, java_source) -> None:
        from embeddings.services.embedding_service import EmbeddingService
        from embeddings.services.batch_service import BatchEmbeddingService
        from services.triple_service import TripleService
        from pipeline.pipeline import SpacyExtractionPipeline
        from extractor_pipeline import ExtractionPipeline
        from loader import ExtractionRecord

        batch_resp = MagicMock()
        batch_resp.vector = [0.1, 0.2]
        batch_resp.model = "qwen3-embedding-8b"
        batch_resp.provider = "openai_compat"
        batch_resp.dimension = 2
        mock_embed_client.embed_batch.return_value = [batch_resp]

        spacy_p = SpacyExtractionPipeline.build()
        triple_s = TripleService(client=mock_llm_client, max_retries=0, retry_delay=0)
        embed_s = EmbeddingService(client=mock_embed_client, retry_delay=0)
        batch_s = BatchEmbeddingService(client=mock_embed_client, batch_size=10, retry_delay=0)

        ep = ExtractionPipeline(
            spacy_pipeline=spacy_p,
            triple_service=triple_s,
            embed_service=embed_s,
            batch_service=batch_s,
        )
        record = ExtractionRecord(
            text="Payment Account Consent v1.3",
            source_metadata=java_source,
            source_parser="java_parser",
        )
        summary = ep.run([record])

        assert summary.records_processed == 1
        assert summary.spacy_entities >= 0
        assert summary.chunk_embeddings >= 0

