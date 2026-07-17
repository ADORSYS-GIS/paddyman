"""Integration test: parameters become first-class entities and are linked.

Verifies that both inline (path/operation) parameters and reusable
`components.parameters` are emitted as `Parameter` entities and that
`HAS_PARAMETER` relationships are created linking endpoints/operations
to those entities.
"""
from __future__ import annotations

from pathlib import Path


def test_parameters_emitted_and_linked(tmp_path: Path):
    spec = """
openapi: 3.0.1
info:
  title: Test API
  version: 1.0.0
paths:
  /pets/{petId}:
    parameters:
      - name: sharedParam
        in: header
        required: false
        schema:
          type: string
    get:
      operationId: getPet
      parameters:
        - name: petId
          in: path
          required: true
          schema:
            type: string
        - $ref: '#/components/parameters/GlobalLimit'
      responses:
        '200':
          description: OK
components:
  parameters:
    GlobalLimit:
      name: limit
      in: query
      description: Global limit
      required: false
      schema:
        type: integer
"""

    spec_path = tmp_path / "test_spec.yaml"
    spec_path.write_text(spec)

    from openapi_parser.document_entities_builder import build_openapi_document_with_entities
    from openapi_parser.relationship_builder import build_openapi_relationships

    doc, entities = build_openapi_document_with_entities(tmp_path, spec_path)

    params = [e for e in entities if e.get("type") == "Parameter"]
    # Expect both inline path parameter and reusable component parameter
    assert any(p.get("name") == "petId" and p.get("in") == "path" for p in params)
    assert any(p.get("name") == "limit" and p.get("in") == "query" for p in params)

    # Provenance/source file should be present
    assert any(p.get("name") == "limit" and p.get("source_file") == str(spec_path) for p in params)

    relationships = build_openapi_relationships(entities)
    # There should be HAS_PARAMETER links for both parameters
    assert any(r.get("type") == "HAS_PARAMETER" and r.get("properties", {}).get("parameter_name") == "petId" for r in relationships)
    assert any(r.get("type") == "HAS_PARAMETER" and r.get("properties", {}).get("parameter_name") == "limit" for r in relationships)
