"""Pydantic model for top-level API entity extracted from OpenAPI specs.
"""
from __future__ import annotations
from uuid import UUID
from typing import Literal
from pydantic import BaseModel, Field, ConfigDict

from .provenance import Provenance


class API(BaseModel):
    """Top-level API entity model.

    Minimal required fields: title, version, description. Parsers may
    attach child entity lists (endpoints, operations, schemas, etc.)
    as additional keys on the instance when serializing to JSON.
    """
    id: UUID
    type: Literal["API"] = "API"
    name: str
    title: str
    version: str | None = None
    description: str | None = None
    provenance: Provenance
    # Allow arbitrary child lists (endpoints, schemas, operations)
    tags: list[str] = Field(default_factory=list)

    model_config = ConfigDict(validate_by_name=True)
