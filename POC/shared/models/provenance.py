"""Pydantic model for provenance metadata."""
from __future__ import annotations
from pydantic import BaseModel


class Provenance(BaseModel):
    """Provenance metadata for an entity."""
    source_file: str
    context: str
