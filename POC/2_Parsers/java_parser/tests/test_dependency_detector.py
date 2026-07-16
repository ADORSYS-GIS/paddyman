"""Tests for discovery.dependency_detector (Maven) and gradle_detector."""
from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from java_parser.discovery.dependency_detector import extract_maven_metadata
from java_parser.discovery.gradle_detector import extract_gradle_metadata


class TestExtractMavenMetadata:
    def test_extracts_coordinates(self, tmp_path: Path) -> None:
        pom = tmp_path / "pom.xml"
        pom.write_text(
            textwrap.dedent("""\
            <?xml version="1.0" encoding="UTF-8"?>
            <project xmlns="http://maven.apache.org/POM/4.0.0">
              <groupId>com.example</groupId>
              <artifactId>my-app</artifactId>
              <version>1.2.3</version>
            </project>
            """),
            encoding="utf-8",
        )
        meta = extract_maven_metadata(pom)
        assert meta is not None
        assert meta.group_id == "com.example"
        assert meta.artifact_id == "my-app"
        assert meta.version == "1.2.3"

    def test_extracts_parent(self, tmp_path: Path) -> None:
        pom = tmp_path / "pom.xml"
        pom.write_text(
            textwrap.dedent("""\
            <?xml version="1.0" encoding="UTF-8"?>
            <project xmlns="http://maven.apache.org/POM/4.0.0">
              <parent>
                <groupId>com.example</groupId>
                <artifactId>parent</artifactId>
                <version>2.0</version>
              </parent>
              <artifactId>child</artifactId>
            </project>
            """),
            encoding="utf-8",
        )
        meta = extract_maven_metadata(pom)
        assert meta is not None
        assert meta.parent_group_id == "com.example"
        assert meta.parent_artifact_id == "parent"
        assert meta.parent_version == "2.0"
        # groupId inherited from parent
        assert meta.group_id == "com.example"

    def test_extracts_declared_modules(self, multi_module_maven_repo: Path) -> None:
        meta = extract_maven_metadata(multi_module_maven_repo / "pom.xml")
        assert meta is not None
        assert set(meta.declared_modules) == {"api", "impl"}

    def test_extracts_dependencies(self, tmp_path: Path) -> None:
        pom = tmp_path / "pom.xml"
        pom.write_text(
            textwrap.dedent("""\
            <?xml version="1.0" encoding="UTF-8"?>
            <project xmlns="http://maven.apache.org/POM/4.0.0">
              <groupId>g</groupId><artifactId>a</artifactId><version>1</version>
              <dependencies>
                <dependency>
                  <groupId>org.springframework</groupId>
                  <artifactId>spring-core</artifactId>
                  <version>5.3.0</version>
                </dependency>
              </dependencies>
            </project>
            """),
            encoding="utf-8",
        )
        meta = extract_maven_metadata(pom)
        assert meta is not None
        assert len(meta.dependencies) == 1
        dep = meta.dependencies[0]
        assert dep["groupId"] == "org.springframework"
        assert dep["artifactId"] == "spring-core"

    def test_missing_artifact_id_returns_none(self, tmp_path: Path) -> None:
        pom = tmp_path / "pom.xml"
        pom.write_text(
            "<project xmlns='http://maven.apache.org/POM/4.0.0'>"
            "<groupId>g</groupId></project>",
            encoding="utf-8",
        )
        assert extract_maven_metadata(pom) is None

    def test_malformed_xml_returns_none(self, tmp_path: Path) -> None:
        pom = tmp_path / "pom.xml"
        pom.write_text("<project>NOT CLOSED", encoding="utf-8")
        assert extract_maven_metadata(pom) is None

    def test_missing_file_returns_none(self, tmp_path: Path) -> None:
        assert extract_maven_metadata(tmp_path / "pom.xml") is None

    def test_no_namespace_pom(self, tmp_path: Path) -> None:
        """pom.xml without XML namespace should still parse."""
        pom = tmp_path / "pom.xml"
        pom.write_text(
            "<project><groupId>g</groupId><artifactId>a</artifactId>"
            "<version>1</version></project>",
            encoding="utf-8",
        )
        meta = extract_maven_metadata(pom)
        assert meta is not None
        assert meta.artifact_id == "a"


class TestExtractGradleMetadata:
    def test_extracts_root_project_name(self, gradle_repo: Path) -> None:
        meta = extract_gradle_metadata(gradle_repo)
        assert meta is not None
        assert meta.project_name == "my-gradle-app"

    def test_no_gradle_files_returns_none(self, tmp_path: Path) -> None:
        assert extract_gradle_metadata(tmp_path) is None

    def test_extracts_included_builds(self, tmp_path: Path) -> None:
        (tmp_path / "settings.gradle").write_text(
            "rootProject.name = 'root'\n"
            "includeBuild('../shared-lib')\n"
            'includeBuild("../another")\n',
            encoding="utf-8",
        )
        (tmp_path / "build.gradle").touch()
        meta = extract_gradle_metadata(tmp_path)
        assert meta is not None
        assert "../shared-lib" in meta.included_builds
        assert "../another" in meta.included_builds

    def test_extracts_project_dependencies(self, tmp_path: Path) -> None:
        (tmp_path / "settings.gradle").write_text(
            "rootProject.name = 'app'\n", encoding="utf-8"
        )
        (tmp_path / "build.gradle").write_text(
            "dependencies { implementation project(':core') }\n",
            encoding="utf-8",
        )
        meta = extract_gradle_metadata(tmp_path)
        assert meta is not None
        assert ":core" in meta.project_dependencies

    def test_settings_only_no_build_file(self, tmp_path: Path) -> None:
        (tmp_path / "settings.gradle").write_text(
            "rootProject.name = 'lib'\n", encoding="utf-8"
        )
        meta = extract_gradle_metadata(tmp_path)
        assert meta is not None
        assert meta.project_name == "lib"
