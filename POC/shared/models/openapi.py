"""Compatibility shim for OpenAPI Pydantic models.

This module re-exports the real implementations from
``shared.models.openapi_models`` so existing imports such as
``from shared.models.openapi import Operation`` continue to work while
keeping this file small enough to satisfy the project's line-length
rules.
"""
from .openapi_models import (
    BaseOpenApiEntity,
    Operation,
    Endpoint,
    Tag,
    Parameter,
    SecurityScheme,
    Response,
)
from .openapi_request import RequestBody

__all__ = [
    "BaseOpenApiEntity",
    "Operation",
    "Endpoint",
    "Tag",
    "Parameter",
    "SecurityScheme",
    "Response",
    "RequestBody",
]


