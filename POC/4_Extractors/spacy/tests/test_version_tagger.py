"""Unit tests for the version-tag injection component."""
from __future__ import annotations

import pytest
import spacy
from spacy.language import Language

from pipeline.version_tagger import (
    VersionTaggerComponent,
    derive_version_tag,
    derive_version_with_source,
)
from matcher import add_entity_matcher


@pytest.fixture()
def armed_nlp() -> Language:
    """Pipeline with entity ruler, content extractor, and version tagger."""
    from pipeline.pipeline import build_nlp
    return build_nlp()


class TestDeriveVersionTag:
    """Tests for :func:`derive_version_tag`."""

    def test_explicit_version_field(self) -> None:
        assert derive_version_tag({"version": "1"}) == "v1"

    def test_explicit_version_with_prefix(self) -> None:
        assert derive_version_tag({"version": "v2.1"}) == "v2.1"

    def test_api_version_field(self) -> None:
        assert derive_version_tag({"api_version": "3"}) == "v3"

    def test_file_path_v_pattern(self) -> None:
        tag = derive_version_tag({"file_path": "/repo/v1/spec.yaml"})
        assert tag == "v1"

    def test_file_path_underscore_pattern(self) -> None:
        tag = derive_version_tag({"file_path": "/specs/nextgenpsd2_1_3/api.yaml"})
        assert tag == "v1.3"

    def test_module_pattern(self) -> None:
        tag = derive_version_tag({"module": "ais_service_1_0"})
        assert tag == "v1.0"

    def test_repository_v_pattern(self) -> None:
        tag = derive_version_tag({"repository": "aspsp-xs2a-v2"})
        assert tag == "v2"

    def test_explicit_takes_priority_over_path(self) -> None:
        tag = derive_version_tag(
            {"version": "9", "file_path": "/repo/v1/spec.yaml"}
        )
        assert tag == "v9"

    def test_no_version_returns_none(self) -> None:
        assert derive_version_tag({}) is None

    def test_no_version_in_plain_path(self) -> None:
        assert derive_version_tag({"file_path": "/docs/spec.md"}) is None

    def test_empty_version_field_falls_through(self) -> None:
        tag = derive_version_tag({"version": "", "file_path": "/repo/v3/spec.yaml"})
        assert tag == "v3"

    def test_deterministic_same_input(self) -> None:
        meta = {"file_path": "/repo/v2/api.yaml"}
        assert derive_version_tag(meta) == derive_version_tag(meta)


class TestVersionTaggerComponent:
    """Tests for the spaCy version tagger pipeline component."""

    def test_version_tags_populated(self, armed_nlp: Language) -> None:
        doc = armed_nlp.make_doc("Payment consent was approved.")
        doc.user_data["source_metadata"] = {"version": "2"}
        doc = armed_nlp(doc)
        assert "version_tags" in doc.user_data
        assert len(doc.user_data["version_tags"]) > 0

    def test_version_tag_value(self, armed_nlp: Language) -> None:
        doc = armed_nlp.make_doc("Payment initiated.")
        doc.user_data["source_metadata"] = {"version": "1"}
        doc = armed_nlp(doc)
        tags = doc.user_data["version_tags"]
        assert all(v == "v1" for v in tags.values())

    def test_no_entities_no_tags(self, armed_nlp: Language) -> None:
        doc = armed_nlp.make_doc("Nothing relevant here.")
        doc.user_data["source_metadata"] = {"version": "1"}
        doc = armed_nlp(doc)
        assert doc.user_data.get("version_tags", {}) == {}

    def test_no_metadata_tag_is_none(self, armed_nlp: Language) -> None:
        doc = armed_nlp.make_doc("Account is active.")
        doc.user_data["source_metadata"] = {}
        doc = armed_nlp(doc)
        tags = doc.user_data.get("version_tags", {})
        assert all(v is None for v in tags.values())

    def test_missing_source_metadata_key(self, armed_nlp: Language) -> None:
        """Pipeline must not raise when source_metadata is absent."""
        doc = armed_nlp.make_doc("Transaction recorded.")
        # No 'source_metadata' key set at all.
        doc = armed_nlp(doc)
        assert "version_tags" in doc.user_data
