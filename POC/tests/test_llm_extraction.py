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

class TestLLMExtractionIntegration:
    """LLM extraction and triple generation with a mocked client."""

    def test_triple_service_produces_result(self, mock_llm_client, java_source) -> None:
        from services.triple_service import TripleService

        service = TripleService(client=mock_llm_client)
        triples, result = service.run(
            text="class PaymentService { void initiate() {} }",
            source_metadata=java_source,
            source_parser="java_parser",
        )

        assert isinstance(result, ExtractionResult)
        assert result.status != ExtractionStatus.FAILED or result.entities  # not empty failure

    def test_triple_service_on_failed_llm(self, java_source) -> None:
        from client.base_client import LLMClientError
        from services.triple_service import TripleService

        bad_client = MagicMock()
        bad_client.model = "m"
        bad_client.complete.side_effect = LLMClientError("timeout")

        service = TripleService(client=bad_client, max_retries=0, retry_delay=0)
        triples, result = service.run(text="class Foo {}", source_metadata=java_source)

        assert result.status == ExtractionStatus.FAILED
        assert triples == []


# ---------------------------------------------------------------------------
# Embedding integration tests
# ---------------------------------------------------------------------------

