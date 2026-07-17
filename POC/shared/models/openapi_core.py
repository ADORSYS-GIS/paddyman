"""Core Pydantic models for OpenAPI entities (kept small).
"""
from __future__ import annotations
from uuid import UUID, uuid5, NAMESPACE_URL
from pydantic import BaseModel, Field, ConfigDict
from typing import Literal
from .provenance import Provenance


class BaseOpenApiEntity(BaseModel):
    id: UUID
    type: str
    name: str
    provenance: Provenance
    tags: list[str] = Field(default_factory=list)

    model_config = ConfigDict(validate_by_name=True)


class Operation(BaseOpenApiEntity):
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
    type: Literal["Tag"] = "Tag"
    description: str | None = None

    @classmethod
    def create(cls, *, tag_name: str, spec_source: str, description: str | None = None) -> "Tag":
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
