"""Unit tests for shared.models.source."""
from __future__ import annotations

import dataclasses
from datetime import datetime
from uuid import UUID

import pytest

from shared.models.source import SourceMetadata, SourceType


def _make_source(**kwargs) -> SourceMetadata:
    defaults = dict(
        source_id="spec_v1.pdf",
        source_type=SourceType.DOCUMENT,
        location="/data/spec_v1.pdf",
    )
    defaults.update(kwargs)
    return SourceMetadata(**defaults)


class TestSourceMetadataCreation:
    def test_minimal_required_fields(self) -> None:
        sm = _make_source()
        assert sm.source_id == "spec_v1.pdf"
        assert sm.source_type == SourceType.DOCUMENT
        assert sm.location == "/data/spec_v1.pdf"
        assert isinstance(sm.id, UUID)
        assert isinstance(sm.ingested_at, datetime)
        assert sm.metadata == {}

    def test_all_source_types_accepted(self) -> None:
        for st in SourceType:
            sm = _make_source(source_type=st)
            assert sm.source_type == st

    def test_source_type_coerced_from_string(self) -> None:
        sm = _make_source(source_type="api")
        assert sm.source_type == SourceType.API

    def test_metadata_stored(self) -> None:
        sm = _make_source(metadata={"author": "Berlin Group"})
        assert sm.metadata["author"] == "Berlin Group"

    def test_ingested_at_is_utc_aware(self) -> None:
        sm = _make_source()
        assert sm.ingested_at.tzinfo is not None


class TestSourceMetadataValidation:
    def test_empty_source_id_raises(self) -> None:
        with pytest.raises(ValueError, match="source_id"):
            _make_source(source_id="")

    def test_whitespace_source_id_raises(self) -> None:
        with pytest.raises(ValueError, match="source_id"):
            _make_source(source_id="   ")

    def test_empty_location_raises(self) -> None:
        with pytest.raises(ValueError, match="location"):
            _make_source(location="")

    def test_invalid_source_type_string_raises(self) -> None:
        with pytest.raises(ValueError):
            _make_source(source_type="unknown_type")


class TestSourceMetadataSerialization:
    def test_asdict_produces_expected_keys(self) -> None:
        sm = _make_source()
        d = dataclasses.asdict(sm)
        assert set(d.keys()) == {
            "id", "source_id", "source_type", "location", "ingested_at", "metadata"
        }
