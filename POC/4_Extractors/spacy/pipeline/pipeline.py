"""spaCy extraction pipeline — Phase 4, Chunks 4.1 & 4.2.

Pipeline component order::

    Parser Output
          │
          ▼
    domain_entity_ruler      (vocabulary-based entity matching)
          │
          ▼
    content_version_extractor  (regex-based version detection from text)
          │
          ▼
    version_tagger           (metadata + path + content priority chain)
          │
          ▼
    Entity Output  (shared.models.Entity list)

Additional extractors may be registered via
:func:`~pipeline.registry.register_component` and are appended after the
version tagger.
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any

import spacy
from spacy.language import Language

from shared.models import ExtractionResult, ExtractionStatus, SourceMetadata

from matcher.entity_matcher import add_entity_matcher
from vocabulary import VocabularyEntry

# Trigger spaCy factory registrations (side-effect imports — no cycles).
from pipeline.version_tagger import VersionTaggerComponent  # noqa: F401
from pipeline.registry import apply_registered_components
from pipeline.converter import doc_to_entities

# Register the content_version_extractor factory.
import version.content_extractor  # noqa: F401

logger = logging.getLogger(__name__)

_DEFAULT_PIPELINE_ID = "spacy_entity_extractor"


def _ensure_poc_on_path() -> None:
    """Add POC/ to sys.path so ``shared`` is importable.

    File: POC/3_Extractors/spacy/pipeline/pipeline.py → parents[3] = POC/.
    """
    poc_root = str(Path(__file__).resolve().parents[3])
    if poc_root not in sys.path:
        sys.path.insert(0, poc_root)


_ensure_poc_on_path()


def build_nlp(entries: list[VocabularyEntry] | None = None) -> Language:
    """Build a configured spaCy Language pipeline.

    Stages added in order:

    1. ``domain_entity_ruler``       — vocabulary matching
    2. ``content_version_extractor`` — text-based version detection
    3. ``version_tagger``            — 3-priority version injection
    4. Any externally registered components

    Args:
        entries: Domain vocabulary. Defaults to the built-in set.

    Returns:
        Ready-to-use :class:`~spacy.language.Language` instance.
    """
    nlp: Language = spacy.blank("en")

    add_entity_matcher(nlp, entries=entries)
    nlp.add_pipe("content_version_extractor")
    nlp.add_pipe("version_tagger")
    apply_registered_components(nlp)

    logger.info("spaCy pipeline built: %s", " → ".join(nlp.pipe_names))
    return nlp


class SpacyExtractionPipeline:
    """High-level wrapper around a configured spaCy Language pipeline.

    Provides a stable ``run()`` interface consumed by downstream callers.
    The underlying spaCy model is built once on construction and reused
    across multiple calls.

    Args:
        nlp:         Pre-built spaCy Language pipeline.
        pipeline_id: Human-readable name for log messages.
    """

    def __init__(
        self,
        nlp: Language,
        pipeline_id: str = _DEFAULT_PIPELINE_ID,
    ) -> None:
        self._nlp = nlp
        self._pipeline_id = pipeline_id

    @classmethod
    def build(
        cls,
        entries: list[VocabularyEntry] | None = None,
        pipeline_id: str = _DEFAULT_PIPELINE_ID,
    ) -> "SpacyExtractionPipeline":
        """Build and return a ready-to-use :class:`SpacyExtractionPipeline`."""
        return cls(nlp=build_nlp(entries=entries), pipeline_id=pipeline_id)

    @property
    def pipe_names(self) -> list[str]:
        """Return the names of all components in the underlying pipeline."""
        return list(self._nlp.pipe_names)

    def run(
        self,
        text: str,
        source_metadata: SourceMetadata,
        extra_metadata: dict[str, Any] | None = None,
        source_parser: str | None = None,
    ) -> ExtractionResult:
        """Extract entities from *text* and return an :class:`ExtractionResult`.

        Args:
            text:            Input text from an upstream parser.
            source_metadata: Provenance for version-tag derivation.
            extra_metadata:  Extra key/value pairs merged into metadata.
            source_parser:   Identifier of the upstream parser
                             (``"java_parser"``, ``"openapi_parser"``, …).

        Returns:
            :class:`ExtractionResult` with all matched, version-tagged entities.
        """
        merged_meta: dict[str, Any] = {
            **source_metadata.metadata,
            **(extra_metadata or {}),
        }

        doc = self._nlp.make_doc(text)
        doc.user_data["source_metadata"] = {
            "source_id": source_metadata.source_id,
            "location": source_metadata.location,
            "source_type": source_metadata.source_type.value,
            **merged_meta,
        }
        doc.user_data["source_parser"] = source_parser

        doc = self._nlp(doc)

        entities = doc_to_entities(doc, source_metadata, source_parser)
        status = (
            ExtractionStatus.SUCCESS if entities else ExtractionStatus.PARTIAL
        )

        result = ExtractionResult(
            source=source_metadata,
            entities=entities,
            status=status,
        )
        logger.debug(
            "Pipeline '%s' extracted %d entities from '%s'",
            self._pipeline_id,
            len(entities),
            source_metadata.source_id,
        )
        return result
