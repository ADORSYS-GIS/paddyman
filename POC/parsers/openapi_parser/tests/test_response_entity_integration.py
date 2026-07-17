"""Integration test: ensure Response entities are created and linked."""
from __future__ import annotations

from pathlib import Path

from openapi_parser.document_entities_builder import build_openapi_document_with_entities


def test_response_entities_and_operation_links(tmp_path: Path) -> None:
    spec_text = """
openapi: "3.0.0"
info:
  title: Test API
  version: "1.0"
paths:
  /payments:
    post:
      operationId: createPayment
      responses:
        "200":
          description: OK
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PaymentResponse'
        "404":
          description: Not Found
components:
  schemas:
    PaymentResponse:
      type: object
      properties:
        id:
          type: string
"""

    file_path = tmp_path / "spec.yaml"
    file_path.write_text(spec_text)

    doc, entities = build_openapi_document_with_entities(tmp_path, file_path)

    responses = [e for e in entities if e.get("type") == "Response"]
    assert any(r.get("properties", {}).get("status_code") == "200" for r in responses)
    assert any(r.get("properties", {}).get("status_code") == "404" for r in responses)

    operations = [e for e in entities if e.get("type") == "Operation"]
    assert len(operations) == 1
    op = operations[0]
    op_resp_keys = op.get("response_match_keys") or {}
    assert "200" in op_resp_keys and "404" in op_resp_keys

    # Verify schema ref on the 200 response
    r200 = next(r for r in responses if r.get("properties", {}).get("status_code") == "200")
    assert isinstance(r200.get("schema_refs"), dict)
    assert "application/json" in r200.get("schema_refs")

    # Each response should have provenance attached by the document builder
    assert any(r.get("provenance") for r in responses)
