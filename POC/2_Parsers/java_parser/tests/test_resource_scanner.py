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

# ── scanner ───────────────────────────────────────────────────────────────────


def test_is_excluded_target(tmp_path):
    f = tmp_path / "target" / "classes" / "application.properties"
    assert _is_excluded(f, tmp_path)


def test_is_excluded_git(tmp_path):
    f = tmp_path / ".git" / "config"
    assert _is_excluded(f, tmp_path)


def test_is_not_excluded_src(tmp_path):
    f = tmp_path / "src" / "main" / "resources" / "application.properties"
    assert not _is_excluded(f, tmp_path)


def test_assign_module_best_match(tmp_path):
    root = tmp_path
    mod_a = root / "module-a"
    mod_b = root / "module-a" / "sub-b"
    file_path = root / "module-a" / "sub-b" / "file.properties"
    label = _assign_module(file_path, [mod_a, mod_b], root)
    assert label == "module-a/sub-b"


def test_assign_module_root_fallback(tmp_path):
    f = tmp_path / "pom.xml"
    label = _assign_module(f, [tmp_path / "module-a"], tmp_path)
    assert label == "root"


def test_find_resource_files_basic(tmp_path):
    (tmp_path / "src" / "main" / "resources").mkdir(parents=True)
    (tmp_path / "src" / "main" / "resources" / "app.properties").write_text("k=v")
    (tmp_path / "src" / "main" / "resources" / "config.yml").write_text("a: 1")
    (tmp_path / "pom.xml").write_text(_POM_XML)
    records = find_resource_files(tmp_path, [tmp_path], repository="test-repo")
    paths = [r.relative_path for r in records]
    assert any("app.properties" in p for p in paths)
    assert any("config.yml" in p for p in paths)
    assert any("pom.xml" in p for p in paths)


def test_find_resource_files_excludes_target(tmp_path):
    (tmp_path / "target").mkdir()
    (tmp_path / "target" / "app.properties").write_text("k=v")
    records = find_resource_files(tmp_path, [tmp_path], repository="test-repo")
    assert not records


def test_find_resource_files_type_assignment(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "file.yaml").write_text("x: 1")
    records = find_resource_files(tmp_path, [tmp_path])
    assert records[0].file_type == ResourceFileType.YAML.value


