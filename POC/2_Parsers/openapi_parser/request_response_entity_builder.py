"""Build normalized entity dicts for request bodies and responses.

Pure transformation module — converts :class:`RequestBodyMetadata` and
:class:`ResponseMetadata` records into flat entity dictionaries for the
``NormalizedJson.entities`` field.
"""
from __future__ import annotations

from typing import Any

from openapi_parser.models import RequestBodyMetadata, ResponseMetadata


def build_request_body_entity(request_body: RequestBodyMetadata) -> dict[str, Any]:
    """Convert a RequestBodyMetadata record to a normalized entity dict.

    Args:
        request_body: Structured request body metadata from the extractor.

    Returns:
        Entity dictionary with keys matching the normalized JSON contract.
        All fields are present; optional fields use ``None`` when absent.

    Example:
        >>> from openapi_parser.models import RequestBodyMetadata
        >>> rb = RequestBodyMetadata(
        ...     name="paymentInitiation",
        ...     spec_source="payment.yaml",
        ...     required=True,
        ...     description="JSON request body for payment initiation",
        ...     content_types=["application/json", "application/xml"],
        ...     schema_ref="#/components/schemas/paymentInitiation_json"
        ... )
        >>> entity = build_request_body_entity(rb)
        >>> entity["type"]
        'RequestBody'
        >>> entity["name"]
        'paymentInitiation'
        >>> entity["required"]
        True
    """
    return {
        "type": "RequestBody",
        "name": request_body.name,
        "required": request_body.required,
        "content_types": request_body.content_types,
        "schema_ref": request_body.schema_ref,
        "schema_type": request_body.schema_type,
        "description": request_body.description,
        "source_file": request_body.spec_source,
    }


def build_response_entity(response: ResponseMetadata) -> dict[str, Any]:
    """Convert a ResponseMetadata record to a normalized entity dict.

    Args:
        response: Structured response metadata from the extractor.

    Returns:
        Entity dictionary with keys matching the normalized JSON contract.
        All fields are present; optional fields use ``None`` when absent.

    Example:
        >>> from openapi_parser.models import ResponseMetadata
        >>> resp = ResponseMetadata(
        ...     name="CREATED_201_PaymentInitiation",
        ...     spec_source="payment.yaml",
        ...     description="CREATED",
        ...     http_status="201",
        ...     content_types=["application/json"],
        ...     schema_ref="#/components/schemas/paymentInitiationRequestResponse-201"
        ... )
        >>> entity = build_response_entity(resp)
        >>> entity["type"]
        'Response'
        >>> entity["name"]
        'CREATED_201_PaymentInitiation'
        >>> entity["http_status"]
        '201'
    """
    return {
        "type": "Response",
        "name": response.name,
        "http_status": response.http_status,
        "description": response.description,
        "content_types": response.content_types,
        "schema_ref": response.schema_ref,
        "schema_type": response.schema_type,
        "headers": response.headers,
        "source_file": response.spec_source,
    }
