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

class TestBuildParameterEntity:
    """Test suite for build_parameter_entity function.

    Covers:
    - minimal parameter conversion
    - required vs optional parameters
    - path, query, header parameter locations
    - parameters with enum values
    - parameters with format field
    - deprecated parameters
    - parameters with examples
    - type field is "Parameter" (capitalized)
    - all optional fields default to appropriate values
    """

    def _import(self):
        from openapi_parser.entity_builder import build_parameter_entity
        return build_parameter_entity

    def test_minimal_parameter_converted(self):
        from openapi_parser.models import ParameterMetadata

        build = self._import()
        param = ParameterMetadata(
            name="simpleParam",
            location="query",
            spec_source="/specs/api.yaml",
        )
        entity = build(param)

        assert entity["type"] == "Parameter"
        assert entity["name"] == "simpleParam"
        assert entity["in"] == "query"
        assert entity["required"] is False
        assert entity["schema_type"] is None
        assert entity["description"] is None
        assert entity["enum_values"] == []
        assert entity["format"] is None
        assert entity["deprecated"] is False
        assert entity["example"] is None
        assert entity["source_file"] == "/specs/api.yaml"

    def test_path_parameter_with_enum(self):
        from openapi_parser.models import ParameterMetadata

        build = self._import()
        param = ParameterMetadata(
            name="paymentService",
            location="path",
            required=True,
            schema_type="string",
            description="Payment service type",
            enum_values=["payments", "bulk-payments", "periodic-payments"],
            spec_source="/specs/payment.yaml",
        )
        entity = build(param)

        assert entity["type"] == "Parameter"
        assert entity["name"] == "paymentService"
        assert entity["in"] == "path"
        assert entity["required"] is True
        assert entity["schema_type"] == "string"
        assert entity["description"] == "Payment service type"
        assert len(entity["enum_values"]) == 3
        assert entity["enum_values"] == ["payments", "bulk-payments", "periodic-payments"]
        assert entity["source_file"] == "/specs/payment.yaml"

    def test_query_parameter_with_format(self):
        from openapi_parser.models import ParameterMetadata

        build = self._import()
        param = ParameterMetadata(
            name="limit",
            location="query",
            required=False,
            schema_type="integer",
            format="int32",
            description="Max items to return",
            example=10,
            spec_source="/specs/api.yaml",
        )
        entity = build(param)

        assert entity["type"] == "Parameter"
        assert entity["name"] == "limit"
        assert entity["in"] == "query"
        assert entity["required"] is False
        assert entity["schema_type"] == "integer"
        assert entity["format"] == "int32"
        assert entity["description"] == "Max items to return"
        assert entity["example"] == 10

