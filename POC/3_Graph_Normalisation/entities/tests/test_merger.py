"""Unit tests for canonical entity merging and duplicate detection."""
from __future__ import annotations

import logging

from entities.merger import EntityMerger
from entities.models import EntitySource
from entities.normalizer import NormalizationOutput


def _out(name: str, canonical_type: str = "domain_entity") -> NormalizationOutput:
    return NormalizationOutput(
        canonical_id="PaymentInitiation",
        canonical_type=canonical_type,
        source=EntitySource(
            source_parser="test",
            original_name=name,
            confidence=0.9,
        ),
    )


class TestEntityMerger:
    def test_merges_duplicate_canonical_ids(self) -> None:
        merged = EntityMerger().merge([_out("PaymentController"), _out("POST /payments")])
        assert len(merged) == 1
        assert merged[0].id == "PaymentInitiation"
        assert merged[0].aliases == ["PaymentController", "POST /payments"]
        assert len(merged[0].sources) == 2

    def test_deduplicates_repeated_aliases(self) -> None:
        merged = EntityMerger().merge([_out("PaymentController"), _out("PaymentController")])
        assert merged[0].aliases == ["PaymentController"]
        assert len(merged[0].sources) == 2

    def test_empty_input_returns_empty_list(self) -> None:
        assert EntityMerger().merge([]) == []

    def test_results_sorted_by_canonical_id(self) -> None:
        first = _out("PaymentController")
        second = NormalizationOutput(
            canonical_id="AccountInformation",
            canonical_type="domain_entity",
            source=EntitySource(source_parser="test", original_name="AccountController"),
        )
        merged = EntityMerger().merge([first, second])
        assert [e.id for e in merged] == ["AccountInformation", "PaymentInitiation"]

    def test_conflicting_types_keep_first_and_warn(self, caplog) -> None:  # type: ignore[no-untyped-def]
        caplog.set_level(logging.WARNING)
        merged = EntityMerger().merge(
            [_out("PaymentController", "api_component"), _out("Payment", "domain_entity")]
        )
        assert merged[0].type == "api_component"
        assert "Conflicting types" in caplog.text