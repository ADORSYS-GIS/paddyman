"""Additional OpenAPI Pydantic types kept separate to respect LOC limits."""
from __future__ import annotations
from typing import Any
from uuid import uuid5, NAMESPACE_URL
from pydantic import Field
from typing import Literal
from .openapi_core import BaseOpenApiEntity
from .provenance import Provenance


class Parameter(BaseOpenApiEntity):
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
    type: Literal["Response"] = "Response"
    status_code: str | None = None
    description: str | None = None
    schema_refs: dict[str, str] = Field(default_factory=dict)
    content_types: list[str] = Field(default_factory=list)
    reusable: bool = False
    ref_path: str | None = None
    is_error: bool = False
    error_category: str | None = None

    @classmethod
    def create(
        cls,
        *,
        name: str,
        status_code: str | None,
        description: str | None,
        schema_refs: dict[str, str] | None,
        content_types: list[str] | None,
        spec_source: str,
        ref_path: str | None = None,
        reusable: bool = False,
        is_error: bool = False,
        error_category: str | None = None,
        id_seed: str | None = None,
    ) -> "Response":
        stable_source = ref_path or id_seed or f"{spec_source}:{name}:{status_code}"
        provenance = Provenance(
            source_file=spec_source,
            context=f"openapi_parser:response:{stable_source}",
        )
        return cls(
            id=uuid5(NAMESPACE_URL, f"openapi-response:{stable_source}"),
            name=name,
            provenance=provenance,
            status_code=status_code,
            description=description,
            schema_refs=schema_refs or {},
            content_types=content_types or [],
            reusable=reusable,
            ref_path=ref_path,
            is_error=is_error,
            error_category=error_category,
        )
