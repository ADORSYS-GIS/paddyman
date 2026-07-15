"""Unit tests for annotation relationship building."""
from __future__ import annotations

import sys
from pathlib import Path

_POC_ROOT = Path(__file__).resolve().parents[2]
_PARSERS_ROOT = _POC_ROOT / "2_Parsers"
for _path in (str(_POC_ROOT), str(_PARSERS_ROOT)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from java_parser.annotation_relationship_builder import (
    build_annotation_type_relationships,
    build_has_annotation_relationships,
)


def test_build_has_annotation_relationships():
    """Test HAS_ANNOTATION relationship creation."""
    source_entity = {
        "type": "Class",
        "name": "User",
        "uuid": "class-uuid-123",
    }
    
    annotation_entities = [
        {
            "type": "Annotation",
            "name": "@Data",
            "uuid": "ann-uuid-456",
            "target_type": "Class",
        },
        {
            "type": "Annotation",
            "name": "@Entity",
            "uuid": "ann-uuid-789",
            "target_type": "Class",
        },
    ]
    
    relationships = build_has_annotation_relationships(source_entity, annotation_entities)
    
    assert len(relationships) == 2
    assert relationships[0]["type"] == "HAS_ANNOTATION"
    assert relationships[0]["source"] == "class-uuid-123"
    assert relationships[0]["target"] == "ann-uuid-456"
    assert relationships[0]["properties"]["target_type"] == "Class"
    assert relationships[1]["target"] == "ann-uuid-789"


def test_build_has_annotation_relationships_empty():
    """Test HAS_ANNOTATION with no annotations."""
    source_entity = {
        "type": "Method",
        "name": "getUser",
        "uuid": "method-uuid-123",
    }
    
    relationships = build_has_annotation_relationships(source_entity, [])
    
    assert relationships == []


def test_build_annotation_type_relationships():
    """Test ANNOTATION_TYPE relationship creation."""
    annotation_entities = [
        {
            "type": "Annotation",
            "name": "@MyCustomAnnotation",
            "qualified_name": "com.example.annotations.MyCustomAnnotation",
            "uuid": "ann-uuid-123",
        },
        {
            "type": "Annotation",
            "name": "@AnotherAnnotation",
            "qualified_name": "com.example.annotations.AnotherAnnotation",
            "uuid": "ann-uuid-456",
        },
        {
            "type": "Annotation",
            "name": "@Override",
            "qualified_name": "java.lang.Override",
            "uuid": "ann-uuid-789",
        },
    ]
    
    type_entities = [
        {
            "type": "Interface",
            "name": "MyCustomAnnotation",
            "qualified_name": "com.example.annotations.MyCustomAnnotation",
            "uuid": "type-uuid-111",
        },
        {
            "type": "Interface",
            "name": "AnotherAnnotation",
            "qualified_name": "com.example.annotations.AnotherAnnotation",
            "uuid": "type-uuid-222",
        },
    ]
    
    relationships = build_annotation_type_relationships(annotation_entities, type_entities)
    
    # Should create relationships for the two custom annotations found in codebase
    assert len(relationships) == 2
    assert relationships[0]["type"] == "ANNOTATION_TYPE"
    assert relationships[0]["source"] == "ann-uuid-123"
    assert relationships[0]["target"] == "type-uuid-111"
    assert relationships[1]["source"] == "ann-uuid-456"
    assert relationships[1]["target"] == "type-uuid-222"
    # @Override is from java.lang, not in codebase, so no relationship


def test_build_annotation_type_relationships_no_matches():
    """Test ANNOTATION_TYPE with no matching declarations."""
    annotation_entities = [
        {
            "type": "Annotation",
            "name": "@Override",
            "qualified_name": "java.lang.Override",
            "uuid": "ann-uuid-123",
        },
    ]
    
    type_entities = [
        {
            "type": "Class",
            "name": "User",
            "qualified_name": "com.example.User",
            "uuid": "type-uuid-111",
        },
    ]
    
    relationships = build_annotation_type_relationships(annotation_entities, type_entities)
    
    assert relationships == []


def test_build_annotation_type_relationships_empty():
    """Test ANNOTATION_TYPE with empty inputs."""
    relationships = build_annotation_type_relationships([], [])
    assert relationships == []
    
    annotation_entities = [
        {"type": "Annotation", "qualified_name": "com.example.Test", "uuid": "ann-123"},
    ]
    relationships = build_annotation_type_relationships(annotation_entities, [])
    assert relationships == []
    
    type_entities = [
        {"type": "Class", "qualified_name": "com.example.Test", "uuid": "type-123"},
    ]
    relationships = build_annotation_type_relationships([], type_entities)
    assert relationships == []
