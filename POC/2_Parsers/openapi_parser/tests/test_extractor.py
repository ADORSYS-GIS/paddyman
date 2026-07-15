"""Unit tests for openapi_parser.extractor (Chunk 3.2).

Covers:
- endpoint extraction from a minimal spec
- multiple paths extracted
- multiple HTTP methods on a single path
- all supported HTTP methods recognised
- unsupported path-item keys ignored (summary, parameters, …)
- missing paths block returns empty list
- invalid paths block type returns empty list
- operationId / summary / description / tags / parameters extracted
- requestBody extracted
- responses extracted
"""
from __future__ import annotations

import pytest


_MINIMAL_RAW: dict = {
    "openapi": "3.0.1",
    "info": {"title": "Pay API", "version": "1.0.0"},
    "paths": {
        "/payments": {
            "post": {
                "summary": "Create payment",
                "operationId": "createPayment",
                "tags": ["payments"],
                "responses": {"201": {"description": "Created"}},
            }
        }
    },
}

_MULTI_PATH_RAW: dict = {
    "openapi": "3.0.1",
    "info": {"title": "Multi API", "version": "2.0.0"},
    "paths": {
        "/accounts": {
            "get": {"summary": "List accounts", "responses": {"200": {}}},
            "post": {"summary": "Create account", "responses": {"201": {}}},
        },
        "/accounts/{id}": {
            "get": {"summary": "Get account", "responses": {"200": {}}},
            "put": {"summary": "Update account", "responses": {"200": {}}},
            "delete": {"summary": "Delete account", "responses": {"204": {}}},
        },
    },
}

_ALL_METHODS_RAW: dict = {
    "openapi": "3.0.1",
    "info": {"title": "Methods API", "version": "1.0.0"},
    "paths": {
        "/resource": {
            "get": {"responses": {}},
            "post": {"responses": {}},
            "put": {"responses": {}},
            "patch": {"responses": {}},
            "delete": {"responses": {}},
            "options": {"responses": {}},
            "head": {"responses": {}},
        }
    },
}

_FULL_OPERATION_RAW: dict = {
    "openapi": "3.0.1",
    "info": {"title": "Full API", "version": "1.0.0"},
    "paths": {
        "/items": {
            "post": {
                "operationId": "createItem",
                "summary": "Create an item",
                "description": "Full description here.",
                "tags": ["items", "write"],
                "parameters": [
                    {"name": "X-Request-ID", "in": "header", "required": False}
                ],
                "requestBody": {"content": {"application/json": {}}},
                "responses": {
                    "201": {"description": "Created"},
                    "400": {"description": "Bad request"},
                },
            }
        }
    },
}


class TestExtractEndpoints:
    def _import(self):
        from openapi_parser.extractor import extract_endpoints
        return extract_endpoints

    def test_single_endpoint_extracted(self):
        extract = self._import()
        results = extract(_MINIMAL_RAW, "Pay API", "/spec.yaml")
        assert len(results) == 1
        ep = results[0]
        assert ep.type == "endpoint"
        assert ep.method == "POST"
        assert ep.path == "/payments"
        assert ep.api_title == "Pay API"
        assert ep.spec_source == "/spec.yaml"

    def test_multiple_paths_and_methods(self):
        extract = self._import()
        results = extract(_MULTI_PATH_RAW, "Multi API", "/spec.yaml")
        assert len(results) == 5
        methods = {(r.path, r.method) for r in results}
        assert ("/accounts", "GET") in methods
        assert ("/accounts", "POST") in methods
        assert ("/accounts/{id}", "DELETE") in methods

    def test_all_http_methods_recognised(self):
        extract = self._import()
        results = extract(_ALL_METHODS_RAW, "Methods API", "/spec.yaml")
        assert len(results) == 7
        extracted_methods = {r.method for r in results}
        assert extracted_methods == {"GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"}

    def test_unknown_path_item_keys_ignored(self):
        extract = self._import()
        raw = {
            "openapi": "3.0.1",
            "info": {"title": "T", "version": "1"},
            "paths": {
                "/x": {
                    "summary": "A path summary",
                    "parameters": [{"name": "x", "in": "query"}],
                    "get": {"responses": {}},
                }
            },
        }
        results = extract(raw, "T", "/spec.yaml")
        assert len(results) == 1
        assert results[0].method == "GET"

    def test_missing_paths_returns_empty(self):
        extract = self._import()
        raw = {"openapi": "3.0.1", "info": {"title": "T", "version": "1"}}
        assert extract(raw, "T", "/spec.yaml") == []

    def test_paths_not_dict_returns_empty(self):
        extract = self._import()
        raw = {"openapi": "3.0.1", "info": {"title": "T", "version": "1"}, "paths": "invalid"}
        assert extract(raw, "T", "/spec.yaml") == []

    def test_full_operation_fields_extracted(self):
        extract = self._import()
        results = extract(_FULL_OPERATION_RAW, "Full API", "/spec.yaml")
        assert len(results) == 1
        ep = results[0]
        assert ep.operation_id == "createItem"
        assert ep.summary == "Create an item"
        assert ep.description == "Full description here."
        assert ep.tags == ["items", "write"]
        assert len(ep.parameters) == 1
        assert ep.parameters[0].name == "X-Request-ID"
        assert ep.parameters[0].location == "header"
        assert ep.parameters[0].required is False
        assert ep.request_body == {"content": {"application/json": {}}}
        assert "201" in ep.responses

    def test_missing_optional_fields_default_to_none(self):
        extract = self._import()
        results = extract(_MINIMAL_RAW, "Pay API", "/spec.yaml")
        ep = results[0]
        assert ep.operation_id == "createPayment"  # present
        assert ep.description is None
        assert ep.parameters == []
        assert ep.request_body is None

    def test_method_is_uppercased(self):
        extract = self._import()
        results = extract(_MINIMAL_RAW, "Pay API", "/spec.yaml")
        assert results[0].method == "POST"

    def test_empty_paths_dict_returns_empty(self):
        extract = self._import()
        raw = {"openapi": "3.0.1", "info": {"title": "T", "version": "1"}, "paths": {}}
        assert extract(raw, "T", "/spec.yaml") == []
