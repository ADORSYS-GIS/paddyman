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


# ── pom_parser ────────────────────────────────────────────────────────────────

_POM_XML = textwrap.dedent("""\
    <?xml version="1.0" encoding="UTF-8"?>
    <project xmlns="http://maven.apache.org/POM/4.0.0">
      <groupId>de.adorsys</groupId>
      <artifactId>my-service</artifactId>
      <version>1.0.0</version>
      <packaging>jar</packaging>
      <dependencies>
        <dependency>
          <groupId>org.springframework.boot</groupId>
          <artifactId>spring-boot-starter</artifactId>
          <version>3.2.0</version>
        </dependency>
      </dependencies>
      <build>
        <plugins>
          <plugin>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-maven-plugin</artifactId>
          </plugin>
        </plugins>
      </build>
    </project>
""")


def test_parse_pom_file_coordinates(tmp_path):
    p = tmp_path / "pom.xml"
    p.write_text(_POM_XML, encoding="utf-8")
    content, errors = parse_pom_file(p)
    assert not errors
    assert content["groupId"] == "de.adorsys"
    assert content["artifactId"] == "my-service"
    assert content["version"] == "1.0.0"


def test_parse_pom_file_dependencies(tmp_path):
    p = tmp_path / "pom.xml"
    p.write_text(_POM_XML, encoding="utf-8")
    content, _ = parse_pom_file(p)
    assert len(content["dependencies"]) == 1
    dep = content["dependencies"][0]
    assert dep["artifactId"] == "spring-boot-starter"


def test_parse_pom_file_plugins(tmp_path):
    p = tmp_path / "pom.xml"
    p.write_text(_POM_XML, encoding="utf-8")
    content, _ = parse_pom_file(p)
    assert len(content["plugins"]) == 1
    assert content["plugins"][0]["artifactId"] == "spring-boot-maven-plugin"


def test_parse_pom_file_invalid_xml(tmp_path):
    p = tmp_path / "pom.xml"
    p.write_text("<project><unclosed>", encoding="utf-8")
    _, errors = parse_pom_file(p)
    assert errors


