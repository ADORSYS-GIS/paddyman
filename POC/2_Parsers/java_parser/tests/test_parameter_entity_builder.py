"""Tests for parameter_entity_builder: parameter entity extraction."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

_PARSERS_ROOT = Path(__file__).resolve().parent.parent.parent
_POC_ROOT = _PARSERS_ROOT.parent
for _p in (str(_POC_ROOT), str(_PARSERS_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from java_parser.members.models import JavaParameter
from java_parser.parameter_entity_builder import (
    extract_parameter_entities,
    parameter_to_entity,
)


class TestParameterToEntity:
    """Tests for parameter_to_entity function."""

    def test_basic_parameter_entity(self) -> None:
        """Verify basic parameter entity structure."""
        param = JavaParameter("count", "int", position=0)
        entity = parameter_to_entity(
            param,
            "myMethod",
            "com.example.MyClass.myMethod",
            "com/example/MyClass.java",
            "my-repo",
            "my-module",
            10,
            "doc:id",
        )

        assert entity["type"] == "Parameter"
        assert entity["name"] == "count"
        assert entity["parameter_type"] == "int"
        assert entity["position"] == 0
        assert entity["is_vararg"] is False
        assert entity["method_name"] == "myMethod"
        assert entity["method_qualified_name"] == "com.example.MyClass.myMethod"
        assert entity["file_path"] == "com/example/MyClass.java"
        assert entity["repository"] == "my-repo"
        assert entity["module"] == "my-module"
        assert entity["start_line"] == 10
        assert entity["source"] == "doc:id"
        assert entity["annotations"] == []

    def test_varargs_parameter(self) -> None:
        """Verify varargs parameter identified correctly."""
        param = JavaParameter("args", "String", is_vararg=True, position=1)
        entity = parameter_to_entity(
            param, "main", "com.example.Main.main",
            "com/example/Main.java", "repo", "module", 5, "doc:id"
        )

        assert entity["is_vararg"] is True
        assert entity["parameter_type"] == "String"
        assert entity["position"] == 1

    def test_generic_type_parameter(self) -> None:
        """Verify generic type parameters handled correctly."""
        param = JavaParameter("items", "List<String>", position=0)
        entity = parameter_to_entity(
            param, "process", "Service.process",
            "Service.java", "repo", "module", 20, "doc:id"
        )

        assert entity["parameter_type"] == "List<String>"
        assert entity["name"] == "items"

    def test_array_type_parameter(self) -> None:
        """Verify array type parameters handled correctly."""
        param = JavaParameter("data", "byte[]", position=0)
        entity = parameter_to_entity(
            param, "write", "Writer.write",
            "Writer.java", "repo", "module", 15, "doc:id"
        )

        assert entity["parameter_type"] == "byte[]"

    def test_parameter_with_annotations(self) -> None:
        """Verify parameter annotations preserved."""
        param = JavaParameter(
            "id", "String",
            annotations=["@NotNull", "@PathVariable"],
            position=0
        )
        entity = parameter_to_entity(
            param, "getUser", "Controller.getUser",
            "Controller.java", "repo", "module", 25, "doc:id",
            imports=[]
        )

        assert len(entity["annotations"]) == 2


class TestExtractParameterEntities:
    """Tests for extract_parameter_entities function."""

    def test_no_parameters(self) -> None:
        """Verify empty list when no parameters."""
        entities = extract_parameter_entities(
            [], "myMethod", "MyClass.myMethod",
            "MyClass.java", "repo", "module", 10, "doc:id"
        )

        assert entities == []

    def test_single_parameter(self) -> None:
        """Verify single parameter extraction."""
        params = [JavaParameter("x", "int", position=0)]
        entities = extract_parameter_entities(
            params, "calculate", "MyClass.calculate",
            "MyClass.java", "repo", "module", 10, "doc:id"
        )

        assert len(entities) == 1
        assert entities[0]["name"] == "x"
        assert entities[0]["parameter_type"] == "int"
        assert entities[0]["position"] == 0

    def test_multiple_parameters(self) -> None:
        """Verify multiple parameters extraction with correct positions."""
        params = [
            JavaParameter("name", "String", position=0),
            JavaParameter("age", "int", position=1),
            JavaParameter("active", "boolean", position=2),
        ]
        entities = extract_parameter_entities(
            params, "createUser", "UserService.createUser",
            "UserService.java", "repo", "module", 20, "doc:id"
        )

        assert len(entities) == 3
        assert entities[0]["position"] == 0
        assert entities[1]["position"] == 1
        assert entities[2]["position"] == 2
        assert entities[0]["name"] == "name"
        assert entities[1]["name"] == "age"
        assert entities[2]["name"] == "active"

