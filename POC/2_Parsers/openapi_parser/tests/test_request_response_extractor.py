"""Unit tests for request body and response extraction."""
from __future__ import annotations

import pytest

from openapi_parser.models import RequestBodyMetadata, ResponseMetadata
from openapi_parser.request_response_extractor import (
    extract_request_bodies,
    extract_responses,
)


def test_extract_request_bodies_empty_spec():
    """Empty spec returns empty list."""
    raw = {}
    result = extract_request_bodies(raw, "test.yaml")
    assert result == []


def test_extract_request_bodies_no_components():
    """Spec without components returns empty list."""
    raw = {"openapi": "3.0.0", "info": {"title": "Test", "version": "1.0"}}
    result = extract_request_bodies(raw, "test.yaml")
    assert result == []


def test_extract_request_bodies_no_requestBodies():
    """Spec with components but no requestBodies returns empty list."""
    raw = {"components": {"schemas": {"Foo": {"type": "object"}}}}
    result = extract_request_bodies(raw, "test.yaml")
    assert result == []


def test_extract_request_bodies_single():
    """Spec with one request body produces one RequestBodyMetadata."""
    raw = {
        "components": {
            "requestBodies": {
                "paymentInitiation": {
                    "required": True,
                    "description": "Payment initiation request",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/PaymentInit"}
                        }
                    },
                }
            }
        }
    }
    result = extract_request_bodies(raw, "payment.yaml")
    
    assert len(result) == 1
    rb = result[0]
    assert isinstance(rb, RequestBodyMetadata)
    assert rb.name == "paymentInitiation"
    assert rb.required is True
    assert rb.description == "Payment initiation request"
    assert rb.content_types == ["application/json"]
    assert rb.schema_ref == "#/components/schemas/PaymentInit"
    assert rb.spec_source == "payment.yaml"


def test_extract_request_bodies_multiple_content_types():
    """Request body with multiple content types."""
    raw = {
        "components": {
            "requestBodies": {
                "multiFormat": {
                    "content": {
                        "application/json": {"schema": {"type": "object"}},
                        "application/xml": {"schema": {"type": "string"}},
                    }
                }
            }
        }
    }
    result = extract_request_bodies(raw, "test.yaml")
    
    assert len(result) == 1
    rb = result[0]
    assert set(rb.content_types) == {"application/json", "application/xml"}
    assert rb.schema_type == "object"  # from first content type


def test_extract_request_bodies_multiple():
    """Spec with two request bodies produces two RequestBodyMetadata."""
    raw = {
        "components": {
            "requestBodies": {
                "body1": {"content": {"application/json": {"schema": {"type": "object"}}}},
                "body2": {"content": {"text/plain": {"schema": {"type": "string"}}}},
            }
        }
    }
    result = extract_request_bodies(raw, "test.yaml")
    
    assert len(result) == 2
    names = {rb.name for rb in result}
    assert names == {"body1", "body2"}


def test_extract_responses_empty_spec():
    """Empty spec returns empty list."""
    raw = {}
    result = extract_responses(raw, "test.yaml")
    assert result == []


def test_extract_responses_no_components():
    """Spec without components returns empty list."""
    raw = {"openapi": "3.0.0", "info": {"title": "Test", "version": "1.0"}}
    result = extract_responses(raw, "test.yaml")
    assert result == []


def test_extract_responses_no_responses():
    """Spec with components but no responses returns empty list."""
    raw = {"components": {"schemas": {"Foo": {"type": "object"}}}}
    result = extract_responses(raw, "test.yaml")
    assert result == []


def test_extract_responses_single():
    """Spec with one response produces one ResponseMetadata."""
    raw = {
        "components": {
            "responses": {
                "CREATED_201_PaymentInitiation": {
                    "description": "Payment created",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/PaymentResponse"}
                        }
                    },
                }
            }
        }
    }
    result = extract_responses(raw, "payment.yaml")
    
    assert len(result) == 1
    resp = result[0]
    assert isinstance(resp, ResponseMetadata)
    assert resp.name == "CREATED_201_PaymentInitiation"
    assert resp.description == "Payment created"
    assert resp.http_status == "201"  # extracted from name
    assert resp.content_types == ["application/json"]
    assert resp.schema_ref == "#/components/schemas/PaymentResponse"
    assert resp.spec_source == "payment.yaml"


def test_extract_responses_status_extraction():
    """HTTP status code extracted from response name."""
    raw = {
        "components": {
            "responses": {
                "BAD_REQUEST_400_PIS": {
                    "description": "Bad request",
                },
                "OK_200": {
                    "description": "Success",
                },
            }
        }
    }
    result = extract_responses(raw, "test.yaml")
    
    assert len(result) == 2
    status_map = {r.name: r.http_status for r in result}
    assert status_map["BAD_REQUEST_400_PIS"] == "400"
    assert status_map["OK_200"] == "200"


def test_extract_responses_multiple():
    """Spec with five responses produces five ResponseMetadata."""
    raw = {
        "components": {
            "responses": {
                "OK_200": {"description": "OK"},
                "CREATED_201": {"description": "Created"},
                "BAD_REQUEST_400": {"description": "Bad request"},
                "UNAUTHORIZED_401": {"description": "Unauthorized"},
                "NOT_FOUND_404": {"description": "Not found"},
            }
        }
    }
    result = extract_responses(raw, "test.yaml")
    
    assert len(result) == 5
    names = {r.name for r in result}
    assert names == {"OK_200", "CREATED_201", "BAD_REQUEST_400", "UNAUTHORIZED_401", "NOT_FOUND_404"}


def test_extract_responses_with_headers():
    """Response with headers."""
    raw = {
        "components": {
            "responses": {
                "WithHeaders": {
                    "description": "Response with headers",
                    "headers": {
                        "X-Rate-Limit": {"schema": {"type": "integer"}},
                        "X-Request-ID": {"schema": {"type": "string"}},
                    },
                }
            }
        }
    }
    result = extract_responses(raw, "test.yaml")
    
    assert len(result) == 1
    resp = result[0]
    assert len(resp.headers) == 2
    assert "X-Rate-Limit" in resp.headers
    assert "X-Request-ID" in resp.headers
