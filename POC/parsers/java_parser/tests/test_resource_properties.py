"""Tests for java_parser.resources — Chunk 1.7: Spring Boot resource file parser."""
from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from java_parser.resources import (
    ResourceSummary,
    scan_and_parse_resources,
)
from java_parser.resources.models import ResourceFileType, XmlType
from java_parser.resources.properties_parser import _parse_content, parse_properties_file
from java_parser.resources.scanner import find_resource_files, _assign_module, _is_excluded
from java_parser.resources.xml_parser import (
    _detect_xml_type,
    _parse_liquibase_xml,
    _parse_spring_xml,
    _parse_generic_xml,
    parse_xml_file,
)
from java_parser.resources.yaml_parser import _flatten, _is_go_template, _load_all_docs, parse_yaml_file
from java_parser.resources.pom_parser import parse_pom_file

import xml.etree.ElementTree as ET


# ── properties_parser ─────────────────────────────────────────────────────────


def test_properties_basic():
    kv = _parse_content("server.port=8080\nspring.datasource.url=jdbc:h2:mem:test")
    assert kv["server.port"] == "8080"
    assert kv["spring.datasource.url"] == "jdbc:h2:mem:test"


def test_properties_colon_separator():
    kv = _parse_content("name: value")
    assert kv["name"] == "value"


def test_properties_ignores_comments():
    kv = _parse_content("# comment\n! also comment\nkey=val")
    assert list(kv.keys()) == ["key"]


def test_properties_ignores_blank_lines():
    kv = _parse_content("\n\nkey=val\n\n")
    assert kv == {"key": "val"}


def test_properties_key_no_value():
    kv = _parse_content("standalone")
    assert "standalone" in kv
    assert kv["standalone"] == ""


def test_properties_continuation_line():
    kv = _parse_content("long=first \\\n  second")
    assert kv["long"] == "first second"


def test_parse_properties_file_not_found(tmp_path):
    _, errors = parse_properties_file(tmp_path / "missing.properties")
    assert errors


def test_parse_properties_file_roundtrip(tmp_path):
    p = tmp_path / "app.properties"
    p.write_text("a=1\nb=2\n", encoding="utf-8")
    kv, errors = parse_properties_file(p)
    assert not errors
    assert kv == {"a": "1", "b": "2"}


