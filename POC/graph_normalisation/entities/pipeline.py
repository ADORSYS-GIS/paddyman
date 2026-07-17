"""Graph Normalisation — Canonical Entity Pipeline entry point (Chunk 5.1).

Consumes :class:`~shared.models.ExtractionResult` objects from any parser or
extractor and produces a deduplicated list of :class:`~models.CanonicalEntity`
objects.

Usage::

    from shared.models import ExtractionResult
    from entities.pipeline import normalise_entities

    results: list[ExtractionResult] = [...]   # from any parser
    entities = normalise_entities(results)

Pipeline stages (in order):

1. :class:`~adapter.EntitySourceAdapter` — convert each Entity to EntitySource
2. :class:`~normalizer.EntityNormalizer` — apply rule chain to get canonical ID/type
3. :class:`~merger.EntityMerger`         — merge by canonical ID, deduplicate aliases
"""
from __future__ import annotations

import logging

from shared.models import ExtractionResult

from .adapter import EntitySourceAdapter
from .merger import EntityMerger
from .models import CanonicalEntity
from .normalizer import EntityNormalizer, NormalizationOutput

logger = logging.getLogger(__name__)


def normalise_entities(
    results: list[ExtractionResult],
    normalizer: EntityNormalizer | None = None,
    adapter: EntitySourceAdapter | None = None,
    merger: EntityMerger | None = None,
) -> list[CanonicalEntity]:
    """Normalise entities from multiple :class:`~shared.models.ExtractionResult` objects.

    Failures on individual entities are logged and skipped; the pipeline
    continues processing the remaining entities.

    Args:
        results:    ExtractionResult objects from any parser or extractor.
        normalizer: Custom normalizer; uses :class:`~normalizer.EntityNormalizer`
                    with defaults when ``None``.
        adapter:    Custom adapter; uses :class:`~adapter.EntitySourceAdapter`
                    when ``None``.
        merger:     Custom merger; uses :class:`~merger.EntityMerger` when ``None``.

    Returns:
        Deduplicated list of :class:`~models.CanonicalEntity` objects, sorted
        by canonical ID.
    """
    _normalizer = normalizer if normalizer is not None else EntityNormalizer()
    _adapter = adapter if adapter is not None else EntitySourceAdapter()
    _merger = merger if merger is not None else EntityMerger()

    raw_count = sum(len(r.entities) for r in results)
    outputs: list[NormalizationOutput] = []

    for result in results:
        for entity in result.entities:
            try:
                source = _adapter.adapt(entity)
                out = _normalizer.normalise(source)
                if out is not None:
                    outputs.append(out)
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "Failed to normalise entity '%s': %s",
                    getattr(entity, "name", "<unknown>"),
                    exc,
                )

    canonical = _merger.merge(outputs)

    logger.info(
        "Normalised %d raw entities from %d result(s) into %d canonical entities",
        raw_count,
        len(results),
        len(canonical),
    )
    return canonical
