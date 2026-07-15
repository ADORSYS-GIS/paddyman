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


# ── yaml_parser ───────────────────────────────────────────────────────────────


def test_flatten_simple_dict():
    flat = _flatten({"a": 1, "b": 2})
    assert flat == {"a": 1, "b": 2}


def test_flatten_nested():
    flat = _flatten({"server": {"port": 8080}})
    assert flat["server.port"] == 8080


def test_flatten_list():
    flat = _flatten({"items": ["x", "y"]})
    assert flat["items.0"] == "x"
    assert flat["items.1"] == "y"


def test_parse_yaml_file_simple(tmp_path):
    p = tmp_path / "app.yml"
    p.write_text("server:\n  port: 8080\n", encoding="utf-8")
    content, errors = parse_yaml_file(p)
    assert not errors
    assert content["flat"]["server.port"] == 8080


def test_parse_yaml_file_empty(tmp_path):
    p = tmp_path / "empty.yml"
    p.write_text("", encoding="utf-8")
    content, errors = parse_yaml_file(p)
    assert not errors
    assert content["raw"] == {}


def test_parse_yaml_file_invalid(tmp_path):
    p = tmp_path / "bad.yml"
    p.write_text("key: [unclosed", encoding="utf-8")
    _, errors = parse_yaml_file(p)
    assert errors


def test_parse_yaml_file_not_found(tmp_path):
    _, errors = parse_yaml_file(tmp_path / "missing.yml")
    assert errors


def test_parse_yaml_file_multi_document(tmp_path):
    """Multi-document YAML (--- separator) should merge all mapping docs."""
    p = tmp_path / "application.yml"
    p.write_text("server:\n  port: 8080\n---\nspring:\n  datasource:\n    url: jdbc:h2\n", encoding="utf-8")
    content, errors = parse_yaml_file(p)
    assert not errors
    assert content["flat"]["server.port"] == 8080
    assert "spring.datasource.url" in content["flat"]


def test_parse_yaml_file_unknown_tag(tmp_path):
    """Unknown tags like !reference should be tolerated without error."""
    p = tmp_path / ".gitlab-ci.yml"
    p.write_text("rules:\n  - !reference [.template, rules]\n", encoding="utf-8")
    content, errors = parse_yaml_file(p)
    assert not errors


def test_parse_yaml_file_go_template(tmp_path):
    """Helm / Go template files (containing '{{') should be skipped silently."""
    p = tmp_path / "deployment.yaml"
    p.write_text("{{ if .Values.enabled }}\napiVersion: apps/v1\n{{ end }}\n", encoding="utf-8")
    content, errors = parse_yaml_file(p)
    assert not errors
    assert content == {"raw": {}, "flat": {}}


def test_is_go_template_detects_helm():
    assert _is_go_template("{{- if .Values.ingress.enabled -}}\n")
    assert _is_go_template("{{ if .Values.enabled }}\n")
    assert not _is_go_template("server:\n  port: 8080\n")


def test_load_all_docs_multi_document():
    text = "a: 1\n---\nb: 2\n"
    data, errors = _load_all_docs(text)
    assert not errors
    assert data == {"a": 1, "b": 2}


