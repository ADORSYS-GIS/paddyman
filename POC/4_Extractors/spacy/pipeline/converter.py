"""Converts a processed spaCy ``Doc`` into shared :class:`~shared.models.Entity` objects.

Separated from the pipeline orchestrator to keep each file focused on a
single responsibility and within the 150-LOC limit.
"""
from __future__ import annotations

from typing import Any

from shared.models import Entity, SourceMetadata


def doc_to_entities(
    doc: Any,
    source_metadata: SourceMetadata,
    source_parser: str | None = None,
) -> list[Entity]:
    """Convert ``doc.ents`` into :class:`Entity` instances.

    Reads version tags, version sources, and raw metadata stored in
    ``doc.user_data`` by upstream pipeline components and assembles a
    de-duplicated list of entities compatible with the shared model.

    Args:
        doc:             Processed spaCy Doc.
        source_metadata: Provenance for the processed text.
        source_parser:   Identifier of the upstream parser that produced the
                         text (e.g. ``"java_parser"``, ``"openapi_parser"``).

    Returns:
        Deduplicated list of :class:`Entity` objects with full provenance.
    """
    version_tags: dict[int, str | None] = doc.user_data.get("version_tags", {})
    version_sources: dict[int, str | None] = doc.user_data.get("version_sources", {})
    raw_meta: dict[str, Any] = doc.user_data.get("source_metadata", {})

    entities: list[Entity] = []
    seen: set[tuple[str, str]] = set()

    for ent in doc.ents:
        dedup_key = (ent.label_, ent.text.lower())
        if dedup_key in seen:
            continue
        seen.add(dedup_key)

        properties: dict[str, Any] = {
            "label": ent.label_,
            "version": version_tags.get(ent.start),
            "version_source": version_sources.get(ent.start),
            "source_parser": source_parser,
            "source": source_metadata.source_id,
            "repository": raw_meta.get("repository"),
            "module": raw_meta.get("module"),
            "file_path": raw_meta.get("file_path"),
            "document": raw_meta.get("document"),
            "confidence": 1.0,
            "extraction_rule": "entity_ruler",
        }

        entities.append(
            Entity(
                type="entity",
                name=ent.text,
                source=source_metadata.source_id,
                properties=properties,
            )
        )

    return entities
