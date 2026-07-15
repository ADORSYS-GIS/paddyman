"""Embedding result models and input type definitions.

Defines the canonical output shape for all embedding generation operations.
Compatible with the shared pipeline models from ``shared.models``.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class EmbeddingInputType(str, Enum):
    """Semantic category of the text that was embedded."""

    ENTITY = "entity"
    CHUNK = "chunk"
    JAVA_CLASS = "java_class"
    JAVA_METHOD = "java_method"
    OPENAPI_SCHEMA = "openapi_schema"
    API_ENDPOINT = "api_endpoint"
    MARKDOWN_SECTION = "markdown_section"


@dataclass(frozen=True)
class EmbeddingMetadata:
    """Provenance and generation context for a single embedding.

    Args:
        embedding_model:    Model identifier used for generation.
        embedding_provider: Provider name (e.g. ``"openai_compat"``).
        vector_dimension:   Length of the output vector.
        source_parser:      Parser that produced the source text.
        repository:         Source repository name.
        module:             Module within the repository.
        document:           Source document name.
        file_path:          Absolute or relative path to the source file.
        version_tag:        Version tag of the source artefact.
        extra:              Additional provider-specific metadata.
    """

    embedding_model: str
    embedding_provider: str
    vector_dimension: int
    source_parser: str = ""
    repository: str = ""
    module: str = ""
    document: str = ""
    file_path: str = ""
    version_tag: str = ""
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class EmbeddingResult:
    """Output of a single embedding generation call.

    Matches the canonical output shape::

        {
            "entity": "Payment",
            "vector": [...]
        }

    Args:
        entity:     Human-readable identifier of the embedded item.
        input_type: Semantic category of the input.
        source_id:  Identifier of the originating source.
        vector:     The embedding vector.
        metadata:   Full provenance and generation context.
    """

    entity: str
    input_type: EmbeddingInputType
    source_id: str
    vector: list[float]
    metadata: EmbeddingMetadata

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serialisable representation."""
        return {
            "entity": self.entity,
            "input_type": self.input_type.value,
            "source_id": self.source_id,
            "vector": self.vector,
            "metadata": {
                "embedding_model": self.metadata.embedding_model,
                "embedding_provider": self.metadata.embedding_provider,
                "vector_dimension": self.metadata.vector_dimension,
                "source_parser": self.metadata.source_parser,
                "repository": self.metadata.repository,
                "module": self.metadata.module,
                "document": self.metadata.document,
                "file_path": self.metadata.file_path,
                "version_tag": self.metadata.version_tag,
            },
        }
