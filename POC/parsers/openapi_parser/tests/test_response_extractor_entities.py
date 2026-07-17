"""Unit tests for response entity extraction."""
from __future__ import annotations

from openapi_parser.response_extractor import extract_response_entities


def test_extracts_inline_response() -> None:
    raw = {
        "paths": {
            "/payments": {
                "post": {
                    "responses": {
                        "201": {
                            "description": "Created",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/PaymentResponse"}
                                }
                            },
                        }
                    }
                }
            }
        }
    }

    entities, links = extract_response_entities(raw, "spec.yaml")

    assert len(entities) == 1
    assert len(links) == 1
    assert entities[0]["type"] == "Response"
    assert entities[0]["properties"]["status_code"] == "201"
    assert entities[0]["properties"]["error_category"] == "success"


def test_extracts_shared_response() -> None:
    raw = {
        "components": {
            "responses": {
                "CREATED_201_Payment": {
                    "description": "Created",
                    "content": {"application/json": {"schema": {"$ref": "#/components/schemas/PaymentResponse"}}},
                }
            }
        }
    }

    entities, links = extract_response_entities(raw, "spec.yaml")

    assert len(entities) == 1
    assert links == []
    assert entities[0]["properties"]["ref_path"] == "#/components/responses/CREATED_201_Payment"


def test_marks_error_responses() -> None:
    raw = {
        "paths": {
            "/payments": {
                "post": {
                    "responses": {
                        "400": {"description": "Bad request"},
                        "500": {"description": "Server error"},
                    }
                }
            }
        }
    }

    entities, _ = extract_response_entities(raw, "spec.yaml")

    by_status = {item["properties"]["status_code"]: item for item in entities}
    assert by_status["400"]["properties"]["is_error"] is True
    assert by_status["400"]["properties"]["error_category"] == "client_error"
    assert by_status["500"]["properties"]["is_error"] is True
    assert by_status["500"]["properties"]["error_category"] == "server_error"


def test_handles_multiple_content_types_and_dedup() -> None:
    shared = {
        "description": "OK",
        "content": {
            "application/json": {"schema": {"$ref": "#/components/schemas/A"}},
            "application/xml": {"schema": {"$ref": "#/components/schemas/B"}},
        },
    }
    raw = {
        "paths": {
            "/one": {"get": {"responses": {"200": dict(shared)}}},
            "/two": {"get": {"responses": {"200": dict(shared)}}},
        }
    }

    entities, links = extract_response_entities(raw, "spec.yaml")

    assert len(entities) == 1
    assert len(links) == 2
    assert entities[0]["properties"]["content_types"] == ["application/json", "application/xml"]
    assert entities[0]["properties"]["reusable"] is True
