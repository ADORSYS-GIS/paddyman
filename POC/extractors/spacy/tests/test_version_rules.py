"""Unit tests for version rules and the content-based version extractor (Chunk 4.2)."""
from __future__ import annotations

import pytest
import spacy
from spacy.language import Language

from shared.models import SourceMetadata

from ..pipeline.version_tagger import derive_version_with_source
from ..version.rules import CONTENT_RULES, VersionRule
from ..version.content_extractor import ContentVersionExtractorComponent
from ..matcher import add_entity_matcher

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _armed_nlp() -> Language:
    """Build a minimal pipeline: entity ruler + content extractor + version tagger."""
    from pipeline.pipeline import build_nlp
    return build_nlp()


# ---------------------------------------------------------------------------
# VersionRule.extract
# ---------------------------------------------------------------------------

class TestVersionRuleExtract:
    """Tests for individual :meth:`VersionRule.extract` calls."""

    def _rule(self, name: str) -> VersionRule:
        return next(r for r in CONTENT_RULES if r.name == name)

    def test_psd2_semantic_version(self) -> None:
        assert self._rule("psd2").extract("PSD2 v1.3.16") == "v1.3.16"

    def test_psd2_without_prefix(self) -> None:
        assert self._rule("psd2").extract("PSD2 1.3") == "v1.3"

    def test_psd2_case_insensitive(self) -> None:
        assert self._rule("psd2").extract("psd2 1.3") == "v1.3"

    def test_berlin_group_with_prefix(self) -> None:
        assert self._rule("berlin_group").extract("Berlin Group V2") == "v2"

    def test_berlin_group_semantic(self) -> None:
        assert self._rule("berlin_group").extract("Berlin Group 1.3.2") == "v1.3.2"

    def test_berlin_group_case_insensitive(self) -> None:
        assert self._rule("berlin_group").extract("BERLIN GROUP 3") == "v3"

    def test_nextgenpsd2_version(self) -> None:
        assert self._rule("nextgenpsd2").extract("NextGenPSD2 1.3") == "v1.3"

    def test_openapi_colon_format(self) -> None:
        assert self._rule("openapi").extract("openapi: 3.0.1") == "v3.0.1"

    def test_openapi_space_format(self) -> None:
        assert self._rule("openapi").extract("OpenAPI 3.0") == "v3.0"

    def test_version_prefix_semantic(self) -> None:
        assert self._rule("version_prefix_semantic").extract("v1.3.16") == "v1.3.16"

    def test_version_prefix_major(self) -> None:
        assert self._rule("version_prefix_major").extract("V2") == "v2"

    def test_semantic_version_bare(self) -> None:
        assert self._rule("semantic_version").extract("API version 3.0.1") == "v3.0.1"

    def test_no_match_returns_none(self) -> None:
        assert self._rule("psd2").extract("no version here") is None

    def test_empty_string_returns_none(self) -> None:
        for rule in CONTENT_RULES:
            assert rule.extract("") is None


# ---------------------------------------------------------------------------
# ContentVersionExtractorComponent
# ---------------------------------------------------------------------------

class TestContentVersionExtractorComponent:
    """Tests for the spaCy content-version-extractor component."""

    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.extractor = ContentVersionExtractorComponent()

    def _run(self, text: str) -> dict | None:
        nlp = spacy.blank("en")
        doc = nlp(text)
        self.extractor(doc)
        return doc.user_data.get("content_version")

    def test_psd2_detected(self) -> None:
        result = self._run("Implements PSD2 v1.3.16 requirements.")
        assert result is not None
        assert result["version"] == "v1.3.16"
        assert result["rule"] == "psd2"

    def test_berlin_group_detected(self) -> None:
        result = self._run("Based on Berlin Group V2 specification.")
        assert result is not None
        assert result["rule"] == "berlin_group"

    def test_openapi_detected(self) -> None:
        result = self._run("openapi: 3.0.1")
        assert result is not None
        assert result["version"] == "v3.0.1"
        assert result["rule"] == "openapi"

    def test_nextgenpsd2_detected(self) -> None:
        result = self._run("NextGenPSD2 1.3 compliant.")
        assert result is not None
        assert result["rule"] == "nextgenpsd2"

    def test_generic_version_prefix(self) -> None:
        result = self._run("Release V2 is available.")
        assert result is not None
        assert result["version"] == "v2"

    def test_psd2_takes_priority_over_generic(self) -> None:
        result = self._run("PSD2 1.3.16, v2")
        assert result is not None
        assert result["rule"] == "psd2"

    def test_no_version_in_text(self) -> None:
        result = self._run("Payment consent was approved.")
        assert result is None

    def test_empty_text(self) -> None:
        assert self._run("") is None

    def test_custom_rules(self) -> None:
        import re
        custom = [VersionRule("custom", re.compile(r"REL-(\d+)"))]
        extractor = ContentVersionExtractorComponent(rules=custom)
        nlp = spacy.blank("en")
        doc = nlp("Deployed REL-42 today.")
        extractor(doc)
        result = doc.user_data.get("content_version")
        assert result is not None
        assert result["version"] == "v42"
        assert result["rule"] == "custom"


# ---------------------------------------------------------------------------
# derive_version_with_source — priority chain
# ---------------------------------------------------------------------------

