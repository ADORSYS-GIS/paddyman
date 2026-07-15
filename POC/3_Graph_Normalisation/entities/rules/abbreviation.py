"""AbbreviationRule — normalise residual ALL-CAPS abbreviation segments.

Applied after :class:`~rules.casing.CasingRule`.  In most cases the casing
rule already expands ALLCAPS sequences correctly (``"PaymentAPIController"``
→ ``"PaymentApiController"``).  This rule acts as a safety net for rare
edge-cases where a standalone ALL-CAPS token survives into the output (e.g.
when source pattern rules return a raw abbreviation such as ``"SEPA"``).

The table is extensible — pass a custom mapping to :class:`AbbreviationRule`.
"""
from __future__ import annotations

import re

# Default abbreviation table.
# Key:   ALL-CAPS token as it would appear after incomplete normalisation.
# Value: preferred PascalCase replacement.
DEFAULT_ABBREVIATIONS: dict[str, str] = {
    "ID": "Id",
    "API": "Api",
    "URL": "Url",
    "URI": "Uri",
    "HTTP": "Http",
    "HTTPS": "Https",
    "PSD2": "Psd2",
    "IBAN": "Iban",
    "BIC": "Bic",
    "SEPA": "Sepa",
    "TPP": "Tpp",
    "ASPSP": "Aspsp",
    "AIS": "Ais",
    "PIS": "Pis",
    "PIIS": "Piis",
    "SCA": "Sca",
    "PSU": "Psu",
    "XML": "Xml",
    "JSON": "Json",
    "DTO": "Dto",
    "SPI": "Spi",
    "CMS": "Cms",
    "DB": "Db",
}

# Matches a run of 2 or more uppercase ASCII letters
_UPPER_RUN = re.compile(r"[A-Z]{2,}")


def normalise_abbreviations(name: str, table: dict[str, str]) -> str:
    """Replace ALL-CAPS runs in *name* using *table*.

    Only substitutes tokens that are keys in *table*; unknown abbreviations
    are left unchanged.
    """
    if not name:
        return name
    return _UPPER_RUN.sub(lambda m: table.get(m.group(0), m.group(0)), name)


class AbbreviationRule:
    """Replace residual ALL-CAPS abbreviation segments with normalised forms."""

    def __init__(self, table: dict[str, str] | None = None) -> None:
        self._table = table if table is not None else DEFAULT_ABBREVIATIONS

    def apply(
        self,
        name: str,
        entity_type: str,
        source_parser: str,
    ) -> str | None:
        """Return normalised *name*, or ``None`` when no change is needed."""
        _ = (entity_type, source_parser)
        if not name:
            return None
        result = normalise_abbreviations(name, self._table)
        return result if result != name else None
