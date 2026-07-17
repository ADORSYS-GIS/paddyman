"""Integration tests for OpenAPI schema composition relationships."""
from __future__ import annotations

from openapi_parser.relationship_builder import build_openapi_relationships
from openapi_parser.schema_composition_metadata import extract_schema_composition_map


def _build_entities(raw: dict) -> list[dict]:
  composition_map = extract_schema_composition_map(raw)
  entities: list[dict] = []
  for schema_name in raw["components"]["schemas"].keys():
    entities.append(
      {
        "id": f"id:{schema_name}",
        "type": "Schema",
        "name": schema_name,
        "schema_composition": composition_map.get(schema_name, []),
      }
    )
  return entities


def test_extracts_all_schema_composition_relationship_types() -> None:
  raw = {
    "components": {
      "schemas": {
        "PaymentResponse": {"allOf": [{"$ref": "#/components/schemas/BaseResponse"}]},
        "PaymentProduct": {
          "discriminator": {"propertyName": "kind"},
          "oneOf": [{"$ref": "#/components/schemas/SepaPayment"}],
        },
        "PaymentMethod": {"anyOf": [{"$ref": "#/components/schemas/CardPayment"}]},
        "NonEmptyString": {"not": {"$ref": "#/components/schemas/EmptyString"}},
        "BaseResponse": {"type": "object"},
        "SepaPayment": {"type": "object"},
        "CardPayment": {"type": "object"},
        "EmptyString": {"type": "string"},
      }
    }
  }

  relationships = build_openapi_relationships(_build_entities(raw))
  rel_types = {rel["type"] for rel in relationships}
  assert "COMPOSES_ALL_OF" in rel_types
  assert "ONE_OF" in rel_types
  assert "ANY_OF" in rel_types
  assert "NOT" in rel_types


def test_preserves_position_and_nested_composition_path() -> None:
  raw = {
    "components": {
      "schemas": {
        "Envelope": {
          "allOf": [
            {"$ref": "#/components/schemas/BaseEnvelope"},
            {
              "type": "object",
              "discriminator": {"propertyName": "payloadKind"},
              "oneOf": [
                {"$ref": "#/components/schemas/CardBody"},
                {"$ref": "#/components/schemas/TransferBody"},
              ],
            },
          ]
        },
        "BaseEnvelope": {"type": "object"},
        "CardBody": {"type": "object"},
        "TransferBody": {"type": "object"},
      }
    }
  }

  relationships = build_openapi_relationships(_build_entities(raw))
  all_of = [rel for rel in relationships if rel["type"] == "COMPOSES_ALL_OF"]
  one_of = [rel for rel in relationships if rel["type"] == "ONE_OF"]

  assert any(rel["properties"].get("position") == 0 for rel in all_of)
  assert any(rel["properties"].get("position") == 0 for rel in one_of)
  assert any(rel["properties"].get("path") == "allOf[1]" for rel in one_of)
  assert any(rel["properties"].get("discriminator") == "payloadKind" for rel in one_of)
