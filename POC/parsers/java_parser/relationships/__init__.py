"""Java structural relationship extraction sub-package.

Public API for extracting inheritance, implementation, and call relationships
from parsed Java ASTs.
"""
from .extractor import extract_relationships, extract_relationships_from_source
from .models import JavaRelationship, RelationshipType

__all__ = [
    "JavaRelationship",
    "RelationshipType",
    "extract_relationships",
    "extract_relationships_from_source",
]
