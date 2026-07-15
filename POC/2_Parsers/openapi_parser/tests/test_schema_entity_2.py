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

    def test_enum_schema_with_values(self):
        from openapi_parser.models import SchemaMetadata

        build = self._import()
        schema = SchemaMetadata(
            type="schema",
            name="TransactionStatus",
            spec_source="/specs/api.yaml",
            schema_type="string",
            description="Status codes.",
            enum_values=["ACCP", "RJCT", "PDNG", "ACTC", "ACSC"],
        )
        entity = build(schema)

        assert entity["type"] == "Schema"
        assert entity["name"] == "TransactionStatus"
        assert entity["schema_type"] == "string"
        assert entity["description"] == "Status codes."
        assert len(entity["enum_values"]) == 5
        assert entity["enum_values"] == ["ACCP", "RJCT", "PDNG", "ACTC", "ACSC"]
        assert entity["properties"] == []
        assert entity["required"] == []
        assert entity["refs"] == []

    def test_schema_with_composition_refs(self):
        from openapi_parser.models import SchemaMetadata

        build = self._import()
        schema = SchemaMetadata(
            type="schema",
            name="ExtendedAccount",
            spec_source="/specs/api.yaml",
            schema_type=None,
            refs=[
                "#/components/schemas/AccountDetails",
                "#/components/schemas/ExtraFields",
            ],
        )
        entity = build(schema)

        assert entity["type"] == "Schema"
        assert entity["name"] == "ExtendedAccount"
        assert len(entity["refs"]) == 2
        assert entity["refs"][0] == "#/components/schemas/AccountDetails"
        assert entity["refs"][1] == "#/components/schemas/ExtraFields"
        assert entity["enum_values"] == []
        assert entity["properties"] == []

    def test_property_with_ref(self):
        from openapi_parser.models import PropertyMetadata, SchemaMetadata

        build = self._import()
        schema = SchemaMetadata(
            type="schema",
            name="AccountDetails",
            spec_source="/specs/api.yaml",
            schema_type="object",
            properties=[
                PropertyMetadata(
                    name="accountId",
                    ref="#/components/schemas/accountId",
                    required=True,
                ),
                PropertyMetadata(
                    name="balance",
                    type="number",
                    required=False,
                ),
            ],
            required=["accountId"],
        )
        entity = build(schema)

        assert len(entity["properties"]) == 2
        prop1 = entity["properties"][0]
        assert prop1["name"] == "accountId"
        assert prop1["ref"] == "#/components/schemas/accountId"
        assert prop1["type"] is None
        assert prop1["required"] is True

        prop2 = entity["properties"][1]
        assert prop2["name"] == "balance"
        assert prop2["type"] == "number"
        assert prop2["ref"] is None

    def test_property_with_inline_enum(self):
        from openapi_parser.models import PropertyMetadata, SchemaMetadata

        build = self._import()
        schema = SchemaMetadata(
            type="schema",
            name="OtpFormat",
            spec_source="/specs/api.yaml",
            schema_type="object",
            properties=[
                PropertyMetadata(
                    name="format",
                    type="string",
                    enum_values=["characters", "integer"],
                    required=False,
                )
            ],
        )
        entity = build(schema)

        assert len(entity["properties"]) == 1
        prop = entity["properties"][0]
        assert prop["name"] == "format"
        assert prop["type"] == "string"
        assert len(prop["enum_values"]) == 2
        assert prop["enum_values"] == ["characters", "integer"]

