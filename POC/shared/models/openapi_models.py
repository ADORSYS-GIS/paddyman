"""Pydantic models implementation for OpenAPI entities.

This module contains the full model implementations and is imported by
`shared.models.openapi` which re-exports the public symbols. Splitting the
implementation into a separate file keeps `openapi.py` small to satisfy
project style rules.
"""
from __future__ import annotations
from uuid import UUID, uuid5, NAMESPACE_URL
from pydantic import BaseModel, Field
from typing import Literal, Any
from pydantic import ConfigDict
from .provenance import Provenance


class BaseOpenApiEntity(BaseModel):
    """Base model for all OpenAPI entities."""
    id: UUID
    type: str
    name: str
    provenance: Provenance
    tags: list[str] = Field(default_factory=list)

    model_config = ConfigDict(validate_by_name=True)


class Operation(BaseOpenApiEntity):
    """A first-class entity representing an OpenAPI Operation."""
    type: Literal["Operation"] = "Operation"
    summary: str | None = None
    description: str | None = None
    deprecated: bool = False
    external_docs: dict | None = None
    method: str
    path: str
    endpoint_id: UUID

    @classmethod
    def create(
        cls,
        *,
        operation_id: str,
        method: str,
        path: str,
        operation: dict,
        spec_source: str,
        endpoint_id: UUID,
    ) -> "Operation":
        """Create an Operation entity."""
        stable_key = f"{spec_source}:{method.upper()}:{path}:{operation_id}"
        provenance = Provenance(
            source_file=spec_source,
            context=f"openapi_parser:operation:{stable_key}",
        )
        return cls(
            id=uuid5(NAMESPACE_URL, f"openapi-operation:{stable_key}"),
            name=operation_id,
            provenance=provenance,
            summary=operation.get("summary"),
            description=operation.get("description"),
            tags=operation.get("tags", []),
            deprecated=operation.get("deprecated", False),
            external_docs=operation.get("externalDocs"),
            method=method.upper(),
            path=path,
            endpoint_id=endpoint_id,
        )


class Endpoint(BaseOpenApiEntity):
    """A first-class entity representing an OpenAPI Endpoint."""
    type: Literal["Endpoint"] = "Endpoint"
    path: str
    method: str

    @classmethod
    def create(
        cls,
        *,
        path: str,
        method: str,
        spec_source: str,
    ) -> "Endpoint":
        """Create an Endpoint entity."""
        stable_key = f"{spec_source}:{method.upper()}:{path}"
        provenance = Provenance(
            source_file=spec_source,
            context=f"openapi_parser:endpoint:{stable_key}",
        )
        return cls(
            id=uuid5(NAMESPACE_URL, f"openapi-endpoint:{stable_key}"),
            name=f"{method.upper()} {path}",
            provenance=provenance,
            path=path,
            method=method.upper(),
        )


class Tag(BaseOpenApiEntity):
    """A first-class entity representing an OpenAPI Tag."""
    type: Literal["Tag"] = "Tag"
    description: str | None = None

    @classmethod
    def create(cls, *, tag_name: str, spec_source: str, description: str | None = None) -> "Tag":
        """Create a Tag entity."""
        stable_key = f"{spec_source}:{tag_name}"
        provenance = Provenance(
            source_file=spec_source,
            context=f"openapi_parser:tag:{stable_key}",
        )
        return cls(
            id=uuid5(NAMESPACE_URL, f"openapi-tag:{stable_key}"),
            name=tag_name,
            provenance=provenance,
            description=description,
        )


class Parameter(BaseOpenApiEntity):
    """A first-class entity representing an OpenAPI Parameter."""
    type: Literal["Parameter"] = "Parameter"
    location: str
    required: bool = False
    description: str | None = None
    schema_type: str | None = None
    schema_ref: str | None = None

    @classmethod
    def create(
        cls,
        *,
        name: str,
        location: str,
        required: bool,
        description: str | None,
        schema_type: str | None,
        schema_ref: str | None,
        spec_source: str,
    ) -> "Parameter":
        """Create a Parameter entity."""
        stable_key = f"{spec_source}:{location}:{name}"
        provenance = Provenance(
            source_file=spec_source,
            context=f"openapi_parser:parameter:{stable_key}",
        )
        return cls(
            id=uuid5(NAMESPACE_URL, f"openapi-parameter:{stable_key}"),
            name=name,
            provenance=provenance,
            location=location,
            required=required,
            description=description,
            schema_type=schema_type,
            schema_ref=schema_ref,
        )


class SecurityScheme(BaseOpenApiEntity):
    """A first-class entity representing an OpenAPI Security Scheme."""
    type: Literal["SecurityScheme"] = "SecurityScheme"
    scheme_type: str
    description: str | None = None
    scheme: str | None = None
    bearer_format: str | None = None
    in_: str | None = Field(default=None, alias="in")
    parameter_name: str | None = None
    open_id_connect_url: str | None = None
    flows: dict[str, Any] = Field(default_factory=dict)
    source_location: str | None = None

    @classmethod
    def create(
        cls,
        *,
        name: str,
        scheme_type: str,
        spec_source: str,
        description: str | None = None,
        scheme: str | None = None,
        bearer_format: str | None = None,
        in_: str | None = None,
        parameter_name: str | None = None,
        open_id_connect_url: str | None = None,
        flows: dict[str, Any] | None = None,
    ) -> "SecurityScheme":
        stable_key = f"{spec_source}:{name}"
        provenance = Provenance(
            source_file=spec_source,
            context=f"openapi_parser:security_scheme:{stable_key}",
        )
        return cls(
            id=uuid5(NAMESPACE_URL, f"openapi-securityscheme:{stable_key}"),
            name=name,
            provenance=provenance,
            scheme_type=scheme_type,
            description=description,
            scheme=scheme,
            bearer_format=bearer_format,
            in_=in_,
            parameter_name=parameter_name,
            open_id_connect_url=open_id_connect_url,
            flows=flows or {},
            source_location=f"#/components/securitySchemes/{name}",
        )


class Response(BaseOpenApiEntity):
    """A first-class entity representing an OpenAPI Response."""
    type: Literal["Response"] = "Response"
    status_code: str | None = None
    description: str | None = None
    content_types: list[str] = Field(default_factory=list)
    schema_refs: dict[str, str] = Field(default_factory=dict)
    spec_source: str | None = None
    ref_path: str | None = None
    reusable: bool = False
    is_error: bool = False
    error_category: str | None = None

    @classmethod
    def create(
        cls,
        *,
        name: str,
        status_code: str | None,
        description: str | None,
        schema_refs: dict[str, str],
        content_types: list[str],
        spec_source: str,
        ref_path: str | None = None,
        reusable: bool = False,
        is_error: bool = False,
        error_category: str | None = None,
        id_seed: str | None = None,
    ) -> "Response":
        stable = id_seed or f"{spec_source}:{name}:{status_code}"
        provenance = Provenance(
            source_file=spec_source,
            context=f"openapi_parser:response:{stable}",
        )
        return cls(
            id=uuid5(NAMESPACE_URL, f"openapi-response:{stable}"),
            name=name,
            provenance=provenance,
            status_code=status_code,
            description=description,
            content_types=content_types or [],
            schema_refs=schema_refs or {},
            spec_source=spec_source,
            ref_path=ref_path,
            reusable=reusable,
            is_error=is_error,
            error_category=error_category,
        )
