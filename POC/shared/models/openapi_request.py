"""Pydantic model for OpenAPI `RequestBody` entities.

Kept intentionally small so it can be imported without triggering the
150-LOC refactor requirement for larger files.
"""
from __future__ import annotations
from uuid import uuid5, NAMESPACE_URL
from typing import Literal
from pydantic import Field
from .openapi_core import BaseOpenApiEntity
from .provenance import Provenance


class RequestBody(BaseOpenApiEntity):
    """A first-class entity representing an OpenAPI Request Body."""
    type: Literal["RequestBody"] = "RequestBody"
    description: str | None = None
    required: bool = False
    content_types: list[str] = Field(default_factory=list)
    schema_refs: dict[str, str] = Field(default_factory=dict)
    spec_source: str | None = None
    ref_path: str | None = None
    reusable: bool = False
    source_location: str | None = None

    @classmethod
    def create(
        cls,
        *,
        name: str,
        description: str | None,
        required: bool,
        content_types: list[str],
        schema_refs: dict[str, str],
        spec_source: str,
        ref_path: str | None,
        reusable: bool,
        id_seed: str | None = None,
    ) -> "RequestBody":
        stable = id_seed or f"{spec_source}:{name}:{','.join(content_types or [])}"
        provenance = Provenance(
            source_file=spec_source,
            context=f"openapi_parser:request_body:{stable}",
        )
        return cls(
            id=uuid5(NAMESPACE_URL, f"openapi-request-body:{stable}"),
            name=name,
            provenance=provenance,
            description=description,
            required=required,
            content_types=content_types or [],
            schema_refs=schema_refs or {},
            spec_source=spec_source,
            ref_path=ref_path,
            reusable=reusable,
            source_location=(f"#/components/requestBodies/{name}" if ref_path else None),
        )
