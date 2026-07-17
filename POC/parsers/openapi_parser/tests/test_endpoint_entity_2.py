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

    def test_type_field_capitalized(self):
        from openapi_parser.models import EndpointMetadata

        build = self._import()
        ep = EndpointMetadata(
            type="endpoint",
            method="DELETE",
            path="/resource/{id}",
            api_title="API",
            spec_source="/spec.yaml",
        )
        entity = build(ep)
        # Requirement: type field is "Endpoint" (capital E) in entity
        assert entity["type"] == "Endpoint"

    def test_dynamic_path_parameters_preserved(self):
        from openapi_parser.models import EndpointMetadata

        build = self._import()
        ep = EndpointMetadata(
            type="endpoint",
            method="GET",
            path="/v1/{payment-service}/{payment-product}",
            api_title="PSD2 API",
            spec_source="/psd2.yaml",
        )
        entity = build(ep)
        # Dynamic path params like {payment-service} must be preserved as-is
        assert entity["path"] == "/v1/{payment-service}/{payment-product}"

    def test_empty_tags_list(self):
        from openapi_parser.models import EndpointMetadata

        build = self._import()
        ep = EndpointMetadata(
            type="endpoint",
            method="PUT",
            path="/update",
            api_title="API",
            spec_source="/spec.yaml",
            tags=[],
        )
        entity = build(ep)
        assert "tags" not in entity

    def test_response_match_keys_present_without_embedding(self):
        from openapi_parser.models import EndpointMetadata

        build = self._import()
        ep = EndpointMetadata(
            type="endpoint",
            method="GET",
            path="/data",
            api_title="API",
            spec_source="/spec.yaml",
            responses={
                "200": {"description": "OK", "content": {"application/json": {}}},
                "404": {"description": "Not Found"},
            },
        )
        entity = build(ep)
        assert "response_match_keys" in entity
        assert set(entity["response_match_keys"].keys()) == {"200", "404"}
        assert "responses" not in entity

    def test_request_body_ref_extraction(self):
        """Endpoint with $ref in request body produces request_body_ref."""
        from openapi_parser.models import EndpointMetadata

        build = self._import()
        ep = EndpointMetadata(
            type="endpoint",
            method="POST",
            path="/payments",
            api_title="Payment API",
            spec_source="/specs/payment.yaml",
            request_body={"$ref": "#/components/requestBodies/paymentInitiation"},
        )
        entity = build(ep)
        
        assert entity["request_body_ref"] == "#/components/requestBodies/paymentInitiation"

    def test_response_refs_extraction(self):
        """Endpoint with $ref in responses produces response_refs map."""
        from openapi_parser.models import EndpointMetadata

        build = self._import()
        ep = EndpointMetadata(
            type="endpoint",
            method="POST",
            path="/payments",
            api_title="Payment API",
            spec_source="/specs/payment.yaml",
            responses={
                "201": {"$ref": "#/components/responses/CREATED_201_PaymentInitiation"},
                "400": {"$ref": "#/components/responses/BAD_REQUEST_400_PIS"},
                "500": {"description": "Internal server error"},
            },
        )
        entity = build(ep)
        
        assert entity["response_refs"]["201"] == "#/components/responses/CREATED_201_PaymentInitiation"
        assert entity["response_refs"]["400"] == "#/components/responses/BAD_REQUEST_400_PIS"
        assert "500" not in entity["response_refs"]  # no $ref

    def test_no_request_body_ref(self):
        """Endpoint without request body has request_body_ref as None."""
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
        
        assert entity["request_body_ref"] is None
        assert entity["response_refs"] == {}
        assert entity["response_match_keys"] == {}


