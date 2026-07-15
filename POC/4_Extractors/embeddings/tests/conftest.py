"""Shared fixtures for the embedding module test suite."""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# Ensure embeddings/ and POC/ are importable during collection.
_embed_root = str(Path(__file__).resolve().parents[1])
_poc_root = str(Path(__file__).resolve().parents[3])
for _p in (_embed_root, _poc_root):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from shared.models import Entity, SourceMetadata, SourceType
from client.base_client import EmbeddingResponse
from models.embedding_result import EmbeddingInputType


@pytest.fixture()
def java_source() -> SourceMetadata:
    return SourceMetadata(
        source_id="aspsp-xs2a",
        source_type=SourceType.DOCUMENT,
        location="/repos/aspsp-xs2a/src/PaymentController.java",
        metadata={
            "repository": "aspsp-xs2a",
            "module": "payments",
            "file_path": "/repos/aspsp-xs2a/src/PaymentController.java",
            "version": "2",
        },
    )


@pytest.fixture()
def openapi_source() -> SourceMetadata:
    return SourceMetadata(
        source_id="berlin-group-api",
        source_type=SourceType.API,
        location="/specs/nextgenpsd2_1_3/openapi.yaml",
        metadata={
            "repository": "berlin-group",
            "file_path": "/specs/nextgenpsd2_1_3/openapi.yaml",
            "module": "nextgenpsd2_1_3",
        },
    )


@pytest.fixture()
def markdown_source() -> SourceMetadata:
    return SourceMetadata(
        source_id="psd2-guidelines",
        source_type=SourceType.DOCUMENT,
        location="/docs/psd2_guidelines.md",
        metadata={"repository": "berlin-group", "file_path": "/docs/psd2_guidelines.md"},
    )


@pytest.fixture()
def payment_entity() -> Entity:
    return Entity(
        type="class",
        name="PaymentService",
        source="aspsp-xs2a",
        properties={"description": "Handles payment initiation"},
    )


@pytest.fixture()
def endpoint_entity() -> Entity:
    return Entity(
        type="endpoint",
        name="POST /v1/payments",
        source="berlin-group-api",
        properties={"description": "Initiate a payment"},
    )


@pytest.fixture()
def mock_embedding_client():
    """A mock BaseEmbeddingClient returning a fixed 4-dim vector."""
    client = MagicMock()
    client.model = "qwen3-embedding-8b"
    client.provider_name = "openai_compat"
    client.embed.return_value = EmbeddingResponse(
        vector=[0.1, 0.2, 0.3, 0.4],
        model="qwen3-embedding-8b",
        provider="openai_compat",
    )
    client.embed_batch.return_value = [
        EmbeddingResponse(
            vector=[0.1, 0.2, 0.3, 0.4],
            model="qwen3-embedding-8b",
            provider="openai_compat",
        )
    ]
    return client
