"""Unit tests for DTO/Enum schema classification in entity building."""
from __future__ import annotations


class TestSchemaEntityClassification:
    def _import(self):
        from openapi_parser.entity_builder import build_schema_entities

        return build_schema_entities

    def test_object_schema_with_properties_becomes_dto(self):
        from openapi_parser.models import PropertyMetadata, SchemaMetadata

        build = self._import()
        schema = SchemaMetadata(
            type="schema",
            name="PaymentInitiation",
            spec_source="/specs/payment.yaml",
            schema_type="object",
            description="Payment initiation request",
            properties=[
                PropertyMetadata(name="amount", type="number", required=True),
                PropertyMetadata(name="remittance", type="string", required=False),
            ],
            required=["amount"],
        )

        entities = build(schema)
        dto = next(e for e in entities if e["type"] == "DTO")
        property_schemas = [e for e in entities if e["type"] == "Schema"]

        assert dto["name"] == "PaymentInitiation"
        assert dto["properties"]["property_count"] == 2
        assert dto["properties"]["required_fields"] == ["amount"]
        assert len(property_schemas) == 2

    def test_enum_schema_becomes_enum_and_value_entities(self):
        from openapi_parser.models import SchemaMetadata

        build = self._import()
        schema = SchemaMetadata(
            type="schema",
            name="PaymentProduct",
            spec_source="/specs/payment.yaml",
            schema_type="string",
            enum_values=["sepa", "instant"],
        )

        entities = build(schema)
        enum_entity = next(e for e in entities if e["type"] == "Enum")
        enum_values = [e for e in entities if e["type"] == "EnumValue"]

        assert enum_entity["properties"]["values"] == ["sepa", "instant"]
        assert enum_entity["properties"]["value_count"] == 2
        assert len(enum_values) == 2

    def test_numeric_enum_values_supported(self):
        from openapi_parser.models import SchemaMetadata

        build = self._import()
        schema = SchemaMetadata(
            type="schema",
            name="RetryCount",
            spec_source="/specs/payment.yaml",
            schema_type="integer",
            enum_values=[1, 2, 3],
        )

        entities = build(schema)
        enum_entity = next(e for e in entities if e["type"] == "Enum")

        assert enum_entity["properties"]["base_type"] == "integer"
        assert enum_entity["properties"]["values"] == [1, 2, 3]

    def test_simple_schema_remains_schema(self):
        from openapi_parser.models import SchemaMetadata

        build = self._import()
        schema = SchemaMetadata(
            type="schema",
            name="SimpleType",
            spec_source="/specs/payment.yaml",
            schema_type="string",
        )

        entities = build(schema)

        assert len(entities) == 1
        assert entities[0]["type"] == "Schema"
        assert entities[0]["name"] == "SimpleType"
