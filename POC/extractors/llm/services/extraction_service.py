"""Extraction service — orchestrates client, prompt builder, and response parser.

Responsibilities:
- Build the prompt from parser output and source metadata.
- Call the LLM client with automatic retry on transient errors.
- Parse and validate the response into shared model objects.
- Log failures; never raise — all errors surface in :class:`ExtractionResult`.
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
from shared.models import ExtractionResult, ExtractionStatus, SourceMetadata

from ..client.base_client import BaseLLMClient, CompletionRequest, LLMClientError
from ..parser.response_parser import ResponseParser
from ..prompts.extractor_prompt import build_request

logger = logging.getLogger(__name__)


class ExtractionService:
    """LLM-based entity and relationship extraction service.

    Args:
        client:      Configured LLM client (any :class:`BaseLLMClient`).
        max_retries: Retry attempts on transient errors. Defaults to
                     ``settings.llm_max_retries``.
        retry_delay: Seconds between retry attempts.
    """

    def __init__(
        self,
        client: BaseLLMClient,
        max_retries: int | None = None,
        retry_delay: float = 1.0,
    ) -> None:
        self._client = client
        self._max_retries = (
            max_retries if max_retries is not None else settings.llm_max_retries
        )
        self._retry_delay = retry_delay
        self._parser = ResponseParser()

    def run(
        self,
        text: str,
        source_metadata: SourceMetadata,
        source_parser: str | None = None,
    ) -> ExtractionResult:
        """Extract entities and relationships from *text*.

        Accepts outputs from any upstream parser (Java, Markdown, OpenAPI).

        Args:
            text:            Parsed document content from an upstream parser.
            source_metadata: Provenance for extracted entities.
            source_parser:   Parser that produced *text*
                             (e.g. ``"java_parser"``, ``"openapi_parser"``).

        Returns:
            :class:`ExtractionResult` — never raises.
        """
        request = build_request(
            text=text,
            source_id=source_metadata.source_id,
            source_parser=source_parser,
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens,
        )

        raw = self._complete_with_retry(request, source_metadata.source_id)
        if raw is None:
            return ExtractionResult(
                source=source_metadata,
                status=ExtractionStatus.FAILED,
                errors=["All retry attempts exhausted without a response."],
            )

        return self._parser.parse(raw, source_metadata, source_parser)

    # ------------------------------------------------------------------

    def _complete_with_retry(
        self,
        request: CompletionRequest,
        source_id: str,
    ) -> str | None:
        """Call the client with up to ``_max_retries`` retries."""
        last_error: Exception | None = None
        attempts = self._max_retries + 1

        for attempt in range(1, attempts + 1):
            try:
                response = self._client.complete(request)
                return response.content
            except LLMClientError as exc:
                last_error = exc
                logger.warning(
                    "LLM attempt %d/%d failed for '%s': %s",
                    attempt,
                    attempts,
                    source_id,
                    exc,
                )
                if attempt < attempts:
                    time.sleep(self._retry_delay)

        logger.error(
            "All %d LLM attempts failed for '%s': %s",
            attempts,
            source_id,
            last_error,
        )
        return None
