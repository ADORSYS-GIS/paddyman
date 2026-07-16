"""Unit tests for annotation entity extraction."""
from __future__ import annotations

import sys
from pathlib import Path

_POC_ROOT = Path(__file__).resolve().parents[2]
_PARSERS_ROOT = _POC_ROOT / "2_Parsers"
for _path in (str(_POC_ROOT), str(_PARSERS_ROOT)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from java_parser.annotation_entity_builder import (
    annotation_to_entity,
    extract_annotation_entities,
)
from java_parser.java_ast.models import JavaAnnotation


def test_annotation_to_entity_basic():
    """Test basic annotation entity extraction."""
    annotation = JavaAnnotation(
        name="@Data",
        value=None,
        attributes={},
    )
    
    entity = annotation_to_entity(
        annotation=annotation,
        target_type="Class",
        target_name="User",
        file_path="com/example/User.java",
        repository="user-service",
        module="user-service",
        start_line=10,
        document_id="test-doc",
        imports=["lombok.Data"],
    )
    
    assert entity["type"] == "Annotation"
    assert entity["name"] == "@Data"
    assert entity["simple_name"] == "Data"
    assert entity["qualified_name"] == "lombok.Data"
    assert entity["target_type"] == "Class"
    assert entity["target_name"] == "User"
    assert entity["file_path"] == "com/example/User.java"
    assert entity["repository"] == "user-service"
    assert entity["module"] == "user-service"
    assert entity["start_line"] == 10
    assert "uuid" in entity


def test_annotation_to_entity_with_attributes():
    """Test annotation entity extraction with attributes."""
    annotation = JavaAnnotation(
        name="@Column",
        value='name="id", nullable=false',
        attributes={"name": "id", "nullable": "false"},
    )
    
    entity = annotation_to_entity(
        annotation=annotation,
        target_type="Field",
        target_name="id",
        file_path="com/example/User.java",
        repository="user-service",
        module="user-service",
        start_line=15,
        document_id="test-doc",
        imports=["javax.persistence.Column"],
    )
    
    assert entity["type"] == "Annotation"
    assert entity["name"] == "@Column"
    assert entity["qualified_name"] == "javax.persistence.Column"
    assert entity["attributes"]["name"] == "id"
    assert entity["attributes"]["nullable"] == "false"
    assert entity["target_type"] == "Field"


def test_annotation_string_format():
    """Test annotation entity extraction from string."""
    annotation_str = "@Override"
    
    entity = annotation_to_entity(
        annotation=annotation_str,
        target_type="Method",
        target_name="toString",
        file_path="com/example/User.java",
        repository="user-service",
        module="user-service",
        start_line=20,
        document_id="test-doc",
        imports=[],
    )
    
    assert entity["type"] == "Annotation"
    assert entity["name"] == "@Override"
    assert entity["simple_name"] == "Override"
    assert entity["target_type"] == "Method"


def test_extract_annotation_entities_multiple():
    """Test extraction of multiple annotation entities."""
    annotations = [
        JavaAnnotation(name="@NotNull", value=None, attributes={}),
        JavaAnnotation(name="@Size", value="min=1, max=100", attributes={"min": "1", "max": "100"}),
    ]
    
    entities = extract_annotation_entities(
        annotations=annotations,
        target_type="Field",
        target_name="username",
        file_path="com/example/User.java",
        repository="user-service",
        module="user-service",
        start_line=25,
        document_id="test-doc",
        imports=["javax.validation.constraints.NotNull", "javax.validation.constraints.Size"],
    )
    
    assert len(entities) == 2
    assert entities[0]["name"] == "@NotNull"
    assert entities[1]["name"] == "@Size"
    assert entities[1]["attributes"]["min"] == "1"
    assert entities[1]["attributes"]["max"] == "100"


def test_extract_annotation_entities_empty():
    """Test extraction with no annotations."""
    entities = extract_annotation_entities(
        annotations=[],
        target_type="Method",
        target_name="getUser",
        file_path="com/example/UserService.java",
        repository="user-service",
        module="user-service",
        start_line=30,
        document_id="test-doc",
        imports=[],
    )
    
    assert entities == []


def test_annotation_parameter_target():
    """Test annotation entity for parameter target."""
    annotation = JavaAnnotation(
        name="@PathVariable",
        value=None,
        attributes={},
    )
    
    entity = annotation_to_entity(
        annotation=annotation,
        target_type="Parameter",
        target_name="getUser.userId",
        file_path="com/example/UserController.java",
        repository="user-service",
        module="user-service",
        start_line=35,
        document_id="test-doc",
        imports=["org.springframework.web.bind.annotation.PathVariable"],
    )
    
    assert entity["type"] == "Annotation"
    assert entity["target_type"] == "Parameter"
    assert entity["target_name"] == "getUser.userId"
