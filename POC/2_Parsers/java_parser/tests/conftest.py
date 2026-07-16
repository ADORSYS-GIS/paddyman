"""Shared fixtures for java_parser discovery tests."""
from __future__ import annotations

import textwrap
from pathlib import Path

import pytest


@pytest.fixture()
def tmp_repo(tmp_path: Path) -> Path:
    """Return a temporary directory representing a repository root."""
    return tmp_path


@pytest.fixture()
def maven_repo(tmp_path: Path) -> Path:
    """Single-module Maven repository with one Java file."""
    pom = tmp_path / "pom.xml"
    pom.write_text(
        textwrap.dedent("""\
        <?xml version="1.0" encoding="UTF-8"?>
        <project xmlns="http://maven.apache.org/POM/4.0.0">
          <modelVersion>4.0.0</modelVersion>
          <groupId>com.example</groupId>
          <artifactId>my-app</artifactId>
          <version>1.0.0</version>
        </project>
        """),
        encoding="utf-8",
    )
    java_dir = tmp_path / "src" / "main" / "java" / "com" / "example"
    java_dir.mkdir(parents=True)
    (java_dir / "App.java").write_text(
        "package com.example;\n\npublic class App {}\n", encoding="utf-8"
    )
    return tmp_path


@pytest.fixture()
def multi_module_maven_repo(tmp_path: Path) -> Path:
    """Multi-module Maven repository with two child modules."""
    root_pom = tmp_path / "pom.xml"
    root_pom.write_text(
        textwrap.dedent("""\
        <?xml version="1.0" encoding="UTF-8"?>
        <project xmlns="http://maven.apache.org/POM/4.0.0">
          <modelVersion>4.0.0</modelVersion>
          <groupId>com.example</groupId>
          <artifactId>parent</artifactId>
          <version>2.0.0</version>
          <packaging>pom</packaging>
          <modules>
            <module>api</module>
            <module>impl</module>
          </modules>
        </project>
        """),
        encoding="utf-8",
    )
    for module in ("api", "impl"):
        mod_dir = tmp_path / module
        (mod_dir / "src" / "main" / "java" / "com" / "example" / module).mkdir(
            parents=True
        )
        (mod_dir / "pom.xml").write_text(
            textwrap.dedent(f"""\
            <?xml version="1.0" encoding="UTF-8"?>
            <project xmlns="http://maven.apache.org/POM/4.0.0">
              <modelVersion>4.0.0</modelVersion>
              <parent>
                <groupId>com.example</groupId>
                <artifactId>parent</artifactId>
                <version>2.0.0</version>
              </parent>
              <artifactId>{module}</artifactId>
            </project>
            """),
            encoding="utf-8",
        )
        java_dir = mod_dir / "src" / "main" / "java" / "com" / "example" / module
        (java_dir / "Service.java").write_text(
            f"package com.example.{module};\n\npublic class Service {{}}\n",
            encoding="utf-8",
        )
    return tmp_path


@pytest.fixture()
def gradle_repo(tmp_path: Path) -> Path:
    """Single-module Gradle repository."""
    (tmp_path / "settings.gradle").write_text(
        "rootProject.name = 'my-gradle-app'\n", encoding="utf-8"
    )
    (tmp_path / "build.gradle").write_text(
        "apply plugin: 'java'\n", encoding="utf-8"
    )
    java_dir = tmp_path / "src" / "main" / "java" / "org" / "example"
    java_dir.mkdir(parents=True)
    (java_dir / "Main.java").write_text(
        "package org.example;\n\npublic class Main {}\n", encoding="utf-8"
    )
    return tmp_path
