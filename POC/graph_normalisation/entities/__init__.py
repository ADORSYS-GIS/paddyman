"""Canonical Entity layer — Graph Normalisation Chunk 5.1."""
from .deduplicator import EntityDeduplicator, deduplicate_entities
from .models import CanonicalEntity, EntitySource
from .pipeline import normalise_entities

__all__ = [
    "CanonicalEntity",
    "EntitySource",
    "EntityDeduplicator",
    "deduplicate_entities",
    "normalise_entities",
]
