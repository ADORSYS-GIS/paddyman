"""Entity deduplication layer for canonical entities (Chunk 5.2)."""
from __future__ import annotations

import logging

from .dedup_rules import DeduplicationMatch, DeduplicationRule, default_deduplication_rules
from .models import CanonicalEntity, EntitySource

logger = logging.getLogger(__name__)


class EntityDeduplicator:
    """Identify and merge equivalent canonical entities from different sources."""

    def __init__(self, rules: list[DeduplicationRule] | None = None) -> None:
        self._rules = rules if rules is not None else default_deduplication_rules()

    def deduplicate(self, entities: list[CanonicalEntity]) -> list[CanonicalEntity]:
        """Return deduplicated canonical entities sorted by ID."""
        if not entities:
            return []
        parent = list(range(len(entities)))
        matches: dict[tuple[int, int], DeduplicationMatch] = {}

        for left in range(len(entities)):
            for right in range(left + 1, len(entities)):
                match = self._best_match(entities[left], entities[right])
                if match is not None:
                    self._union(parent, left, right)
                    matches[(left, right)] = match

        groups: dict[int, list[CanonicalEntity]] = {}
        for index, entity in enumerate(entities):
            groups.setdefault(self._find(parent, index), []).append(entity)

        merged = [self._merge_group(group) for group in groups.values()]
        logger.info("Deduplicated %d entities into %d", len(entities), len(merged))
        return sorted(merged, key=lambda entity: entity.id)

    def _best_match(
        self,
        left: CanonicalEntity,
        right: CanonicalEntity,
    ) -> DeduplicationMatch | None:
        """Return the highest-scoring rule match for two entities."""
        matches = [m for rule in self._rules if (m := rule.match(left, right))]
        return max(matches, key=lambda m: (m.score, m.reason)) if matches else None

    def _merge_group(self, group: list[CanonicalEntity]) -> CanonicalEntity:
        """Merge one connected duplicate group while preserving provenance."""
        winner = max(group, key=lambda e: (e.confidence, len(e.sources), e.id))
        aliases = self._unique_aliases(group)
        sources = [source for entity in group for source in entity.sources]
        confidence = self._combined_confidence(group, sources)
        return CanonicalEntity(
            id=winner.id,
            type=self._type_for_group(group, winner),
            aliases=aliases,
            sources=sources,
            confidence=confidence,
            properties=self._merge_properties(group),
        )

    def _type_for_group(self, group: list[CanonicalEntity], winner: CanonicalEntity) -> str:
        """Return winner type, warning if duplicate group has conflicting types."""
        types = {entity.type for entity in group}
        if len(types) > 1:
            logger.warning("Conflicting entity types for '%s': %s", winner.id, sorted(types))
        return winner.type

    def _unique_aliases(self, group: list[CanonicalEntity]) -> list[str]:
        """Return aliases and IDs from group in deterministic first-seen order."""
        seen: set[str] = set()
        aliases: list[str] = []
        for entity in group:
            for alias in [entity.id, *entity.aliases]:
                if alias not in seen:
                    seen.add(alias)
                    aliases.append(alias)
        return aliases

    def _merge_properties(self, group: list[CanonicalEntity]) -> dict:
        """Merge property bags without modifying embeddings."""
        merged: dict = {"deduplicated_from": [entity.id for entity in group]}
        original_ids = [str(s.entity_ref.id) for e in group for s in e.sources if s.entity_ref]
        if original_ids:
            merged["original_entity_ids"] = original_ids
        for entity in group:
            for key, value in entity.properties.items():
                merged.setdefault(key, value)
        return merged

    def _combined_confidence(
        self,
        group: list[CanonicalEntity],
        sources: list[EntitySource],
    ) -> float:
        """Combine entity and source confidence scores deterministically."""
        scores = [entity.confidence for entity in group] + [source.confidence for source in sources]
        return round(sum(scores) / len(scores), 4) if scores else 1.0

    def _find(self, parent: list[int], index: int) -> int:
        """Find connected-component root with path compression."""
        if parent[index] != index:
            parent[index] = self._find(parent, parent[index])
        return parent[index]

    def _union(self, parent: list[int], left: int, right: int) -> None:
        """Join two connected components."""
        left_root = self._find(parent, left)
        right_root = self._find(parent, right)
        if left_root != right_root:
            parent[right_root] = left_root


def deduplicate_entities(entities: list[CanonicalEntity]) -> list[CanonicalEntity]:
    """Deduplicate canonical entities with the default deterministic rules."""
    return EntityDeduplicator().deduplicate(entities)