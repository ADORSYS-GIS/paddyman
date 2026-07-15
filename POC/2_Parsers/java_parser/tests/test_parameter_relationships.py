"""Tests for parameter relationship building."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

_PARSERS_ROOT = Path(__file__).resolve().parent.parent.parent
_POC_ROOT = _PARSERS_ROOT.parent
for _p in (str(_POC_ROOT), str(_PARSERS_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from java_parser.parameter_entity_builder import build_has_parameter_relationships


class TestBuildHasParameterRelationships:
    """Tests for build_has_parameter_relationships function."""

    def test_no_parameters(self) -> None:
        """Verify empty relationships when no parameters."""
        method_entity = {"uuid": "method-123", "name": "myMethod"}
        relationships = build_has_parameter_relationships(method_entity, [])

        assert relationships == []

    def test_single_parameter_relationship(self) -> None:
        """Verify single HAS_PARAMETER relationship created."""
        method_entity = {"uuid": "method-123", "name": "myMethod"}
        param_entities = [
            {"uuid": "param-456", "name": "x", "position": 0}
        ]
        relationships = build_has_parameter_relationships(method_entity, param_entities)

        assert len(relationships) == 1
        rel = relationships[0]
        assert rel["type"] == "HAS_PARAMETER"
        assert rel["source"] == "method-123"
        assert rel["target"] == "param-456"
        assert rel["properties"]["position"] == 0

    def test_multiple_parameter_relationships(self) -> None:
        """Verify multiple HAS_PARAMETER relationships with correct positions."""
        method_entity = {"uuid": "method-123", "name": "myMethod"}
        param_entities = [
            {"uuid": "param-1", "name": "a", "position": 0},
            {"uuid": "param-2", "name": "b", "position": 1},
            {"uuid": "param-3", "name": "c", "position": 2},
        ]
        relationships = build_has_parameter_relationships(method_entity, param_entities)

        assert len(relationships) == 3
        for i, rel in enumerate(relationships):
            assert rel["type"] == "HAS_PARAMETER"
            assert rel["source"] == "method-123"
            assert rel["target"] == f"param-{i+1}"
            assert rel["properties"]["position"] == i

    def test_relationship_preserves_position_order(self) -> None:
        """Verify position property is correctly set for each relationship."""
        method_entity = {"uuid": "m-1", "name": "test"}
        param_entities = [
            {"uuid": "p-10", "name": "x", "position": 10},
            {"uuid": "p-20", "name": "y", "position": 20},
        ]
        relationships = build_has_parameter_relationships(method_entity, param_entities)

        assert relationships[0]["properties"]["position"] == 10
        assert relationships[1]["properties"]["position"] == 20
