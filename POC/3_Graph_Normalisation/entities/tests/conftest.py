"""Shared fixtures for entities normalisation tests."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Ensure POC/ is importable for ``shared`` and
# 4_Graph_Normalisation/ is importable for the ``entities`` package.
_HERE = Path(__file__).resolve().parent          # tests/
_ENTITIES_ROOT = _HERE.parent                    # entities/
_GRAPH_ROOT = _ENTITIES_ROOT.parent              # 4_Graph_Normalisation/
_POC_ROOT = _HERE.parents[2]                     # POC/

for _p in (str(_POC_ROOT), str(_GRAPH_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from shared.models import Entity, ExtractionResult, ExtractionStatus, SourceMetadata, SourceType


@pytest.fixture()
def java_entity() -> Entity:
    """Entity produced by the Java parser (controller class)."""
    return Entity(
        type="controller",
        name="PaymentController",
        source="java_parser",
        properties={
            "source_parser": "java_parser",
            "repository": "aspsp-xs2a",
            "module": "xs2a-impl",
            "file_path": "src/main/java/de/adorsys/psd2/xs2a/web/controller/PaymentController.java",
            "version": "v2",
            "confidence": 1.0,
        },
    )


@pytest.fixture()
def openapi_entity() -> Entity:
    """Entity produced by the OpenAPI parser (endpoint)."""
    return Entity(
        type="endpoint",
        name="POST /payments",
        source="openapi_parser",
        properties={
            "source_parser": "openapi_parser",
            "spec_source": "DataSource/yaml_spec/psd2-api-1.3.yaml",
            "api_title": "Berlin Group PSD2 AIS API",
            "version": "1.3",
            "confidence": 1.0,
        },
    )


@pytest.fixture()
def markdown_entity() -> Entity:
    """Entity produced by the Markdown parser."""
    return Entity(
        type="concept",
        name="Payment Initiation",
        source="markdown_parser",
        properties={
            "source_parser": "markdown_parser",
            "document": "psd2-spec.md",
            "file_path": "docs/psd2-spec.md",
            "confidence": 0.9,
        },
    )


@pytest.fixture()
def spacy_entity() -> Entity:
    """Entity produced by the spaCy extractor."""
    return Entity(
        type="entity",
        name="Payment",
        source="test-doc",
        properties={
            "source_parser": "spacy",
            "label": "PAYMENT_TYPE",
            "repository": "aspsp-xs2a",
            "module": "xs2a-impl",
            "file_path": "docs/payment-guide.md",
            "document": "payment-guide.md",
            "confidence": 0.95,
        },
    )


@pytest.fixture()
def llm_entity() -> Entity:
    """Entity produced by the LLM extractor."""
    return Entity(
        type="entity",
        name="PaymentInitiation",
        source="test-doc",
        properties={
            "source_parser": "llm",
            "repository": "aspsp-xs2a",
            "confidence": 0.85,
        },
    )


@pytest.fixture()
def basic_source_meta() -> SourceMetadata:
    return SourceMetadata(
        source_id="test-source",
        source_type=SourceType.DOCUMENT,
        location="/docs/test.md",
    )


@pytest.fixture()
def extraction_result(
    java_entity: Entity,
    openapi_entity: Entity,
    basic_source_meta: SourceMetadata,
) -> ExtractionResult:
    return ExtractionResult(
        source=basic_source_meta,
        entities=[java_entity, openapi_entity],
        status=ExtractionStatus.SUCCESS,
    )
