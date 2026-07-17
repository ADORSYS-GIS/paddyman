"""Canonical relationship normalisation pipeline."""
from __future__ import annotations

import logging
from uuid import UUID, uuid5, NAMESPACE_URL

from entities.models import CanonicalEntity
from shared.models import Relationship

from .adapter import adapt_relationship
from .models import RawRelationship
from .rules import RelationshipTypeMapper

logger = logging.getLogger(__name__)


class RelationshipNormalizer:
    """Normalize parser relationships into shared canonical relationships."""

    def __init__(self, mapper: RelationshipTypeMapper | None = None) -> None:
        self._mapper = mapper if mapper is not None else RelationshipTypeMapper()

    def normalize(
        self,
        relationships: list[object],
        entities: list[CanonicalEntity],
    ) -> list[Relationship]:
        """Normalize *relationships* using canonical or deduplicated *entities*."""
        entity_index = self._entity_index(entities)
        normalized: dict[tuple[UUID, UUID, str], Relationship] = {}
        for raw_input in relationships:
            raw = adapt_relationship(raw_input)
            rel = self._normalize_one(raw, entity_index)
            key = (rel.source_entity_id, rel.target_entity_id, rel.type)
            normalized[key] = self._merge_duplicate(normalized.get(key), rel)
        return sorted(normalized.values(), key=lambda rel: rel.type + str(rel.id))

    def _normalize_one(
        self,
        raw: RawRelationship,
        entity_index: dict[str, CanonicalEntity],
    ) -> Relationship:
        source = entity_index.get(raw.source.lower())
        target = entity_index.get(raw.target.lower())
        source_id = self._stable_id(source.id if source else raw.source)
        target_id = self._stable_id(target.id if target else raw.target)
        canonical_type = self._mapper.normalize(raw.relationship_type)
        return Relationship(
            id=self._relationship_id(source_id, target_id, canonical_type),
            source_entity_id=source_id,
            target_entity_id=target_id,
            type=canonical_type,
            confidence=raw.confidence,
            properties=self._properties(raw, source, target, canonical_type),
        )

    def _properties(
        self,
        raw: RawRelationship,
        source: CanonicalEntity | None,
        target: CanonicalEntity | None,
        canonical_type: str,
    ) -> dict:
        return {
            "source": source.id if source else raw.source,
            "target": target.id if target else raw.target,
            "original_type": raw.relationship_type,
            "normalized_relationship": canonical_type,
            "source_parser": raw.source_parser,
            "repository": raw.repository,
            "module": raw.module,
            "document": raw.document,
            "file_path": raw.file_path,
            "version_tag": raw.version_tag,
            "confidence": raw.confidence,
            "provenance": [self._provenance(raw)],
        }

    def _merge_duplicate(self, existing: Relationship | None, new: Relationship) -> Relationship:
        if existing is None:
            return new
        if new.confidence > existing.confidence:
            winner, other = new, existing
        else:
            winner, other = existing, new
        winner.properties["provenance"].extend(other.properties.get("provenance", []))
        originals = [winner.properties["original_type"], other.properties["original_type"]]
        winner.properties["original_types"] = sorted(set(originals))
        winner.confidence = max(existing.confidence, new.confidence)
        return winner

    def _entity_index(self, entities: list[CanonicalEntity]) -> dict[str, CanonicalEntity]:
        index: dict[str, CanonicalEntity] = {}
        for entity in entities:
            for name in [entity.id, *entity.aliases]:
                index[name.lower()] = entity
        return index

    def _stable_id(self, value: str) -> UUID:
        return uuid5(NAMESPACE_URL, f"paddyman:relationship-entity:{value}")

    def _relationship_id(self, source: UUID, target: UUID, rel_type: str) -> UUID:
        return uuid5(NAMESPACE_URL, f"paddyman:relationship:{source}:{target}:{rel_type}")

    def _provenance(self, raw: RawRelationship) -> dict:
        return {
            "source_entity": raw.source,
            "target_entity": raw.target,
            "original_type": raw.relationship_type,
            "source_parser": raw.source_parser,
            "repository": raw.repository,
            "module": raw.module,
            "document": raw.document,
            "file_path": raw.file_path,
            "version_tag": raw.version_tag,
            "confidence": raw.confidence,
            "raw": raw.provenance,
        }


def normalize_relationships(
    relationships: list[object],
    entities: list[CanonicalEntity],
) -> list[Relationship]:
    """Normalize raw relationships with the default canonical vocabulary."""
    return RelationshipNormalizer().normalize(relationships, entities)