class TestDeriveVersionWithSource:
    """Tests for the 3-priority version resolution in :func:`derive_version_with_source`."""

    def test_priority_1_explicit_version(self) -> None:
        v, src = derive_version_with_source({"version": "3"})
        assert v == "v3"
        assert src == "metadata"

    def test_priority_1_api_version(self) -> None:
        v, src = derive_version_with_source({"api_version": "1.2"})
        assert v == "v1.2"
        assert src == "metadata"

    def test_priority_2_file_path(self) -> None:
        v, src = derive_version_with_source({"file_path": "/repo/v1/spec.yaml"})
        assert v == "v1"
        assert src == "source_path"

    def test_priority_2_module(self) -> None:
        v, src = derive_version_with_source({"module": "service_1_3"})
        assert v == "v1.3"
        assert src == "source_path"

    def test_priority_3_content_fallback(self) -> None:
        content = {"version": "v1.3.16", "rule": "psd2"}
        v, src = derive_version_with_source({}, content)
        assert v == "v1.3.16"
        assert src == "content:psd2"

    def test_priority_1_beats_content(self) -> None:
        content = {"version": "v9.9", "rule": "psd2"}
        v, src = derive_version_with_source({"version": "1"}, content)
        assert v == "v1"
        assert src == "metadata"

    def test_priority_2_beats_content(self) -> None:
        content = {"version": "v9.9", "rule": "semantic_version"}
        v, src = derive_version_with_source(
            {"file_path": "/repo/v3/api.yaml"}, content
        )
        assert v == "v3"
        assert src == "source_path"

    def test_no_version_anywhere(self) -> None:
        v, src = derive_version_with_source({})
        assert v is None
        assert src is None

    def test_empty_explicit_version_falls_through(self) -> None:
        content = {"version": "v2", "rule": "berlin_group"}
        v, src = derive_version_with_source({"version": ""}, content)
        assert v == "v2"
        assert src == "content:berlin_group"

    def test_deterministic(self) -> None:
        meta = {"file_path": "/repo/v2/spec.yaml"}
        assert derive_version_with_source(meta) == derive_version_with_source(meta)


# ---------------------------------------------------------------------------
# Full pipeline: version_source and source_parser in entity properties
# ---------------------------------------------------------------------------

class TestPipelineVersionTagging:
    """Tests verifying version metadata flows through the full pipeline."""

    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        from pipeline.pipeline import SpacyExtractionPipeline
        self.pipeline = SpacyExtractionPipeline.build()

    def test_version_source_metadata_in_entity(
        self, versioned_source: SourceMetadata
    ) -> None:
        result = self.pipeline.run("Payment approved.", versioned_source)
        for entity in result.entities:
            assert entity.properties["version"] == "v2"
            assert entity.properties["version_source"] == "metadata"

    def test_version_source_path_in_entity(
        self, path_versioned_source: SourceMetadata
    ) -> None:
        result = self.pipeline.run("Account created.", path_versioned_source)
        for entity in result.entities:
            assert entity.properties["version_source"] == "source_path"

    def test_version_source_content_in_entity(
        self, no_meta_source: SourceMetadata
    ) -> None:
        result = self.pipeline.run(
            "PSD2 1.3.16 — Payment consent recorded.",
            no_meta_source,
        )
        for entity in result.entities:
            assert entity.properties["version"] == "v1.3.16"
            assert entity.properties["version_source"].startswith("content:")

    def test_source_parser_java(self, basic_source: SourceMetadata) -> None:
        result = self.pipeline.run(
            "Account opened.", basic_source, source_parser="java_parser"
        )
        for entity in result.entities:
            assert entity.properties["source_parser"] == "java_parser"

    def test_source_parser_openapi(self, basic_source: SourceMetadata) -> None:
        result = self.pipeline.run(
            "Payment initiated.", basic_source, source_parser="openapi_parser"
        )
        for entity in result.entities:
            assert entity.properties["source_parser"] == "openapi_parser"

    def test_source_parser_markdown(self, basic_source: SourceMetadata) -> None:
        result = self.pipeline.run(
            "Consent submitted.", basic_source, source_parser="markdown_parser"
        )
        for entity in result.entities:
            assert entity.properties["source_parser"] == "markdown_parser"

    def test_no_version_no_source(self, basic_source: SourceMetadata) -> None:
        result = self.pipeline.run("Transaction logged.", basic_source)
        for entity in result.entities:
            assert entity.properties["version"] is None
            assert entity.properties["version_source"] is None

    def test_content_version_extractor_in_pipe(self) -> None:
        assert "content_version_extractor" in self.pipeline.pipe_names

    def test_version_tagger_after_content_extractor(self) -> None:
        names = self.pipeline.pipe_names
        ce_idx = names.index("content_version_extractor")
        vt_idx = names.index("version_tagger")
        assert ce_idx < vt_idx

    def test_berlin_group_from_content(
        self, no_meta_source: SourceMetadata
    ) -> None:
        result = self.pipeline.run(
            "Berlin Group V2 — Account service specification.",
            no_meta_source,
        )
        for entity in result.entities:
            assert entity.properties["version"] == "v2"
            assert "berlin_group" in entity.properties["version_source"]
