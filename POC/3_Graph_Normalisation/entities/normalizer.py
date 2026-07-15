"""EntityNormalizer — applies normalisation rules to produce a canonical ID and type.

Instantiate once and call :meth:`normalise` for each :class:`~models.EntitySource`
record produced by :class:`~adapter.EntitySourceAdapter`.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

from .models import EntitySource
from .rules import RuleChain, default_rule_chain
from .rules.type_map import TypeMapRule

logger = logging.getLogger(__name__)


@dataclass
class NormalizationOutput:
    """Result of normalising a single entity source record.

    Attributes:
        canonical_id:   Deterministic PascalCase identifier.
        canonical_type: Canonical type label from :class:`~rules.type_map.TypeMapRule`.
        source:         The originating :class:`~models.EntitySource`.
    """

    canonical_id: str
    canonical_type: str
    source: EntitySource


class EntityNormalizer:
    """Apply the normalisation rule chain to a single :class:`~models.EntitySource`.

    Args:
        rule_chain: Name-normalisation rules; uses :func:`~rules.default_rule_chain`
                    when ``None``.
        type_rule:  Type-mapping rule; uses :class:`~rules.type_map.TypeMapRule`
                    when ``None``.
    """

    def __init__(
        self,
        rule_chain: RuleChain | None = None,
        type_rule: TypeMapRule | None = None,
    ) -> None:
        self._chain = rule_chain if rule_chain is not None else default_rule_chain()
        self._type_rule = type_rule if type_rule is not None else TypeMapRule()

    def normalise(self, source: EntitySource) -> NormalizationOutput | None:
        """Normalise *source* and return a :class:`NormalizationOutput`.

        Args:
            source: Entity source record from :class:`~adapter.EntitySourceAdapter`.

        Returns:
            Populated :class:`NormalizationOutput`, or ``None`` when normalisation
            produces an empty canonical ID (entity is skipped with a warning).
        """
        raw_name = source.original_name
        raw_type = (
            source.entity_ref.type if source.entity_ref is not None else "concept"
        )

        canonical_id = self._chain.apply(
            name=raw_name,
            entity_type=raw_type,
            source_parser=source.source_parser,
        )

        if not canonical_id or not canonical_id.strip():
            logger.warning(
                "Normalisation produced an empty ID for '%s' from '%s' — skipping",
                raw_name,
                source.source_parser,
            )
            return None

        return NormalizationOutput(
            canonical_id=canonical_id.strip(),
            canonical_type=self._type_rule.normalise_type(raw_type),
            source=source,
        )
