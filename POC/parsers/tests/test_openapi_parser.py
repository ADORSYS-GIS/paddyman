from __future__ import annotations

from pathlib import Path

from parsers.openapi_parser.spec_processor import process_spec


def test_api_entity_root_contains_children(tmp_path: Path) -> None:
    spec_dir = tmp_path / "specs"
    spec_dir.mkdir(parents=True, exist_ok=True)
    spec_path = spec_dir / "payment.yaml"
    spec_content = """
openapi: 3.0.1
info:
  title: Payment API
  version: 1.0.0
paths:
  /payments:
    post:
      operationId: createPayment
      summary: Create payment
      tags: [payments, pis]
      responses:
        '201':
          description: Created
"""
    spec_path.write_text(spec_content, encoding="utf-8")

    result = process_spec(spec_path)
    assert result is not None

    api = result.get("api")
    assert isinstance(api, dict)
    assert api.get("title") == "Payment API"

    # Children should be embedded into the API object
    endpoints = api.get("endpoints") or []
    operations = api.get("operations") or []
    tags = api.get("tags") or []

    assert len(endpoints) == 1
    assert len(operations) == 1
    assert {t.get("name") for t in tags} == {"payments", "pis"}
