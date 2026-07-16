"""Integration tests for RequestBody entities in OpenAPI output."""
from __future__ import annotations

import json
import sys
from pathlib import Path

_POC_ROOT = Path(__file__).resolve().parents[2]
_PARSERS_ROOT = _POC_ROOT / "2_Parsers"
for _path in (str(_POC_ROOT), str(_PARSERS_ROOT)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from openapi_file_output import write_openapi_file_normalized_jsons


def _render_payload(tmp_path: Path, spec_content: str) -> dict:
    spec_dir = tmp_path / "specs"
    spec_dir.mkdir(parents=True)
    (spec_dir / "payment.yaml").write_text(spec_content, encoding="utf-8")
    output_dir = tmp_path / "output"
    paths = write_openapi_file_normalized_jsons(source_dir=spec_dir, output_dir=output_dir)
    return json.loads(paths[0].read_text(encoding="utf-8"))


def test_creates_request_body_entities_and_relationships(tmp_path: Path) -> None:
    payload = _render_payload(
        tmp_path,
        """openapi: 3.0.1
info:
  title: Payment API
  version: 1.0.0
paths:
  /payments:
    post:
      operationId: createPayment
      requestBody:
        required: true
        description: Payment initiation request
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/PaymentInitiation'
      responses:
        '201':
          description: Created
components:
  schemas:
    PaymentInitiation:
      type: object
      properties:
        amount:
          type: number
""",
    )

    entities = payload["entities"]
    endpoint = next(e for e in entities if e["type"] == "Endpoint")
    request_body = next(e for e in entities if e["type"] == "RequestBody")

    assert "request_body" not in endpoint
    assert endpoint["request_body_match_key"] == request_body["match_key"]
    assert request_body["properties"]["required"] is True

    rels = payload["relationships"]
    assert any(r["type"] == "HAS_REQUEST_BODY" for r in rels)
    assert any(r["type"] == "USES_SCHEMA" for r in rels)


def test_extracts_shared_request_body_once(tmp_path: Path) -> None:
    payload = _render_payload(
        tmp_path,
        """openapi: 3.0.1
info:
  title: Payment API
  version: 1.0.0
paths:
  /payments:
    post:
      requestBody:
        $ref: '#/components/requestBodies/PaymentInitiationRequest'
      responses: {}
  /payments/{id}:
    put:
      requestBody:
        $ref: '#/components/requestBodies/PaymentInitiationRequest'
      responses: {}
components:
  requestBodies:
    PaymentInitiationRequest:
      required: false
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/PaymentInitiation'
  schemas:
    PaymentInitiation:
      type: object
""",
    )

    request_bodies = [e for e in payload["entities"] if e["type"] == "RequestBody"]
    has_request_body = [r for r in payload["relationships"] if r["type"] == "HAS_REQUEST_BODY"]

    assert len(request_bodies) == 1
    assert request_bodies[0]["properties"]["reusable"] is True
    assert len(has_request_body) == 2
