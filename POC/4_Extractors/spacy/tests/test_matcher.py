"""Unit tests for the EntityRuler-based domain entity matcher."""
from __future__ import annotations

import pytest
import spacy
from spacy.language import Language

from matcher import add_entity_matcher
from vocabulary import VocabularyEntry


@pytest.fixture()
def blank_nlp() -> Language:
    return spacy.blank("en")


class TestAddEntityMatcher:
    """Tests for :func:`add_entity_matcher`."""

    def test_returns_language_instance(self, blank_nlp: Language) -> None:
        result = add_entity_matcher(blank_nlp)
        assert isinstance(result, Language)

    def test_ruler_is_in_pipe_names(self, blank_nlp: Language) -> None:
        add_entity_matcher(blank_nlp)
        assert "domain_entity_ruler" in blank_nlp.pipe_names

    def test_cannot_add_twice(self, blank_nlp: Language) -> None:
        add_entity_matcher(blank_nlp)
        with pytest.raises(ValueError):
            add_entity_matcher(blank_nlp)

    def test_custom_vocabulary(self, blank_nlp: Language) -> None:
        entries = [VocabularyEntry(term="Loan", label="DOMAIN_ENTITY")]
        add_entity_matcher(blank_nlp, entries=entries)
        doc = blank_nlp("Request a loan.")
        assert any(e.label_ == "DOMAIN_ENTITY" for e in doc.ents)


class TestEntityMatching:
    """Tests for domain entity recognition in text."""

    @pytest.fixture(autouse=True)
    def setup(self, blank_nlp: Language) -> None:
        add_entity_matcher(blank_nlp)
        self.nlp = blank_nlp

    def _match_texts(self, text: str) -> list[str]:
        return [ent.text.lower() for ent in self.nlp(text).ents]

    def test_matches_payment(self) -> None:
        assert "payment" in self._match_texts("The payment was processed.")

    def test_matches_account(self) -> None:
        assert "account" in self._match_texts("Open an account today.")

    def test_matches_consent(self) -> None:
        assert "consent" in self._match_texts("Consent was granted.")

    def test_matches_customer(self) -> None:
        assert "customer" in self._match_texts("The customer submitted a request.")

    def test_matches_transaction(self) -> None:
        assert "transaction" in self._match_texts("A transaction occurred.")

    def test_case_insensitive_upper(self) -> None:
        assert "PAYMENT" in [e.text for e in self.nlp("PAYMENT approved.").ents]

    def test_multiple_entities_in_one_text(self) -> None:
        doc = self.nlp("Payment and Account details are linked.")
        labels = {e.label_ for e in doc.ents}
        assert "DOMAIN_ENTITY" in labels
        texts = {e.text.lower() for e in doc.ents}
        assert {"payment", "account"}.issubset(texts)

    def test_no_match_on_unrelated_text(self) -> None:
        doc = self.nlp("The weather is sunny today.")
        assert len(doc.ents) == 0

    def test_empty_text(self) -> None:
        doc = self.nlp("")
        assert len(doc.ents) == 0

    def test_entity_label_is_domain_entity(self) -> None:
        doc = self.nlp("Transaction initiated.")
        for ent in doc.ents:
            assert ent.label_ == "DOMAIN_ENTITY"
