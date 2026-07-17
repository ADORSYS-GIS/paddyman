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

# ── scan_and_parse_resources (integration) ────────────────────────────────────


def test_scan_and_parse_resources_counts(tmp_path):
    res_dir = tmp_path / "src" / "main" / "resources"
    res_dir.mkdir(parents=True)
    (res_dir / "app.properties").write_text("server.port=8080\ndb.url=jdbc:h2:mem")
    (res_dir / "app.yml").write_text("spring:\n  datasource:\n    url: jdbc:h2:mem\n")
    (tmp_path / "pom.xml").write_text(_POM_XML)
    (res_dir / "changelog.xml").write_text(_LIQUIBASE_XML)

    summary: ResourceSummary = scan_and_parse_resources(tmp_path, [tmp_path])
    assert summary.properties_count == 1
    assert summary.yaml_count == 1
    assert summary.pom_count == 1
    assert summary.migration_count == 1
    assert summary.config_keys >= 2  # at least 2 from .properties
    assert summary.maven_deps >= 1   # from pom.xml


def test_scan_and_parse_resources_empty_dir(tmp_path):
    summary = scan_and_parse_resources(tmp_path)
    assert summary.total_files == 0
    assert summary.errors == 0
