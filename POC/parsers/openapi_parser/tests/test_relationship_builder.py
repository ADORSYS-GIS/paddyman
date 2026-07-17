"""Unit tests for OpenAPI relationship extraction."""
from __future__ import annotations

from uuid import uuid4

import pytest

from openapi_parser.relationship_builder import (
    build_openapi_relationships,
    extract_schema_name_from_ref,
)


class TestExtractSchemaNameFromRef:
    """Test schema name extraction from $ref paths."""

    def test_component_schema_ref(self):
        """Should extract name from component schema reference."""
        ref = "#/components/schemas/Account"
        assert extract_schema_name_from_ref(ref) == "Account"

    def test_external_file_ref(self):
        """Should extract name from external file reference."""
        ref = "./common.yaml#/components/schemas/Address"
        assert extract_schema_name_from_ref(ref) == "Address"

    def test_none_ref(self):
        """Should return None for None input."""
        assert extract_schema_name_from_ref(None) is None

    def test_empty_ref(self):
        """Should return None for empty string."""
        assert extract_schema_name_from_ref("") is None

    def test_invalid_ref(self):
        """Should return None for unrecognized format."""
        assert extract_schema_name_from_ref("invalid") is None


class TestEndpointParameterRelationships:
    """Test HAS_PARAMETER relationship extraction."""

    def test_endpoint_with_parameters(self):
        """Should create HAS_PARAMETER relationships."""
        endpoint_id = str(uuid4())
        param_id = str(uuid4())
        
        entities = [
            {
                "id": endpoint_id,
                "type": "Endpoint",
                "path": "/accounts/{accountId}",
                "method": "GET",
                "parameters": [
                    {"name": "accountId", "location": "path", "required": True}
                ]
            },
            {
                "id": param_id,
                "type": "Parameter",
                "name": "accountId",
                "in": "path"
            }
        ]
        
        relationships = build_openapi_relationships(entities)
        
        param_rels = [r for r in relationships if r["type"] == "HAS_PARAMETER"]
        assert len(param_rels) == 1
        assert param_rels[0]["source_entity_id"] == endpoint_id
        assert param_rels[0]["target_entity_id"] == param_id
        assert param_rels[0]["properties"]["parameter_name"] == "accountId"

    def test_endpoint_without_parameters(self):
        """Should handle endpoints with no parameters."""
        entities = [
            {
                "id": str(uuid4()),
                "type": "Endpoint",
                "path": "/accounts",
                "method": "GET",
                "parameters": []
            }
        ]
        
        relationships = build_openapi_relationships(entities)
        param_rels = [r for r in relationships if r["type"] == "HAS_PARAMETER"]
        assert len(param_rels) == 0


class TestSchemaReferenceRelationships:
    """Test REFERENCES_SCHEMA relationship extraction."""

    def test_schema_with_ref(self):
        """Should create REFERENCES_SCHEMA for schema $ref."""
        source_id = str(uuid4())
        target_id = str(uuid4())
        
        entities = [
            {
                "id": source_id,
                "type": "Schema",
                "name": "PaymentResponse",
                "schema_ref": "#/components/schemas/Payment"
            },
            {
                "id": target_id,
                "type": "Schema",
                "name": "Payment"
            }
        ]
        
        relationships = build_openapi_relationships(entities)
        
        ref_rels = [r for r in relationships if r["type"] == "REFERENCES_SCHEMA"]
        assert len(ref_rels) == 1
        assert ref_rels[0]["source_entity_id"] == source_id
        assert ref_rels[0]["target_entity_id"] == target_id

    def test_schema_property_ref(self):
        """Should create REFERENCES_SCHEMA for property $ref."""
        source_id = str(uuid4())
        target_id = str(uuid4())
        
        entities = [
            {
                "id": source_id,
                "type": "Schema",
                "name": "Account",
                "properties": {
                    "owner": {"$ref": "#/components/schemas/User"}
                }
            },
            {
                "id": target_id,
                "type": "Schema",
                "name": "User"
            }
        ]
        
        relationships = build_openapi_relationships(entities)
        
        ref_rels = [r for r in relationships if r["type"] == "REFERENCES_SCHEMA"]
        assert len(ref_rels) == 1
        assert ref_rels[0]["properties"]["property_name"] == "owner"


