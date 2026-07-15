"""EntityMerger — merges NormalizationOutput records into CanonicalEntity objects.

Entities sharing the same canonical ID are merged into a single
:class:`~models.CanonicalEntity`.  All provenance (aliases, sources) is
preserved.  Duplicate aliases are deduplicated while preserving first-seen
order.  Sources are accumulated in encounter order.
"""
from __future__ import annotations

import logging
from collections import defaultdict

from .models import CanonicalEntity, EntitySource
from .normalizer import NormalizationOutput

logger = logging.getLogger(__name__)


class EntityMerger:
    """Merge normalised entity outputs into deduplicated CanonicalEntity objects."""

    def merge(
        self,
        outputs: list[NormalizationOutput],
    ) -> list[CanonicalEntity]:
        """Merge *outputs* by canonical ID into a deduplicated list.

        Entities with the same ``canonical_id`` are merged.  When types
        conflict, the type from the first occurrence is used and a warning is
        logged.  The resulting list is sorted alphabetically by canonical ID
        for deterministic ordering.

        Args:
            outputs: Normalised records from :class:`~normalizer.EntityNormalizer`.

        Returns:
            Sorted, deduplicated list of :class:`~models.CanonicalEntity` objects.
        """
        if not outputs:
            return []

        buckets: dict[str, list[NormalizationOutput]] = defaultdict(list)
        for out in outputs:
            buckets[out.canonical_id].append(out)

        entities = [
            self._build(cid, group)
            for cid, group in sorted(buckets.items())
        ]

        logger.debug(
            "Merged %d normalised outputs into %d canonical entities",
            len(outputs),
            len(entities),
        )
        return entities

    # ──────────────────────────────────────────────────────────────────────────

    def _build(
        self,
        canonical_id: str,
        group: list[NormalizationOutput],
    ) -> CanonicalEntity:
        """Build a single :class:`~models.CanonicalEntity` from a merged group."""
        types = [o.canonical_type for o in group]
        if len(set(types)) > 1:
            logger.warning(
                "Conflicting types for canonical entity '%s': %s — using '%s'",
                canonical_id,
                types,
                types[0],
            )
        canonical_type = types[0]

        seen_aliases: set[str] = set()
        aliases: list[str] = []
        sources: list[EntitySource] = []

        for out in group:
            alias = out.source.original_name
            if alias not in seen_aliases:
                seen_aliases.add(alias)
                aliases.append(alias)
            sources.append(out.source)

        confidence = round(
            sum(s.confidence for s in sources) / len(sources),
            4,
        )

        return CanonicalEntity(
            id=canonical_id,
            type=canonical_type,
            aliases=aliases,
            sources=sources,
            confidence=confidence,
        )
