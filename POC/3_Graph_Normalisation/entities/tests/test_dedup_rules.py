"""Unit tests for canonical entity deduplication rules."""
from __future__ import annotations

from entities.dedup_rules import (
    DomainMappingRule,
    EmbeddingSimilarityRule,
    ExactAliasRule,
    NameSimilarityRule,
)
from entities.models import CanonicalEntity


def _entity(
    entity_id: str,
    aliases: list[str] | None = None,
    embedding: list[float] | None = None,
) -> CanonicalEntity:
    properties = {"embedding": embedding} if embedding is not None else {}
    return CanonicalEntity(
        id=entity_id,
        type="domain_entity",
        aliases=aliases or [],
        properties=properties,
    )


class TestExactAliasRule:
    def test_exact_alias_match(self) -> None:
        left = _entity("PaymentRequest", ["PaymentDTO"])
        right = _entity("PaymentDto")
        match = ExactAliasRule().match(left, right)
        assert match is not None
        assert match.score == 1.0
        assert match.reason == "exact_alias"

    def test_no_exact_alias_match(self) -> None:
        assert ExactAliasRule().match(_entity("Payment"), _entity("Account")) is None


class TestNameSimilarityRule:
    def test_similar_normalized_names_match(self) -> None:
        match = NameSimilarityRule(threshold=0.82).match(
            _entity("PaymentRequest"),
            _entity("PaymentRequests"),
        )
        assert match is not None
        assert match.reason == "name_similarity"

    def test_different_names_do_not_match(self) -> None:
        match = NameSimilarityRule(threshold=0.9).match(
            _entity("PaymentRequest"),
            _entity("AccountInformation"),
        )
        assert match is None


class TestEmbeddingSimilarityRule:
    def test_embedding_similarity_match(self) -> None:
        match = EmbeddingSimilarityRule(threshold=0.95).match(
            _entity("PaymentDto", embedding=[1.0, 0.0, 0.0]),
            _entity("PaymentRequest", embedding=[0.99, 0.01, 0.0]),
        )
        assert match is not None
        assert match.reason == "embedding_similarity"

    def test_missing_embeddings_do_not_match(self) -> None:
        match = EmbeddingSimilarityRule().match(_entity("PaymentDto"), _entity("PaymentRequest"))
        assert match is None

    def test_mismatched_embedding_dimensions_do_not_match(self) -> None:
        match = EmbeddingSimilarityRule().match(
            _entity("PaymentDto", embedding=[1.0, 0.0]),
            _entity("PaymentRequest", embedding=[1.0, 0.0, 0.0]),
        )
        assert match is None


class TestDomainMappingRule:
    def test_domain_mapping_matches_request_equivalents(self) -> None:
        match = DomainMappingRule().match(
            _entity("PaymentDTO"),
            _entity("PaymentInitiationRequest"),
        )
        assert match is not None
        assert match.reason == "domain_mapping"

    def test_custom_domain_mapping_is_supported(self) -> None:
        rule = DomainMappingRule({"FooCanonical": ["FooLegacy", "FooRequest"]})
        assert rule.match(_entity("FooLegacy"), _entity("FooRequest")) is not None