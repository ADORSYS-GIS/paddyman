"""Embedding generation service — orchestrates client, text preparation, and retry.

Responsibilities:
- Build embedding text from entity or chunk inputs.
- Call the embedding client with automatic retry on transient errors.
- Assemble :class:`EmbeddingResult` with full provenance metadata.
- Log failures gracefully; surface errors via return value.
"""
from __future__ import annotations

import logging
import sys
import time
from pathlib import Path

_poc_root = str(Path(__file__).resolve().parents[3])
if _poc_root not in sys.path:
    sys.path.insert(0, _poc_root)

from shared.config import settings
from shared.models import Entity, SourceMetadata

try:
    from client.base_client import BaseEmbeddingClient, EmbeddingClientError, EmbeddingRequest  # standalone mode
    from models.embedding_result import EmbeddingInputType, EmbeddingMetadata, EmbeddingResult
except ImportError:
    from embeddings.client.base_client import BaseEmbeddingClient, EmbeddingClientError, EmbeddingRequest  # package mode
    from embeddings.models.embedding_result import EmbeddingInputType, EmbeddingMetadata, EmbeddingResult

logger = logging.getLogger(__name__)


def _truncate(text: str) -> str:
    """Truncate *text* to ``settings.embed_max_chars`` characters (0 = no limit)."""
    limit = settings.embed_max_chars
    if limit > 0 and len(text) > limit:
        logger.debug("Truncating text from %d to %d chars for embedding.", len(text), limit)
        return text[:limit]
    return text


def _is_non_retryable(exc: EmbeddingClientError) -> bool:
    """Return True when the error is a permanent provider rejection (e.g. 400)."""
    msg = str(exc).lower()
    return "too long" in msg or "invalid_request_error" in msg or "400" in msg


class EmbeddingService:
    """Single-item embedding service.

    Args:
        client:      Configured embedding client (any :class:`BaseEmbeddingClient`).
        max_retries: Retry attempts on transient errors.
        retry_delay: Seconds between retry attempts.
    """

    def __init__(
        self,
        client: BaseEmbeddingClient,
        max_retries: int | None = None,
        retry_delay: float = 1.0,
    ) -> None:
        self._client = client
        self._max_retries = (
            max_retries if max_retries is not None else settings.embed_max_retries
        )
        self._retry_delay = retry_delay

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def embed_entity(
        self,
        entity: Entity,
        source_metadata: SourceMetadata,
        source_parser: str = "",
    ) -> EmbeddingResult:
        """Generate an embedding for a shared-model :class:`Entity`.

        Args:
            entity:          The entity to embed.
            source_metadata: Provenance of the entity's source.
            source_parser:   Parser that produced the entity.

        Returns:
            :class:`EmbeddingResult` — never raises.
        """
        text = _entity_text(entity)
        input_type = _entity_input_type(entity)
        return self._embed(
            text=text,
            label=entity.name,
            input_type=input_type,
            source_id=source_metadata.source_id,
            source_metadata=source_metadata,
            source_parser=source_parser,
        )

    def embed_chunk(
        self,
        text: str,
        label: str,
        input_type: EmbeddingInputType,
        source_metadata: SourceMetadata,
        source_parser: str = "",
    ) -> EmbeddingResult:
        """Generate an embedding for a parsed document chunk.

        Args:
            text:            Chunk text to embed.
            label:           Human-readable identifier (section title, class name…).
            input_type:      Semantic category of the chunk.
            source_metadata: Provenance of the chunk's source.
            source_parser:   Parser that produced the chunk.

        Returns:
            :class:`EmbeddingResult` — never raises.
        """
        return self._embed(
            text=text,
            label=label,
            input_type=input_type,
            source_id=source_metadata.source_id,
            source_metadata=source_metadata,
            source_parser=source_parser,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _embed(
        self,
        text: str,
        label: str,
        input_type: EmbeddingInputType,
        source_id: str,
        source_metadata: SourceMetadata,
        source_parser: str,
    ) -> EmbeddingResult:
        request = EmbeddingRequest(text=_truncate(text))
        response = self._call_with_retry(request, source_id)

        if response is None:
            logger.error("All retry attempts exhausted for '%s'.", source_id)
            return EmbeddingResult(
                entity=label,
                input_type=input_type,
                source_id=source_id,
                vector=[],
                metadata=_build_metadata(
                    model=self._client.model,
                    provider=self._client.provider_name,
                    dimension=0,
                    source_metadata=source_metadata,
                    source_parser=source_parser,
                ),
            )

        return EmbeddingResult(
            entity=label,
            input_type=input_type,
            source_id=source_id,
            vector=response.vector,
            metadata=_build_metadata(
                model=response.model,
                provider=response.provider,
                dimension=response.dimension,
                source_metadata=source_metadata,
                source_parser=source_parser,
            ),
        )

    def _call_with_retry(self, request: EmbeddingRequest, source_id: str):  # type: ignore[return]
        """Call the client with up to ``_max_retries`` retries."""
        attempts = self._max_retries + 1
        for attempt in range(1, attempts + 1):
            try:
                return self._client.embed(request)
            except EmbeddingClientError as exc:
                if _is_non_retryable(exc):
                    logger.warning("Skipping non-retryable embed error for '%s': %s", source_id, exc)
                    return None
                logger.warning(
                    "Embed attempt %d/%d failed for '%s': %s",
                    attempt, attempts, source_id, exc,
                )
                if attempt < attempts:
                    time.sleep(self._retry_delay)
        return None


# ------------------------------------------------------------------
# Module-level helpers (pure functions — no class coupling)
# ------------------------------------------------------------------

def _entity_text(entity: Entity) -> str:
    """Build the embedding text for an :class:`Entity`."""
    parts = [f"{entity.type}: {entity.name}"]
    description = entity.properties.get("description") or entity.properties.get("summary")
    if description:
        parts.append(str(description))
    return " ".join(parts)


def _entity_input_type(entity: Entity) -> EmbeddingInputType:
    """Map an entity type label to an :class:`EmbeddingInputType`."""
    mapping: dict[str, EmbeddingInputType] = {
        "class": EmbeddingInputType.JAVA_CLASS,
        "method": EmbeddingInputType.JAVA_METHOD,
        "endpoint": EmbeddingInputType.API_ENDPOINT,
        "schema": EmbeddingInputType.OPENAPI_SCHEMA,
        "section": EmbeddingInputType.MARKDOWN_SECTION,
    }
    return mapping.get(entity.type.lower(), EmbeddingInputType.ENTITY)


def _build_metadata(
    model: str,
    provider: str,
    dimension: int,
    source_metadata: SourceMetadata,
    source_parser: str,
) -> EmbeddingMetadata:
    m = source_metadata.metadata
    return EmbeddingMetadata(
        embedding_model=model,
        embedding_provider=provider,
        vector_dimension=dimension,
        source_parser=source_parser,
        repository=str(m.get("repository", "")),
        module=str(m.get("module", "")),
        document=str(m.get("document", "")),
        file_path=str(m.get("file_path", "")),
        version_tag=str(m.get("version", "")),
    )
