"""Configurable deterministic relationship vocabulary rules."""
from __future__ import annotations

import re


DEFAULT_RELATIONSHIP_MAP: dict[str, str] = {
    "CALLS": "USES",
    "USES": "USES",
    "DEPENDS_ON": "DEPENDS_ON",
    "DEPENDS": "DEPENDS_ON",
    "DEPENDSON": "DEPENDS_ON",
    "REFERENCES": "REFERENCES",
    "REFERENCE": "REFERENCES",
    "RETURNS": "EXPOSES",
    "ACCEPTS": "USES",
    "IMPLEMENTS": "IMPLEMENTS",
    "EXTENDS": "IMPLEMENTS",
    "DOCUMENTS": "DOCUMENTS",
    "DOCUMENTED_BY": "DOCUMENTS",
    "EXPOSES": "EXPOSES",
}

UNKNOWN_RELATIONSHIP = "REFERENCES"
_SEPARATORS = re.compile(r"[\s\-./]+")
_CAMEL = re.compile(r"([a-z\d])([A-Z])")


def normalize_key(raw_type: str) -> str:
    """Return a stable upper-snake key for *raw_type*."""
    spaced = _CAMEL.sub(r"\1_\2", raw_type.strip())
    underscored = _SEPARATORS.sub("_", spaced)
    return underscored.upper().strip("_")


class RelationshipTypeMapper:
    """Map source relationship names into the canonical relationship vocabulary."""

    def __init__(self, mapping: dict[str, str] | None = None) -> None:
        table = mapping if mapping is not None else DEFAULT_RELATIONSHIP_MAP
        self._mapping = {normalize_key(k): normalize_key(v) for k, v in table.items()}

    def normalize(self, relationship_type: str) -> str:
        """Return canonical relationship type for *relationship_type*."""
        return self._mapping.get(normalize_key(relationship_type), UNKNOWN_RELATIONSHIP)