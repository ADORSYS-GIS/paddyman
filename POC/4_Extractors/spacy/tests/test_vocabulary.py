"""Unit tests for the domain vocabulary and pattern builders."""
from __future__ import annotations

import pytest

from vocabulary import (
    DOMAIN_ENTRIES,
    VocabularyEntry,
    build_entity_ruler_patterns,
)


class TestVocabularyEntries:
    """Tests for the built-in DOMAIN_ENTRIES list."""

    def test_five_initial_entries(self) -> None:
        """Exactly five domain entries are defined."""
        assert len(DOMAIN_ENTRIES) == 5

    def test_required_terms_present(self) -> None:
        terms = {e.term for e in DOMAIN_ENTRIES}
        assert {"Payment", "Account", "Consent", "Customer", "Transaction"} == terms

    def test_all_labels_are_domain_entity(self) -> None:
        for entry in DOMAIN_ENTRIES:
            assert entry.label == "DOMAIN_ENTITY", f"{entry.term} has wrong label"

    def test_entries_are_immutable(self) -> None:
        entry = DOMAIN_ENTRIES[0]
        with pytest.raises((AttributeError, TypeError)):
            entry.term = "Modified"  # type: ignore[misc]

    def test_each_entry_has_aliases(self) -> None:
        for entry in DOMAIN_ENTRIES:
            assert len(entry.aliases) > 0, f"{entry.term} has no aliases"


class TestBuildEntityRulerPatterns:
    """Tests for :func:`build_entity_ruler_patterns`."""

    def test_returns_list(self) -> None:
        patterns = build_entity_ruler_patterns()
        assert isinstance(patterns, list)

    def test_all_patterns_have_label_and_pattern(self) -> None:
        for p in build_entity_ruler_patterns():
            assert "label" in p
            assert "pattern" in p

    def test_label_is_domain_entity(self) -> None:
        for p in build_entity_ruler_patterns():
            assert p["label"] == "DOMAIN_ENTITY"

    def test_no_duplicate_lower_forms(self) -> None:
        patterns = build_entity_ruler_patterns()
        lowers = [p["pattern"][0]["LOWER"] for p in patterns]
        assert len(lowers) == len(set(lowers))

    def test_custom_entry(self) -> None:
        entries = [VocabularyEntry(term="Loan", label="DOMAIN_ENTITY")]
        patterns = build_entity_ruler_patterns(entries)
        lowers = [p["pattern"][0]["LOWER"] for p in patterns]
        assert "loan" in lowers

    def test_empty_entries_returns_empty_list(self) -> None:
        assert build_entity_ruler_patterns([]) == []
