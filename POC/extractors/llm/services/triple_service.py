"""Triple extraction service — composes LLM extraction with triple building.

Responsibilities:
- Accept text from any upstream parser (Java, Markdown, OpenAPI).
- Call :class:`~services.extraction_service.ExtractionService` to obtain
  structured entities and relationships from the LLM.
- Pass the result to :class:`~triples.triple_builder.TripleBuilder` to
  generate human-readable triples.
- Return both triples and the raw :class:`~shared.models.ExtractionResult`
  so downstream graph-normalisation stages can use UUID references.
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

_poc_root = str(Path(__file__).resolve().parents[3])
if _poc_root not in sys.path:
    sys.path.insert(0, _poc_root)

from shared.models import ExtractionResult, SourceMetadata

from ..client.base_client import BaseLLMClient
from .extraction_service import ExtractionService
from ..triples.triple_builder import Triple, TripleBuilder

logger = logging.getLogger(__name__)


class TripleService:
    """End-to-end service: parser text → (triples, ExtractionResult).

    Composes :class:`ExtractionService` (LLM call) with
    :class:`TripleBuilder` (triple generation) in a single ``run()`` call.

    Args:
        client:      Configured LLM client (any :class:`BaseLLMClient`).
        max_retries: Retry attempts on transient errors.
        retry_delay: Seconds to wait between retry attempts.
    """

    def __init__(
        self,
        client: BaseLLMClient,
        max_retries: int | None = None,
        retry_delay: float = 1.0,
    ) -> None:
        self._extractor = ExtractionService(
            client=client,
            max_retries=max_retries,
            retry_delay=retry_delay,
        )
        self._builder = TripleBuilder()

    def run(
        self,
        text: str,
        source_metadata: SourceMetadata,
        source_parser: str | None = None,
    ) -> tuple[list[Triple], ExtractionResult]:
        """Extract triples from *text*.

        Accepts outputs from any upstream parser module (Java, Markdown,
        OpenAPI) operating on resources under ``POC/DataSource/``.

        Args:
            text:            Parsed document content from an upstream parser.
            source_metadata: Provenance for version-tag and metadata injection.
            source_parser:   Identifier of the upstream parser
                             (``"java_parser"``, ``"openapi_parser"``, …).

        Returns:
            ``(triples, extraction_result)`` — never raises; failures surface
            in ``extraction_result.errors``.
        """
        result = self._extractor.run(text, source_metadata, source_parser)
        triples = self._builder.build(result)
        logger.info(
            "TripleService: %d triple(s) from '%s'",
            len(triples),
            source_metadata.source_id,
        )
        return triples, result
