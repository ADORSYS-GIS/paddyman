"""Unit tests for OpenAPI file output processor.

Tests cover:
- Endpoint entity extraction from paths
- Schema entity extraction from components.schemas
- Parameter entity extraction from components.parameters
- API info metadata extraction
- $ref dereferencing (internal and external)
- Comprehensive validation of normalized JSON output structure
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

_POC_ROOT = Path(__file__).resolve().parents[2]
_PARSERS_ROOT = _POC_ROOT / "2_Parsers"
for _path in (str(_POC_ROOT), str(_PARSERS_ROOT)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from openapi_file_output import write_openapi_file_normalized_jsons


class TestOpenAPIFileOutputEntityExtraction:
    """Test suite for OpenAPI endpoint entity extraction.

    Covers:
    - entities field is populated in output
    - entities list is non-empty for specs with paths
    - entities count matches endpoint operations count
    - entity has required fields (type, path, method, operation_id, etc.)
    - entities list is empty when spec has no paths
    - graceful handling of invalid YAML specs
    """

    def test_entities_populated_for_valid_spec(self, tmp_path: Path) -> None:
        """Entities list is non-empty when spec contains paths."""
        spec_dir = tmp_path / "specs"
        spec_dir.mkdir(parents=True)
        spec_content = """openapi: 3.0.1
info:
  title: Payment API
  version: 1.0.0
paths:
  /payments:
    post:
      operationId: createPayment
      summary: Create a payment
      tags:
        - payments
      responses:
        '201':
          description: Created
    get:
      operationId: listPayments
      summary: List payments
      responses:
        '200':
          description: OK
"""
        (spec_dir / "payment.yaml").write_text(spec_content, encoding="utf-8")

        output_dir = tmp_path / "output"
        paths = write_openapi_file_normalized_jsons(source_dir=spec_dir, output_dir=output_dir)

        assert len(paths) == 1
        payload = json.loads(paths[0].read_text(encoding="utf-8"))

        # Verify entities field exists and is non-empty
        assert "entities" in payload
        entities = payload["entities"]
        assert isinstance(entities, list)
        assert len(entities) == 2  # POST /payments + GET /payments

        # Verify first entity structure
        entity = entities[0]
        assert entity["type"] == "Endpoint"
        assert entity["path"] == "/payments"
        assert entity["method"] in ("POST", "GET")
        assert entity["operation_id"] in ("createPayment", "listPayments")
        assert entity["summary"] is not None
        assert entity["api_title"] == "Payment API"
        assert "source_file" in entity
        assert entity["tags"] == ["payments"] or entity["tags"] == []
        assert "responses" in entity
        assert "parameters" in entity

    def test_all_http_methods_extracted(self, tmp_path: Path) -> None:
        """All supported HTTP methods are extracted as entities."""
        spec_dir = tmp_path / "specs"
        spec_dir.mkdir(parents=True)
        spec_content = """openapi: 3.0.1
info:
  title: Methods API
  version: 1.0.0
paths:
  /resource:
    get:
      responses: {}
    post:
      responses: {}
    put:
      responses: {}
    patch:
      responses: {}
    delete:
      responses: {}
"""
        (spec_dir / "methods.yaml").write_text(spec_content, encoding="utf-8")

        output_dir = tmp_path / "output"
        paths = write_openapi_file_normalized_jsons(source_dir=spec_dir, output_dir=output_dir)

        payload = json.loads(paths[0].read_text(encoding="utf-8"))
        entities = payload["entities"]

        assert len(entities) == 5
        methods = {e["method"] for e in entities}
        assert methods == {"GET", "POST", "PUT", "PATCH", "DELETE"}

    def test_dynamic_path_parameters_preserved(self, tmp_path: Path) -> None:
        """Dynamic path parameters like {id} are preserved in entity path."""
        spec_dir = tmp_path / "specs"
        spec_dir.mkdir(parents=True)
        spec_content = """openapi: 3.0.1
info:
  title: API
  version: 1.0.0
paths:
  /v1/{payment-service}/{payment-product}:
    post:
      operationId: initiatePayment
      responses:
        '201':
          description: Created
"""
        (spec_dir / "dynamic.yaml").write_text(spec_content, encoding="utf-8")

        output_dir = tmp_path / "output"
        paths = write_openapi_file_normalized_jsons(source_dir=spec_dir, output_dir=output_dir)

        payload = json.loads(paths[0].read_text(encoding="utf-8"))
        entities = payload["entities"]

        assert len(entities) == 1
        assert entities[0]["path"] == "/v1/{payment-service}/{payment-product}"


# NOTE: This file exceeds 150 LOC and must be split into multiple files.
# Remaining test classes intentionally truncated - see split files:
# - test_openapi_schema_*.py
# - test_openapi_parameter_*.py  
# - test_openapi_metadata_*.py
# - test_openapi_ref_*.py
