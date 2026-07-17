"""Deterministic rules for matching equivalent canonical entities."""
from __future__ import annotations

import math
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Protocol

from .models import CanonicalEntity
from .rules.casing import to_pascal_case


@dataclass(frozen=True)
class DeduplicationMatch:
    score: float
    reason: str


class DeduplicationRule(Protocol):
    """Protocol for configurable deduplication rules."""

    def match(self, left: CanonicalEntity, right: CanonicalEntity) -> DeduplicationMatch | None:
        """Return a match when *left* and *right* are equivalent."""
        ...


def entity_names(entity: CanonicalEntity) -> list[str]:
    """Return deterministic unique names to compare for *entity*."""
    names = [entity.id, *entity.aliases]
    seen: set[str] = set()
    result: list[str] = []
    for name in names:
        key = _normalise_name(name)
        if key and key not in seen:
            seen.add(key)
            result.append(name)
    return result


def _normalise_name(name: str) -> str:
    """Normalise names for matching without changing entity IDs."""
    return to_pascal_case(name).lower()


def _embedding(entity: CanonicalEntity) -> list[float] | None:
    """Return an existing embedding vector from entity properties, if present."""
    for key in ("embedding", "embeddings", "embedding_vector", "vector"):
        value = entity.properties.get(key)
        if isinstance(value, list) and value:
            try:
                return [float(v) for v in value]
            except (TypeError, ValueError):
                return None
    return None


def _cosine(left: list[float], right: list[float]) -> float:
    """Return cosine similarity for two same-length vectors."""
    if len(left) != len(right) or not left:
        return 0.0
    dot = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    if left_norm <= 1e-12 or right_norm <= 1e-12:
        return 0.0
    return dot / (left_norm * right_norm)


class ExactAliasRule:
    """Match entities with an exact normalised alias or ID overlap."""

    def match(self, left: CanonicalEntity, right: CanonicalEntity) -> DeduplicationMatch | None:
        left_names = {_normalise_name(n) for n in entity_names(left)}
        right_names = {_normalise_name(n) for n in entity_names(right)}
        return DeduplicationMatch(1.0, "exact_alias") if left_names & right_names else None


class NameSimilarityRule:
    """Match entities whose normalised names are highly similar."""

    def __init__(self, threshold: float = 0.88) -> None:
        self.threshold = threshold

    def match(self, left: CanonicalEntity, right: CanonicalEntity) -> DeduplicationMatch | None:
        best = 0.0
        for left_name in entity_names(left):
            for right_name in entity_names(right):
                score = SequenceMatcher(
                    None, _normalise_name(left_name), _normalise_name(right_name)
                ).ratio()
                best = max(best, score)
        if best >= self.threshold:
            return DeduplicationMatch(round(best, 4), "name_similarity")
        return None


class EmbeddingSimilarityRule:
    """Match entities using existing embedding vectors only."""

    def __init__(self, threshold: float = 0.92) -> None:
        self.threshold = threshold

    def match(self, left: CanonicalEntity, right: CanonicalEntity) -> DeduplicationMatch | None:
        left_embedding = _embedding(left)
        right_embedding = _embedding(right)
        if left_embedding is None or right_embedding is None:
            return None
        score = _cosine(left_embedding, right_embedding)
        if score >= self.threshold:
            return DeduplicationMatch(round(score, 4), "embedding_similarity")
        return None


class DomainMappingRule:
    """Match entities using configurable domain-specific equivalence groups."""

    def __init__(self, groups: dict[str, list[str]] | None = None) -> None:
        self._lookup = _build_domain_lookup(groups or DEFAULT_DOMAIN_MAPPINGS)

    def match(self, left: CanonicalEntity, right: CanonicalEntity) -> DeduplicationMatch | None:
        left_targets = {self._lookup.get(_normalise_name(n)) for n in entity_names(left)}
        right_targets = {self._lookup.get(_normalise_name(n)) for n in entity_names(right)}
        left_targets.discard(None)
        right_targets.discard(None)
        return DeduplicationMatch(0.96, "domain_mapping") if left_targets & right_targets else None


DEFAULT_DOMAIN_MAPPINGS: dict[str, list[str]] = {
    "PaymentRequest": ["PaymentDTO", "PaymentRequest", "Payment Initiation Request"],
    "AccountRequest": ["AccountDTO", "AccountRequest", "Account Information Request"],
    "ConsentRequest": ["ConsentDTO", "ConsentRequest", "Consent Management Request"],
}

def _build_domain_lookup(groups: dict[str, list[str]]) -> dict[str, str]:
    """Build alias-to-canonical lookup from domain-specific groups."""
    lookup: dict[str, str] = {}
    for canonical, aliases in groups.items():
        key = _normalise_name(canonical)
        lookup[key] = key
        for alias in aliases:
            lookup[_normalise_name(alias)] = key
    return lookup


def default_deduplication_rules() -> list[DeduplicationRule]:
    """Return the default deterministic deduplication rule set."""
    return [
        ExactAliasRule(), DomainMappingRule(), NameSimilarityRule(), EmbeddingSimilarityRule(),
    ]