"""Shared test fixtures for the LLM extractor test suite."""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# POC/ and llm/ on sys.path (pytest.ini pythonpath handles it at collection
# time; this block ensures the same when conftest is imported directly).
_llm_root = str(Path(__file__).resolve().parents[1])
_poc_root = str(Path(__file__).resolve().parents[3])
for _p in (_llm_root, _poc_root):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from shared.models import SourceMetadata, SourceType


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
        metadata={
            "repository": "berlin-group",
            "file_path": "/docs/psd2_guidelines.md",
        },
    )


@pytest.fixture()
def mock_llm_client():
    """A mock BaseLLMClient that returns configurable responses."""
    client = MagicMock()
    client.model = "glm-4-flash"
    return client


def make_completion_response(content: str, model: str = "glm-4-flash"):
    """Build a mock CompletionResponse."""
    from client.base_client import CompletionResponse
    return CompletionResponse(
        content=content,
        model=model,
        usage={"prompt_tokens": 50, "completion_tokens": 100, "total_tokens": 150},
    )
