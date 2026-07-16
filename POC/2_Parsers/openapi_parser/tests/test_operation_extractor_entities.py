"""Unit tests for operation and tag entity extraction."""
from __future__ import annotations

from openapi_parser.operation_extractor import extract_operation_entities


def test_extracts_operation_with_metadata() -> None:
    raw = {
        "paths": {
            "/payments": {
                "post": {
                    "operationId": "createPayment",
                    "summary": "Create payment",
                    "description": "Creates a payment resource",
                    "tags": ["payments", "pis"],
                    "deprecated": True,
                    "externalDocs": {"url": "https://docs.example.com/payments"},
                }
            }
        }
    }

    operations, tags, links = extract_operation_entities(raw, "spec.yaml")

    assert len(operations) == 1
    assert len(tags) == 2
    assert len(links) == 1
    op = operations[0]
    assert op["type"] == "Operation"
    assert op["properties"]["operation_id"] == "createPayment"
    assert op["properties"]["deprecated"] is True
    assert op["properties"]["external_docs"]["url"] == "https://docs.example.com/payments"


def test_generates_deterministic_operation_id_when_missing() -> None:
    raw = {"paths": {"/accounts/{id}": {"get": {"responses": {"200": {"description": "OK"}}}}}}

    operations, tags, links = extract_operation_entities(raw, "spec.yaml")

    assert len(operations) == 1
    assert tags == []
    assert len(links) == 1
    assert operations[0]["properties"]["operation_id"] == "get_accounts_id"


def test_deduplicates_tags_and_preserves_operation_order() -> None:
    raw = {
        "paths": {
            "/a": {"get": {"operationId": "getA", "tags": ["shared", "a"]}},
            "/b": {"post": {"operationId": "createB", "tags": ["shared", "b"]}},
        }
    }

    operations, tags, links = extract_operation_entities(raw, "spec.yaml")

    assert [op["properties"]["operation_id"] for op in operations] == ["getA", "createB"]
    assert [tag["name"] for tag in tags] == ["shared", "a", "b"]
    assert [link["endpoint_path"] for link in links] == ["/a", "/b"]
