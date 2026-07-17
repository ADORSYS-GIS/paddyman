"""Unit tests for OpenAPI Tag entity extraction and relationships."""
from __future__ import annotations

from pathlib import Path

from parsers.openapi_parser.document_entities_builder import build_openapi_document_with_entities
from parsers.openapi_parser.operation_relationships import build_operation_relationships


def test_global_tags_are_created_and_linked(tmp_path: Path) -> None:
    spec_dir = tmp_path / "specs"
    spec_dir.mkdir(parents=True, exist_ok=True)
    spec_path = spec_dir / "payment.yaml"
    spec_content = """
openapi: 3.0.1
info:
  title: Payment API
  version: 1.0.0
tags:
  - name: payments
    description: Payment operations
  - name: pis
    description: PIS operations
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

    doc, entities = build_openapi_document_with_entities(spec_dir, spec_path)

    operations = [e for e in entities if e.get("type") == "Operation"]
    tags = [e for e in entities if e.get("type") == "Tag"]

    # Ensure tags created and descriptions preserved
    assert len(tags) == 2
    tag_map = {t.get("name"): t for t in tags}
    assert tag_map["payments"].get("description") == "Payment operations"
    assert tag_map["pis"].get("description") == "PIS operations"

    # Ensure operation exists and is linked via relationship builder
    assert len(operations) == 1
    rels = build_operation_relationships(entities)
    tagged = [r for r in rels if r.get("type") == "TAGGED_AS"]
    assert len(tagged) == 2
    # Operation id appears as source in each TAGGED_AS
    op_id = operations[0].get("id")
    assert all(r.get("source_entity_id") == op_id for r in tagged)
