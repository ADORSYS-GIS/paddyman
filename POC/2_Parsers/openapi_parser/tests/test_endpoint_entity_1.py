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

class TestBuildEndpointEntity:
    def _import(self):
        from openapi_parser.entity_builder import build_endpoint_entity
        return build_endpoint_entity

    def test_minimal_endpoint_converted(self):
        from openapi_parser.models import EndpointMetadata

        build = self._import()
        ep = EndpointMetadata(
            type="endpoint",
            method="GET",
            path="/accounts",
            api_title="Banking API",
            spec_source="/specs/banking.yaml",
        )
        entity = build(ep)

        assert entity["type"] == "Endpoint"
        assert entity["method"] == "GET"
        assert entity["path"] == "/accounts"
        assert entity["api_title"] == "Banking API"
        assert entity["source_file"] == "/specs/banking.yaml"
        assert entity["parameters"] == []
        assert entity["request_body_ref"] is None
        assert entity["request_body_match_key"] is None
        assert entity["response_match_keys"] == {}

    def test_full_endpoint_converted(self):
        from openapi_parser.models import EndpointMetadata, ParameterMetadata

        build = self._import()
        ep = EndpointMetadata(
            type="endpoint",
            method="POST",
            path="/payments/{paymentId}",
            api_title="Payment API",
            spec_source="/specs/payment.yaml",
            operation_id="initiatePayment",
            summary="Initiate a payment",
            description="Full description of payment initiation",
            tags=["payments", "PIS"],
            parameters=[
                ParameterMetadata(
                    name="paymentId",
                    location="path",
                    required=True,
                    schema_type="string",
                )
            ],
            request_body={"content": {"application/json": {}}},
            responses={"201": {"description": "Created"}, "400": {"description": "Bad Request"}},
        )
        entity = build(ep)

        assert entity["type"] == "Endpoint"
        assert entity["method"] == "POST"
        assert entity["path"] == "/payments/{paymentId}"
        assert "operation_id" not in entity
        assert "summary" not in entity
        assert "description" not in entity
        assert "tags" not in entity
        assert len(entity["parameters"]) == 1
        assert entity["parameters"][0]["name"] == "paymentId"
        assert entity["parameters"][0]["location"] == "path"
        assert entity["parameters"][0]["required"] is True
        assert entity["request_body_match_key"] is not None
        assert "request_body" not in entity
        assert "201" in entity["response_match_keys"]
        assert "400" in entity["response_match_keys"]

    def test_parameters_converted(self):
        from openapi_parser.models import EndpointMetadata, ParameterMetadata

        build = self._import()
        ep = EndpointMetadata(
            type="endpoint",
            method="GET",
            path="/items",
            api_title="Items API",
            spec_source="/specs/items.yaml",
            parameters=[
                ParameterMetadata(
                    name="limit",
                    location="query",
                    required=False,
                    description="Max items to return",
                    schema_type="integer",
                    format="int32",
                    example=10,
                ),
                ParameterMetadata(
                    name="X-Request-ID",
                    location="header",
                    required=True,
                    schema_type="string",
                    format="uuid",
                ),
            ],
        )
        entity = build(ep)

        assert len(entity["parameters"]) == 2
        p1 = entity["parameters"][0]
        assert p1["name"] == "limit"
        assert p1["location"] == "query"
        assert p1["required"] is False
        assert p1["description"] == "Max items to return"
        assert p1["schema_type"] == "integer"
        assert p1["format"] == "int32"
        assert p1["example"] == 10

        p2 = entity["parameters"][1]
        assert p2["name"] == "X-Request-ID"
        assert p2["location"] == "header"
        assert p2["required"] is True

