"""Shared fixtures for POC-level integration tests."""
from __future__ import annotations

import sys
from pathlib import Path

# POC/ must be on sys.path for all shared.* imports.
_poc_root = str(Path(__file__).resolve().parent)
if _poc_root not in sys.path:
    sys.path.insert(0, _poc_root)

# Pre-import the real `spacy` library before we add 3_Extractors/ to sys.path.
# 3_Extractors/spacy/ contains the project's rule-based extractor package which
# shares the name "spacy"; pre-importing locks the real library into sys.modules
# so subsequent `import spacy` calls always resolve to it.
import spacy as _real_spacy  # noqa: F401  (side-effect import)

# Add 4_Extractors/ so that `embeddings`, `llm`, and extractor sub-packages
# are importable as top-level packages.  Since the real `spacy` is already in
# sys.modules this does NOT shadow the installed spaCy library.
# llm is inserted AFTER embeddings so that `from client.base_client import LLMClientError`
# resolves to the LLM client — the same module ExtractionService imports and catches.
_extractors_root = str(Path(__file__).resolve().parent.parent / "4_Extractors")
_spacy_root = str(Path(__file__).resolve().parent.parent / "4_Extractors" / "spacy")
_embed_root = str(Path(__file__).resolve().parent.parent / "4_Extractors" / "embeddings")
_llm_root = str(Path(__file__).resolve().parent.parent / "4_Extractors" / "llm")

for _p in (_spacy_root, _extractors_root, _embed_root, _llm_root):
    if _p not in sys.path:
        sys.path.insert(0, _p)


# ---------------------------------------------------------------------------
# Shared test fixtures
# ---------------------------------------------------------------------------
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

