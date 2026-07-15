"""spaCy EntityRuler pattern builders for the domain vocabulary.

Converts :data:`~vocabulary.DOMAIN_ENTRIES` into the ``[{"label": ..., "pattern": ...}]``
format consumed by :class:`spacy.pipeline.EntityRuler`.
"""
from __future__ import annotations

from typing import Any

from vocabulary.vocabulary import DOMAIN_ENTRIES, VocabularyEntry


def build_entity_ruler_patterns(
    entries: list[VocabularyEntry] | None = None,
) -> list[dict[str, Any]]:
    """Return spaCy EntityRuler pattern dicts for the given vocabulary entries.

    Each entry and all its aliases become independent patterns so the ruler
    matches any surface form regardless of case (token patterns use
    ``{"LOWER": ...}``).

    Args:
        entries: Vocabulary entries to convert. Defaults to
                 :data:`~vocabulary.DOMAIN_ENTRIES`.

    Returns:
        List of ``{"label": str, "pattern": list[dict]}`` mappings.
    """
    if entries is None:
        entries = DOMAIN_ENTRIES

    patterns: list[dict[str, Any]] = []
    for entry in entries:
        all_forms = [entry.term] + list(entry.aliases)
        seen: set[str] = set()
        for form in all_forms:
            lower = form.lower()
            if lower in seen:
                continue
            seen.add(lower)
            # Single-token pattern with case-insensitive matching
            patterns.append(
                {
                    "label": entry.label,
                    "pattern": [{"LOWER": lower}],
                    "id": entry.term,
                }
            )
    return patterns
