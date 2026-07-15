"""Normalisation rules package.

Exports all individual rules and the :func:`default_rule_chain` factory that
composes them into the canonical normalisation pipeline.

Default pipeline order:

1. :class:`~rules.source_pattern.SourcePatternRule` — source-specific name extraction
2. :class:`~rules.casing.CasingRule`               — PascalCase normalisation
3. :class:`~rules.abbreviation.AbbreviationRule`   — abbreviation normalisation
4. :class:`~rules.synonym.SynonymRule`             — synonym resolution
"""
from __future__ import annotations

from .abbreviation import AbbreviationRule
from .base import NormalizationRule, RuleChain
from .casing import CasingRule
from .source_pattern import SourcePatternRule
from .synonym import SynonymRule
from .type_map import TypeMapRule


def default_rule_chain() -> RuleChain:
    """Build the default normalisation rule chain."""
    return RuleChain(
        [
            SourcePatternRule(),
            CasingRule(),
            AbbreviationRule(),
            SynonymRule(),
        ]
    )


__all__ = [
    "NormalizationRule",
    "RuleChain",
    "AbbreviationRule",
    "CasingRule",
    "SourcePatternRule",
    "SynonymRule",
    "TypeMapRule",
    "default_rule_chain",
]
