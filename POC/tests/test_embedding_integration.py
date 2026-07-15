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

class TestEmbeddingIntegration:
    """Embeddings are generated for entities and chunks."""

    def test_entity_embeddings_generated(self, mock_embed_client, java_source) -> None:
        from embeddings.services.embedding_service import EmbeddingService

        service = EmbeddingService(client=mock_embed_client, retry_delay=0)
        entity = Entity(type="class", name="PaymentService", source="aspsp-xs2a")
        result = service.embed_entity(entity, java_source, source_parser="java_parser")

        assert result.vector == [0.1, 0.2, 0.3, 0.4]
        assert result.metadata.source_parser == "java_parser"

    def test_chunk_embeddings_generated(self, mock_embed_client, markdown_source) -> None:
        from embeddings.services.embedding_service import EmbeddingService

        service = EmbeddingService(client=mock_embed_client, retry_delay=0)
        result = service.embed_chunk(
            text="Consent-based AIS access for PSD2",
            label="AIS Consent",
            input_type=EmbeddingInputType.MARKDOWN_SECTION,
            source_metadata=markdown_source,
        )

        assert len(result.vector) == 4
        assert result.input_type == EmbeddingInputType.MARKDOWN_SECTION

    def test_batch_embeddings_for_entities(self, mock_embed_client, java_source) -> None:
        from embeddings.services.batch_service import BatchEmbeddingService

        resp_a = MagicMock()
        resp_a.vector = [0.1, 0.2]
        resp_a.model = "qwen3-embedding-8b"
        resp_a.provider = "openai_compat"
        resp_a.dimension = 2

        resp_b = MagicMock()
        resp_b.vector = [0.3, 0.4]
        resp_b.model = "qwen3-embedding-8b"
        resp_b.provider = "openai_compat"
        resp_b.dimension = 2

        mock_embed_client.embed_batch.return_value = [resp_a, resp_b]
        service = BatchEmbeddingService(client=mock_embed_client, batch_size=10, retry_delay=0)
        entities = [
            Entity(type="class", name="PaymentService", source="src"),
            Entity(type="endpoint", name="POST /payments", source="src"),
        ]
        results = service.embed_entities(entities, java_source, source_parser="java_parser")

        assert len(results) == 2
        assert all(len(r.vector) > 0 for r in results)


# ---------------------------------------------------------------------------
# Full pipeline integration tests
# ---------------------------------------------------------------------------

