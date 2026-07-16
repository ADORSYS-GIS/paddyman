"""Tests for schema composition relationship extraction."""
from __future__ import annotations

from openapi_parser.relationship_builder import build_openapi_relationships


def _schema(entity_id: str, name: str, composition: list[dict[str, object]]) -> dict[str, object]:
    return {
        "id": entity_id,
        "type": "Schema",
        "name": name,
        "schema_composition": composition,
    }


def test_emits_all_composition_relationship_types() -> None:
    entities = [
        _schema(
            "schema-payment-response",
            "PaymentResponse",
            [
                {
                    "relationship_type": "COMPOSES_ALL_OF",
                    "composition_type": "allOf",
                    "position": 0,
                    "target_schema": "BaseResponse",
                    "ref_path": "#/components/schemas/BaseResponse",
                }
            ],
        ),
        _schema(
            "schema-payment-product",
            "PaymentProduct",
            [
                {
                    "relationship_type": "ONE_OF",
                    "composition_type": "oneOf",
                    "position": 0,
                    "target_schema": "SepaPayment",
                    "discriminator": "paymentType",
                    "ref_path": "#/components/schemas/SepaPayment",
                }
            ],
        ),
        _schema(
            "schema-payment-method",
            "PaymentMethod",
            [
                {
                    "relationship_type": "ANY_OF",
                    "composition_type": "anyOf",
                    "position": 0,
                    "target_schema": "CardPayment",
                    "ref_path": "#/components/schemas/CardPayment",
                }
            ],
        ),
        _schema(
            "schema-non-empty",
            "NonEmptyString",
            [
                {
                    "relationship_type": "NOT",
                    "composition_type": "not",
                    "target_schema": "EmptyString",
                    "ref_path": "#/components/schemas/EmptyString",
                }
            ],
        ),
        _schema("schema-base-response", "BaseResponse", []),
        _schema("schema-sepa", "SepaPayment", []),
        _schema("schema-card", "CardPayment", []),
        _schema("schema-empty", "EmptyString", []),
    ]

    relationships = build_openapi_relationships(entities)
    rel_types = {rel["type"] for rel in relationships}

    assert "COMPOSES_ALL_OF" in rel_types
    assert "ONE_OF" in rel_types
    assert "ANY_OF" in rel_types
    assert "NOT" in rel_types


def test_preserves_position_discriminator_and_nested_path() -> None:
    entities = [
        _schema(
            "schema-order",
            "OrderPayload",
            [
                {
                    "relationship_type": "COMPOSES_ALL_OF",
                    "composition_type": "allOf",
                    "position": 0,
                    "target_schema": "BaseOrder",
                    "ref_path": "#/components/schemas/BaseOrder",
                    "path": "",
                },
                {
                    "relationship_type": "ONE_OF",
                    "composition_type": "oneOf",
                    "position": 1,
                    "target_schema": "CardOrder",
                    "discriminator": "kind",
                    "ref_path": "#/components/schemas/CardOrder",
                    "path": "allOf[1]",
                },
            ],
        ),
        _schema("schema-base", "BaseOrder", []),
        _schema("schema-card", "CardOrder", []),
    ]

    relationships = build_openapi_relationships(entities)
    all_of = next(rel for rel in relationships if rel["type"] == "COMPOSES_ALL_OF")
    one_of = next(rel for rel in relationships if rel["type"] == "ONE_OF")

    assert all_of["properties"]["position"] == 0
    assert one_of["properties"]["position"] == 1
    assert one_of["properties"]["discriminator"] == "kind"
    assert one_of["properties"]["path"] == "allOf[1]"
