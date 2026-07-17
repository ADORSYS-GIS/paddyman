"""Integration tests for Response entities in OpenAPI output."""
from __future__ import annotations

import json
import sys
from pathlib import Path

_POC_ROOT = Path(__file__).resolve().parents[2]
_PARSERS_ROOT = _POC_ROOT / "2_Parsers"
for _path in (str(_POC_ROOT), str(_PARSERS_ROOT)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from parsers.openapi_file_output import write_openapi_file_normalized_jsons


def _render_payload(tmp_path: Path, spec_content: str) -> dict:
    spec_dir = tmp_path / "specs"
    spec_dir.mkdir(parents=True)
    (spec_dir / "payment.yaml").write_text(spec_content, encoding="utf-8")
    output_dir = tmp_path / "output"
    paths = write_openapi_file_normalized_jsons(source_dir=spec_dir, output_dir=output_dir)
    return json.loads(paths[0].read_text(encoding="utf-8"))


def test_creates_response_entities_and_relationships(tmp_path: Path) -> None:
    payload = _render_payload(
        tmp_path,
        """openapi: 3.0.1
info:
  title: Payment API
  version: 1.0.0
paths:
  /payments:
    post:
      responses:
        '201':
          description: Created
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PaymentResponse'
components:
  schemas:
    PaymentResponse:
      type: object
""",
    )

    entities = payload["entities"]
    endpoint = next(e for e in entities if e["type"] == "Endpoint")
    response = next(e for e in entities if e["type"] == "Response")

    assert "responses" not in endpoint
    assert endpoint["response_match_keys"]["201"] == response["match_key"]
    assert response["properties"]["status_code"] == "201"

    rels = payload["relationships"]
    assert any(r["type"] == "HAS_RESPONSE" for r in rels)
    assert any(r["type"] == "USES_SCHEMA" for r in rels)


def test_extracts_shared_response_once(tmp_path: Path) -> None:
    payload = _render_payload(
        tmp_path,
        """openapi: 3.0.1
info:
  title: Payment API
  version: 1.0.0
paths:
  /payments:
    post:
      responses:
        '201':
          $ref: '#/components/responses/CREATED_201_Payment'
  /payments/{id}:
    get:
      responses:
        '201':
          $ref: '#/components/responses/CREATED_201_Payment'
components:
  responses:
    CREATED_201_Payment:
      description: Created
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/PaymentResponse'
  schemas:
    PaymentResponse:
      type: object
""",
    )

    responses = [e for e in payload["entities"] if e["type"] == "Response"]
    has_response = [r for r in payload["relationships"] if r["type"] == "HAS_RESPONSE"]

    assert len(responses) == 1
    assert responses[0]["properties"]["reusable"] is True
    assert len(has_response) == 2
