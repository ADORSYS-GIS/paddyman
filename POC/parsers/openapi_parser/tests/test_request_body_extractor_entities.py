"""Unit tests for request-body entity extraction."""
from __future__ import annotations

from openapi_parser.request_body_extractor import extract_request_body_entities


def test_extracts_inline_request_body() -> None:
    raw = {
        "paths": {
            "/payments": {
                "post": {
                    "operationId": "createPayment",
                    "requestBody": {
                        "required": True,
                        "description": "Payment initiation request",
                        "content": {
                            "application/json": {"schema": {"$ref": "#/components/schemas/PaymentInitiation"}}
                        },
                    },
                }
            }
        }
    }

    entities, links = extract_request_body_entities(raw, "spec.yaml")

    assert len(entities) == 1
    assert len(links) == 1
    assert entities[0]["type"] == "RequestBody"
    assert entities[0]["properties"]["required"] is True
    assert entities[0]["properties"]["content_types"] == ["application/json"]


def test_extracts_component_request_body() -> None:
    raw = {
        "components": {
            "requestBodies": {
                "PaymentInitiationRequest": {
                    "description": "Reusable payment request",
                    "content": {
                        "application/json": {"schema": {"$ref": "#/components/schemas/PaymentInitiation"}}
                    },
                }
            }
        }
    }

    entities, links = extract_request_body_entities(raw, "spec.yaml")

    assert len(entities) == 1
    assert links == []
    assert entities[0]["properties"]["ref_path"] == "#/components/requestBodies/PaymentInitiationRequest"
    assert entities[0]["properties"]["reusable"] is True


def test_handles_multiple_content_types() -> None:
    raw = {
        "components": {
            "requestBodies": {
                "DualFormat": {
                    "content": {
                        "application/json": {"schema": {"$ref": "#/components/schemas/JsonPayload"}},
                        "application/xml": {"schema": {"$ref": "#/components/schemas/XmlPayload"}},
                    }
                }
            }
        }
    }

    entities, _ = extract_request_body_entities(raw, "spec.yaml")

    assert entities[0]["properties"]["content_types"] == ["application/json", "application/xml"]
    assert entities[0]["schema_refs"]["application/json"] == "#/components/schemas/JsonPayload"
    assert entities[0]["schema_refs"]["application/xml"] == "#/components/schemas/XmlPayload"


def test_deduplicates_reused_request_body_by_content() -> None:
    shared = {
        "description": "Same body",
        "content": {"application/json": {"schema": {"$ref": "#/components/schemas/PaymentInitiation"}}},
    }
    raw = {
        "paths": {
            "/payments": {"post": {"requestBody": dict(shared)}},
            "/payments/{id}": {"put": {"requestBody": dict(shared)}},
        }
    }

    entities, links = extract_request_body_entities(raw, "spec.yaml")

    assert len(entities) == 1
    assert len(links) == 2
    assert entities[0]["properties"]["reusable"] is True
