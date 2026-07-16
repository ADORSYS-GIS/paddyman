"""Unit tests for openapi_parser.entity_builder.

Covers:
- converting EndpointMetadata to entity dict
- all fields present in output
- optional fields as None when absent
- parameters list conversion
- type field is "Endpoint" (capitalized)
"""
from __future__ import annotations

import pytest

class TestBuildSchemaEntity:
    """Test suite for build_schema_entity function.

    Covers:
    - minimal schema conversion
    - object schema with properties and required fields
    - enum schema with enum_values
    - schema with composition refs (allOf/oneOf/anyOf)
    - property with $ref
    - property with inline enum
    - property with format field
    - type field is "Schema" (capitalized)
    - all optional fields default to empty lists
    """

    def _import(self):
        from openapi_parser.entity_builder import build_schema_entity
        return build_schema_entity

    def test_minimal_schema_converted(self):
        from openapi_parser.models import SchemaMetadata

        build = self._import()
        schema = SchemaMetadata(
            type="schema",
            name="SimpleString",
            spec_source="/specs/api.yaml",
            schema_type="string",
        )
        entity = build(schema)

        assert entity["type"] == "Schema"
        assert entity["name"] == "SimpleString"
        assert entity["schema_type"] == "string"
        assert entity["description"] is None
        assert entity["source_file"] == "/specs/api.yaml"
        assert entity["properties"] == []
        assert entity["required"] == []
        assert entity["enum_values"] == []
        assert entity["refs"] == []

    def test_object_schema_with_properties(self):
        from openapi_parser.models import PropertyMetadata, SchemaMetadata

        build = self._import()
        schema = SchemaMetadata(
            type="schema",
            name="PaymentRequest",
            spec_source="/specs/payment.yaml",
            schema_type="object",
            description="A payment request DTO.",
            properties=[
                PropertyMetadata(
                    name="amount",
                    type="number",
                    description="Payment amount.",
                    required=True,
                ),
                PropertyMetadata(
                    name="currency",
                    type="string",
                    description="ISO 4217 currency code.",
                    required=True,
                ),
                PropertyMetadata(
                    name="reference",
                    type="string",
                    description="Optional reference.",
                    required=False,
                ),
            ],
            required=["amount", "currency"],
        )
        entity = build(schema)

        assert entity["type"] == "Schema"
        assert entity["name"] == "PaymentRequest"
        assert entity["schema_type"] == "object"
        assert entity["description"] == "A payment request DTO."
        assert len(entity["properties"]) == 3
        assert entity["required"] == ["amount", "currency"]
        assert entity["enum_values"] == []
        assert entity["refs"] == []

        # Verify properties
        prop1 = entity["properties"][0]
        assert prop1["name"] == "amount"
        assert prop1["type"] == "number"
        assert prop1["description"] == "Payment amount."
        assert prop1["required"] is True

        prop2 = entity["properties"][1]
        assert prop2["name"] == "currency"
        assert prop2["type"] == "string"

        prop3 = entity["properties"][2]
        assert prop3["name"] == "reference"
        assert prop3["required"] is False