class TestEndpointSchemaRelationships:
    """Test ACCEPTS and RETURNS relationship extraction."""

    def test_accepts_relationship(self):
        """Should create ACCEPTS for request body schema."""
        endpoint_id = str(uuid4())
        schema_id = str(uuid4())
        
        entities = [
            {
                "id": endpoint_id,
                "type": "Endpoint",
                "path": "/payments",
                "method": "POST",
                "request_body_ref": "#/components/schemas/PaymentRequest"
            },
            {
                "id": schema_id,
                "type": "Schema",
                "name": "PaymentRequest"
            }
        ]
        
        relationships = build_openapi_relationships(entities)
        
        accepts_rels = [r for r in relationships if r["type"] == "ACCEPTS"]
        assert len(accepts_rels) == 1
        assert accepts_rels[0]["source_entity_id"] == endpoint_id
        assert accepts_rels[0]["target_entity_id"] == schema_id

    def test_returns_relationship(self):
        """Should create RETURNS for response schema."""
        endpoint_id = str(uuid4())
        schema_id = str(uuid4())
        
        entities = [
            {
                "id": endpoint_id,
                "type": "Endpoint",
                "path": "/payments/{paymentId}",
                "method": "GET",
                "response_refs": {
                    "200": "#/components/schemas/Payment"
                }
            },
            {
                "id": schema_id,
                "type": "Schema",
                "name": "Payment"
            }
        ]
        
        relationships = build_openapi_relationships(entities)
        
        returns_rels = [r for r in relationships if r["type"] == "RETURNS"]
        assert len(returns_rels) == 1
        assert returns_rels[0]["source_entity_id"] == endpoint_id
        assert returns_rels[0]["target_entity_id"] == schema_id
        assert returns_rels[0]["properties"]["status_code"] == "200"


class TestSecurityRelationships:
    """Test REQUIRES_SECURITY relationship extraction."""

    def test_requires_security(self):
        """Should create REQUIRES_SECURITY relationships."""
        endpoint_id = str(uuid4())
        scheme_id = str(uuid4())
        
        entities = [
            {
                "id": endpoint_id,
                "type": "Endpoint",
                "path": "/accounts",
                "method": "GET",
                "security": [{"BearerAuth": []}]
            },
            {
                "id": scheme_id,
                "type": "SecurityScheme",
                "name": "BearerAuth"
            }
        ]
        
        relationships = build_openapi_relationships(entities)
        
        security_rels = [r for r in relationships if r["type"] == "REQUIRES_SECURITY"]
        assert len(security_rels) == 1
        assert security_rels[0]["source_entity_id"] == endpoint_id
        assert security_rels[0]["target_entity_id"] == scheme_id


class TestEndpointResponseRelationships:
    """Test HAS_RESPONSE and response USES_SCHEMA relationships."""

    def test_has_response_relationship(self):
        endpoint_id = str(uuid4())
        response_id = str(uuid4())

        entities = [
            {
                "id": endpoint_id,
                "type": "Endpoint",
                "path": "/payments",
                "method": "POST",
                "response_match_keys": {"201": "match:ok"},
            },
            {
                "id": response_id,
                "type": "Response",
                "match_key": "match:ok",
                "schema_refs": {},
            },
        ]

        relationships = build_openapi_relationships(entities)
        has_response = [r for r in relationships if r["type"] == "HAS_RESPONSE"]
        assert len(has_response) == 1
        assert has_response[0]["source_entity_id"] == endpoint_id
        assert has_response[0]["target_entity_id"] == response_id
        assert has_response[0]["properties"]["status_code"] == "201"

    def test_response_uses_schema_relationship(self):
        response_id = str(uuid4())
        schema_id = str(uuid4())

        entities = [
            {
                "id": response_id,
                "type": "Response",
                "match_key": "match:ok",
                "schema_refs": {"application/json": "#/components/schemas/Payment"},
            },
            {
                "id": schema_id,
                "type": "Schema",
                "name": "Payment",
            },
        ]

        relationships = build_openapi_relationships(entities)
        uses_schema = [r for r in relationships if r["type"] == "USES_SCHEMA"]
        assert len(uses_schema) == 1
        assert uses_schema[0]["source_entity_id"] == response_id
        assert uses_schema[0]["target_entity_id"] == schema_id
        assert uses_schema[0]["properties"]["content_type"] == "application/json"


class TestParameterSchemaRelationships:
    """Test USES_SCHEMA relationships from Parameter entities to Schema entities."""

    def test_parameter_uses_schema_relationship(self):
        parameter_id = str(uuid4())
        schema_id = str(uuid4())

        entities = [
            {
                "id": parameter_id,
                "type": "Parameter",
                "name": "limit",
                "in": "query",
                "schema_ref": "#/components/schemas/Limit",
            },
            {
                "id": schema_id,
                "type": "Schema",
                "name": "Limit",
            },
        ]

        relationships = build_openapi_relationships(entities)
        uses_schema = [r for r in relationships if r["type"] == "USES_SCHEMA" and r["source_entity_id"] == parameter_id and r["target_entity_id"] == schema_id]

        assert len(uses_schema) == 1
        assert uses_schema[0]["properties"]["schema_name"] == "Limit"
        assert uses_schema[0]["properties"]["parameter_name"] == "limit"
