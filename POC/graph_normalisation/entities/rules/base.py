"""Abstract base for normalisation rules and the rule-chain combinator.

All normalisation rules implement :class:`NormalizationRule`.
Rules are composed into an ordered pipeline via :class:`RuleChain` — each
rule receives the output of the previous rule.
"""
from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class NormalizationRule(Protocol):
    """Protocol satisfied by every normalisation rule.

    A rule may return ``None`` to signal it does not apply; in that case the
    :class:`RuleChain` passes the current value to the next rule unchanged.
    """

    def apply(
        self,
        name: str,
        entity_type: str,
        source_parser: str,
    ) -> str | None:
        """Transform *name* or return ``None`` to skip this rule.

        Args:
            name:          Current (possibly already partly normalised) name.
            entity_type:   Type label from the originating parser.
            source_parser: Parser/extractor that produced this entity.

        Returns:
            Transformed name, or ``None`` when this rule does not apply.
        """
        ...


class RuleChain:
    """Apply an ordered list of :class:`NormalizationRule` instances as a pipeline.

    Each rule receives the output of the previous rule.  Rules returning
    ``None`` are skipped; the current value is forwarded to the next rule
    unchanged.  If no rule produces a result, the original name is returned.
    """

    def __init__(self, rules: list[NormalizationRule]) -> None:
        self._rules = list(rules)

    def apply(self, name: str, entity_type: str, source_parser: str) -> str:
        """Run all rules in sequence and return the final normalised name."""
        result = name
        for rule in self._rules:
            candidate = rule.apply(result, entity_type, source_parser)
            if candidate is not None:
                result = candidate
        return result
