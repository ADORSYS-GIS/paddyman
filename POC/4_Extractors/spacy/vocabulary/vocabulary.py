"""Domain vocabulary definitions for the spaCy entity extraction pipeline.

Defines the canonical set of domain terms that the pipeline recognises as
named entities. Extend :data:`DOMAIN_ENTRIES` to add new terms without
modifying any other component.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class VocabularyEntry:
    """A single entry in the domain vocabulary.

    Attributes:
        term:  Surface form as it appears in text (case-insensitive matching
               is applied by the matcher).
        label: spaCy entity label assigned on match.
        aliases: Additional surface forms for the same concept.
    """

    term: str
    label: str
    aliases: tuple[str, ...] = field(default_factory=tuple)


# ---------------------------------------------------------------------------
# Initial domain vocabulary — extend here to add new terms.
# ---------------------------------------------------------------------------
DOMAIN_ENTRIES: list[VocabularyEntry] = [
    VocabularyEntry(
        term="Payment",
        label="DOMAIN_ENTITY",
        aliases=("payment", "PAYMENT", "payments"),
    ),
    VocabularyEntry(
        term="Account",
        label="DOMAIN_ENTITY",
        aliases=("account", "ACCOUNT", "accounts"),
    ),
    VocabularyEntry(
        term="Consent",
        label="DOMAIN_ENTITY",
        aliases=("consent", "CONSENT", "consents"),
    ),
    VocabularyEntry(
        term="Customer",
        label="DOMAIN_ENTITY",
        aliases=("customer", "CUSTOMER", "customers"),
    ),
    VocabularyEntry(
        term="Transaction",
        label="DOMAIN_ENTITY",
        aliases=("transaction", "TRANSACTION", "transactions"),
    ),
]
