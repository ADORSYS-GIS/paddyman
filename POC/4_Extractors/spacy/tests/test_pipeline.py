"""Unit tests for the spaCy extraction pipeline (Chunk 4.1)."""
from __future__ import annotations

import pytest
from spacy.language import Language

from shared.models import Entity, ExtractionResult, ExtractionStatus, SourceMetadata

from pipeline import SpacyExtractionPipeline, build_nlp, registered_names
from vocabulary import VocabularyEntry


class TestBuildNlp:
    """Tests for :func:`build_nlp`."""

    def test_returns_language_instance(self) -> None:
        nlp = build_nlp()
        assert isinstance(nlp, Language)

    def test_entity_ruler_registered(self) -> None:
        nlp = build_nlp()
        assert "domain_entity_ruler" in nlp.pipe_names

    def test_version_tagger_registered(self) -> None:
        nlp = build_nlp()
        assert "version_tagger" in nlp.pipe_names

    def test_order_ruler_before_tagger(self) -> None:
        nlp = build_nlp()
        names = nlp.pipe_names
        assert names.index("domain_entity_ruler") < names.index("version_tagger")

    def test_custom_vocabulary(self) -> None:
        entries = [VocabularyEntry(term="Mandate", label="DOMAIN_ENTITY")]
        nlp = build_nlp(entries=entries)
        doc = nlp("A mandate was issued.")
        assert any(e.label_ == "DOMAIN_ENTITY" for e in doc.ents)


class TestSpacyExtractionPipeline:
    """Tests for :class:`SpacyExtractionPipeline`."""

    @pytest.fixture(autouse=True)
    def pipeline(self, basic_source: SourceMetadata) -> None:
        self.pipeline = SpacyExtractionPipeline.build()
        self.source = basic_source

    def test_build_returns_pipeline(self) -> None:
        assert isinstance(self.pipeline, SpacyExtractionPipeline)

    def test_pipe_names_not_empty(self) -> None:
        assert len(self.pipeline.pipe_names) >= 2

    def test_run_returns_extraction_result(self) -> None:
        result = self.pipeline.run("Payment was approved.", self.source)
        assert isinstance(result, ExtractionResult)

    def test_run_status_success_with_match(self) -> None:
        result = self.pipeline.run("Payment initiated.", self.source)
        assert result.status == ExtractionStatus.SUCCESS

    def test_run_status_partial_no_match(self) -> None:
        result = self.pipeline.run("Nothing relevant here.", self.source)
        assert result.status == ExtractionStatus.PARTIAL

    def test_entities_are_entity_instances(self) -> None:
        result = self.pipeline.run("Account details updated.", self.source)
        for entity in result.entities:
            assert isinstance(entity, Entity)

    def test_entity_type_is_entity(self) -> None:
        result = self.pipeline.run("Consent was granted.", self.source)
        for entity in result.entities:
            assert entity.type == "entity"

    def test_entity_source_matches_source_id(self) -> None:
        result = self.pipeline.run("Transaction recorded.", self.source)
        for entity in result.entities:
            assert entity.source == self.source.source_id

    def test_entity_has_label_property(self) -> None:
        result = self.pipeline.run("Customer registered.", self.source)
        for entity in result.entities:
            assert entity.properties.get("label") == "DOMAIN_ENTITY"

    def test_entity_has_confidence(self) -> None:
        result = self.pipeline.run("Payment processed.", self.source)
        for entity in result.entities:
            assert entity.properties.get("confidence") == 1.0

    def test_entity_has_extraction_rule(self) -> None:
        result = self.pipeline.run("Account opened.", self.source)
        for entity in result.entities:
            assert entity.properties.get("extraction_rule") == "entity_ruler"

    def test_empty_text_returns_no_entities(self) -> None:
        result = self.pipeline.run("", self.source)
        assert result.entities == []

    def test_no_match_returns_no_entities(self) -> None:
        result = self.pipeline.run("The sky is blue.", self.source)
        assert result.entities == []

    def test_multiple_entities(self) -> None:
        result = self.pipeline.run("Payment and Account linked.", self.source)
        names = {e.name.lower() for e in result.entities}
        assert {"payment", "account"}.issubset(names)

    def test_deduplication_same_entity(self) -> None:
        result = self.pipeline.run("Payment payment payment", self.source)
        names = [e.name.lower() for e in result.entities]
        assert names.count("payment") == 1


class TestVersionTagInjection:
    """Tests for version-tag metadata propagation through the full pipeline."""

    @pytest.fixture(autouse=True)
    def pipeline(self) -> None:
        self.pipeline = SpacyExtractionPipeline.build()

    def test_version_from_explicit_metadata(
        self, versioned_source: SourceMetadata
    ) -> None:
        result = self.pipeline.run("Payment approved.", versioned_source)
        for entity in result.entities:
            assert entity.properties.get("version") == "v2"

    def test_version_from_file_path(
        self, path_versioned_source: SourceMetadata
    ) -> None:
        result = self.pipeline.run("Account created.", path_versioned_source)
        for entity in result.entities:
            version = entity.properties.get("version")
            assert version is not None
            assert version.startswith("v")

    def test_no_version_when_unavailable(
        self, basic_source: SourceMetadata
    ) -> None:
        result = self.pipeline.run("Consent submitted.", basic_source)
        for entity in result.entities:
            assert entity.properties.get("version") is None

    def test_metadata_preserved_in_entity(
        self, versioned_source: SourceMetadata
    ) -> None:
        result = self.pipeline.run("Transaction logged.", versioned_source)
        for entity in result.entities:
            assert entity.properties.get("repository") == "aspsp-xs2a"
            assert entity.properties.get("module") == "consent"
            assert entity.properties.get("file_path") is not None

    def test_extra_metadata_merged(
        self, basic_source: SourceMetadata
    ) -> None:
        result = self.pipeline.run(
            "Customer notified.",
            basic_source,
            extra_metadata={"version": "5"},
        )
        for entity in result.entities:
            assert entity.properties.get("version") == "v5"
