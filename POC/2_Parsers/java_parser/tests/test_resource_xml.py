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



# ── xml_parser — type detection ───────────────────────────────────────────────

_LIQUIBASE_XML = textwrap.dedent("""\
    <?xml version="1.0"?>
    <databaseChangeLog xmlns="http://www.liquibase.org/xml/ns/dbchangelog">
      <changeSet id="1" author="dev" context="test">
        <insert tableName="users"/>
      </changeSet>
    </databaseChangeLog>
""")

_SPRING_XML = textwrap.dedent("""\
    <?xml version="1.0"?>
    <beans xmlns="http://www.springframework.org/schema/beans">
      <bean id="myBean" class="com.example.MyBean"/>
    </beans>
""")

_GENERIC_XML = textwrap.dedent("""\
    <?xml version="1.0"?>
    <configuration>
      <property name="debug" value="true"/>
    </configuration>
""")


def test_detect_xml_type_pom(tmp_path):
    p = tmp_path / "pom.xml"
    p.write_text(_POM_XML, encoding="utf-8")
    root = ET.parse(p).getroot()
    assert _detect_xml_type(p, root) == XmlType.POM


def test_detect_xml_type_liquibase(tmp_path):
    p = tmp_path / "0001-initial.xml"
    p.write_text(_LIQUIBASE_XML, encoding="utf-8")
    root = ET.parse(p).getroot()
    assert _detect_xml_type(p, root) == XmlType.LIQUIBASE


def test_detect_xml_type_spring(tmp_path):
    p = tmp_path / "context.xml"
    p.write_text(_SPRING_XML, encoding="utf-8")
    root = ET.parse(p).getroot()
    assert _detect_xml_type(p, root) == XmlType.SPRING


def test_detect_xml_type_generic(tmp_path):
    p = tmp_path / "config.xml"
    p.write_text(_GENERIC_XML, encoding="utf-8")
    root = ET.parse(p).getroot()
    assert _detect_xml_type(p, root) == XmlType.GENERIC


def test_parse_liquibase_changesets(tmp_path):
    p = tmp_path / "changelog.xml"
    p.write_text(_LIQUIBASE_XML, encoding="utf-8")
    root = ET.parse(p).getroot()
    result = _parse_liquibase_xml(root)
    assert result["changeset_count"] == 1
    assert result["changesets"][0]["id"] == "1"
    assert result["changesets"][0]["author"] == "dev"


def test_parse_spring_beans(tmp_path):
    p = tmp_path / "beans.xml"
    p.write_text(_SPRING_XML, encoding="utf-8")
    root = ET.parse(p).getroot()
    result = _parse_spring_xml(root)
    assert result["bean_count"] == 1
    assert result["beans"][0]["class"] == "com.example.MyBean"


def test_parse_generic_xml(tmp_path):
    p = tmp_path / "config.xml"
    p.write_text(_GENERIC_XML, encoding="utf-8")
    root = ET.parse(p).getroot()
    result = _parse_generic_xml(root)
    assert result["root_element"] == "configuration"
    assert "property" in result["child_elements"]


def test_parse_xml_file_invalid(tmp_path):
    p = tmp_path / "bad.xml"
    p.write_text("<unclosed>", encoding="utf-8")
    _, _, errors = parse_xml_file(p)
    assert errors


