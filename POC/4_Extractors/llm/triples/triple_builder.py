"""Build human-readable triples from a structured :class:`ExtractionResult`.

Triples are RDF-style ``(subject, predicate, object)`` records enriched with
provenance metadata.  They act as the interface between the LLM extraction
output and downstream graph-normalisation stages.

Design:
- Never raises — bad relationships are skipped with a warning.
- Deduplicates triples with identical ``(subject, predicate, object)``,
  keeping the highest-confidence instance.
- Each :class:`Triple` carries a back-reference to the original
  :class:`~shared.models.Relationship` so graph stages can work with UUIDs.
"""
from __future__ import annotations

import logging
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from uuid import UUID

_poc_root = str(Path(__file__).resolve().parents[3])
if _poc_root not in sys.path:
    sys.path.insert(0, _poc_root)

from shared.models import Entity, ExtractionResult, Relationship

logger = logging.getLogger(__name__)


@dataclass
class Triple:
    """An RDF-style triple with provenance metadata.

    Attributes:
        subject:      Human-readable name of the originating entity.
        predicate:    Relationship type in upper-case (e.g. ``"USES"``).
        object_name:  Human-readable name of the target entity.
        confidence:   Extraction confidence in ``[0.0, 1.0]``.
        metadata:     Provenance: repository, module, source_parser, …
        relationship: Backing :class:`~shared.models.Relationship` for
                      graph-normalisation stages that need UUID references.
    """

    subject: str
    predicate: str
    object_name: str
    confidence: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)
    relationship: Relationship | None = None


class TripleBuilder:
    """Convert an :class:`~shared.models.ExtractionResult` into :class:`Triple` objects.

    Instantiate once and call :meth:`build` for each result.
    """

    def build(self, result: ExtractionResult) -> list[Triple]:
        """Generate triples from *result*.

        Args:
            result: Structured output from :class:`~services.extraction_service.ExtractionService`.

        Returns:
            Deduplicated list of :class:`Triple` objects, ordered by first
            occurrence.
        """
        entity_index: dict[UUID, Entity] = {e.id: e for e in result.entities}
        base_meta = self._base_metadata(result)

        triples: list[Triple] = []
        seen: dict[tuple[str, str, str], int] = {}

        for rel in result.relationships:
            src = entity_index.get(rel.source_entity_id)
            tgt = entity_index.get(rel.target_entity_id)

            if src is None or tgt is None:
                missing = rel.source_entity_id if src is None else rel.target_entity_id
                logger.warning("Skipping triple: entity UUID '%s' not found", missing)
                continue

            triple = Triple(
                subject=src.name,
                predicate=rel.type.upper(),
                object_name=tgt.name,
                confidence=rel.confidence,
                metadata={**base_meta, **self._entity_metadata(src)},
                relationship=rel,
            )

            key = (triple.subject.lower(), triple.predicate, triple.object_name.lower())
            if key in seen:
                if triple.confidence > triples[seen[key]].confidence:
                    triples[seen[key]] = triple
                logger.debug("Deduplicated triple %s", key)
            else:
                seen[key] = len(triples)
                triples.append(triple)

        logger.debug(
            "Built %d triple(s) from %d relationship(s)",
            len(triples),
            len(result.relationships),
        )
        return triples

    # ------------------------------------------------------------------

    def _base_metadata(self, result: ExtractionResult) -> dict[str, Any]:
        """Extract source-level provenance from *result*."""
        src_meta = result.source.metadata
        return {
            "source_document": result.source.source_id,
            "repository": src_meta.get("repository"),
            "module": src_meta.get("module"),
            "file_path": src_meta.get("file_path"),
            "version_tag": src_meta.get("version"),
        }

    def _entity_metadata(self, entity: Entity) -> dict[str, Any]:
        """Extract entity-level provenance (source_parser)."""
        meta: dict[str, Any] = {}
        parser = entity.properties.get("source_parser")
        if parser:
            meta["source_parser"] = parser
        return meta
