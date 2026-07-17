"""Tests for schema composition metadata extraction from raw specs."""
from __future__ import annotations

from openapi_parser.schema_composition_metadata import extract_schema_composition_map


def test_extracts_all_of_one_of_any_of_and_not() -> None:
    raw = {
        "components": {
            "schemas": {
                "PaymentResponse": {
                    "allOf": [{"$ref": "#/components/schemas/BaseResponse"}],
                    "oneOf": [{"$ref": "#/components/schemas/SepaPayment"}],
                    "anyOf": [{"$ref": "#/components/schemas/CardPayment"}],
                    "not": {"$ref": "#/components/schemas/EmptyString"},
                    "discriminator": {"propertyName": "paymentType"},
                }
            }
        }
    }

    composition_map = extract_schema_composition_map(raw)
    rels = composition_map["PaymentResponse"]
    rel_types = {rel["relationship_type"] for rel in rels}

    assert rel_types == {"COMPOSES_ALL_OF", "ONE_OF", "ANY_OF", "NOT"}
    one_of = next(rel for rel in rels if rel["relationship_type"] == "ONE_OF")
    assert one_of["discriminator"] == "paymentType"
    assert one_of["position"] == 0


def test_handles_inline_and_nested_composition() -> None:
    raw = {
        "components": {
            "schemas": {
                "Envelope": {
                    "allOf": [
                        {"$ref": "#/components/schemas/BaseEnvelope"},
                        {
                            "type": "object",
                            "oneOf": [
                                {"$ref": "#/components/schemas/CardBody"},
                                {"$ref": "#/components/schemas/TransferBody"},
                            ],
                            "discriminator": {"propertyName": "kind"},
                        },
                    ]
                }
            }
        }
    }

    composition_map = extract_schema_composition_map(raw)
    rels = composition_map["Envelope"]

    top_inline = next(
        rel for rel in rels if rel["composition_type"] == "allOf" and rel["position"] == 1
    )
    nested_one_of = [rel for rel in rels if rel["composition_type"] == "oneOf"]

    assert top_inline["inline"] is True
    assert len(nested_one_of) == 2
    assert nested_one_of[0]["path"] == "allOf[1]"
    assert nested_one_of[0]["discriminator"] == "kind"
