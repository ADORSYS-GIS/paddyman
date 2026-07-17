"""Shared fixtures for POC-level integration tests."""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock

from shared.models import SourceMetadata, SourceType


@pytest.fixture()
def java_source() -> SourceMetadata:
    return SourceMetadata(
        source_id="PaymentService",
        source_type=SourceType.DOCUMENT,
        location="/repos/aspsp-xs2a/src/PaymentService.java",
        metadata={"repository": "aspsp-xs2a", "module": "payments", "file_path": "/src/PaymentService.java"},
    )


@pytest.fixture()
def openapi_source() -> SourceMetadata:
    return SourceMetadata(
        source_id="nextgenpsd2-spec",
        source_type=SourceType.API,
        location="/specs/nextgenpsd2_1_3/openapi.yaml",
        metadata={"repository": "berlin-group", "file_path": "/specs/nextgenpsd2_1_3/openapi.yaml"},
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
def mock_embed_response():
    """Mock embedding response with vector, model, provider, and dimension."""
    resp = MagicMock()
    resp.vector = [0.1, 0.2, 0.3, 0.4]
    resp.model = "qwen3-embedding-8b"
    resp.provider = "openai_compat"
    resp.dimension = 4
    return resp


@pytest.fixture()
def mock_embed_client(mock_embed_response):
    client = MagicMock()
    client.model = "qwen3-embedding-8b"
    client.provider_name = "openai_compat"
    client.embed.return_value = mock_embed_response
    client.embed_batch.return_value = [mock_embed_response]
    return client


@pytest.fixture()
def mock_llm_client():
    client = MagicMock()
    client.model = "glm-5"
    response_json = (
        '{"entities": [{"type": "Schema", "name": "Payment", "source": "src"}],'
        ' "relationships": []}'
    )
    mock_resp = MagicMock()
    mock_resp.content = response_json
    mock_resp.model = "glm-5"
    mock_resp.usage = {}
    client.complete.return_value = mock_resp
    return client

