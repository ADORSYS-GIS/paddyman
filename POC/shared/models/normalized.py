"""Normalized JSON contract shared by parser and extraction stages."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class NormalizedDocument:
    """Parser-agnostic document unit passed to extraction."""

    document_id: str
    text: str
    source_parser: str
    source_metadata: dict[str, Any]
    provenance: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "document_id": self.document_id,
            "text": self.text,
            "source_parser": self.source_parser,
            "source_metadata": self.source_metadata,
            "provenance": self.provenance,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "NormalizedDocument":
        return cls(
            document_id=str(data.get("document_id") or "unknown"),
            text=str(data.get("text") or ""),
            source_parser=str(data.get("source_parser") or "unknown"),
            source_metadata=dict(data.get("source_metadata") or {}),
            provenance=dict(data.get("provenance") or {}),
        )


@dataclass
class NormalizedJson:
    """Common JSON representation between parsing and extraction."""

    entities: list[dict[str, Any]] = field(default_factory=list)
    relationships: list[dict[str, Any]] = field(default_factory=list)
    method_calls: list[dict[str, Any]] = field(default_factory=list)
    # Optional per-parser indices (namespaced). Structure: { index_name: any }
    parser_indices: dict[str, Any] = field(default_factory=dict)
    documents: list[NormalizedDocument] = field(default_factory=list)
    source_metadata: list[dict[str, Any]] = field(default_factory=list)
    provenance: dict[str, Any] = field(default_factory=dict)
    version_metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "entities": self.entities,
            "relationships": self.relationships,
            "method_calls": self.method_calls,
            "parser_indices": self.parser_indices,
            "documents": [doc.to_dict() for doc in self.documents],
            "source_metadata": self.source_metadata,
            "provenance": self.provenance,
            "version_metadata": self.version_metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "NormalizedJson":
        return cls(
            entities=list(data.get("entities") or []),
            relationships=list(data.get("relationships") or []),
            method_calls=list(data.get("method_calls") or []),
            parser_indices=dict(data.get("parser_indices") or {}),
            documents=[
                NormalizedDocument.from_dict(item)
                for item in data.get("documents") or []
                if isinstance(item, dict)
            ],
            source_metadata=list(data.get("source_metadata") or []),
            provenance=dict(data.get("provenance") or {}),
            version_metadata=dict(data.get("version_metadata") or {}),
        )