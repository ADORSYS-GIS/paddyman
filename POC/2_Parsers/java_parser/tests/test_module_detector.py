"""Tests for discovery.module_detector."""
from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from java_parser.discovery.module_detector import detect_modules, module_name


class TestDetectModules:
    def test_single_maven_module(self, maven_repo: Path) -> None:
        # No <modules> in the fixture pom → returns repo root as sole module
        modules = detect_modules(maven_repo)
        assert modules == [maven_repo]

    def test_multi_module_maven(self, multi_module_maven_repo: Path) -> None:
        modules = detect_modules(multi_module_maven_repo)
        names = {m.name for m in modules}
        assert "api" in names
        assert "impl" in names

    def test_single_gradle_module(self, gradle_repo: Path) -> None:
        modules = detect_modules(gradle_repo)
        assert modules == [gradle_repo]

    def test_gradle_multi_module(self, tmp_path: Path) -> None:
        (tmp_path / "settings.gradle").write_text(
            "rootProject.name = 'root'\n"
            "include(':core')\n"
            "include(':api')\n",
            encoding="utf-8",
        )
        (tmp_path / "build.gradle").touch()
        (tmp_path / "core").mkdir()
        (tmp_path / "api").mkdir()
        modules = detect_modules(tmp_path)
        names = {m.name for m in modules}
        assert "core" in names
        assert "api" in names

    def test_unknown_build_system_returns_root(self, tmp_path: Path) -> None:
        modules = detect_modules(tmp_path)
        assert modules == [tmp_path]

    def test_declared_module_missing_on_disk_is_skipped(
        self, tmp_path: Path
    ) -> None:
        pom = tmp_path / "pom.xml"
        pom.write_text(
            textwrap.dedent("""\
            <?xml version="1.0"?>
            <project xmlns="http://maven.apache.org/POM/4.0.0">
              <groupId>g</groupId><artifactId>a</artifactId><version>1</version>
              <modules><module>missing-dir</module></modules>
            </project>
            """),
            encoding="utf-8",
        )
        # missing-dir does not exist → fallback to root
        modules = detect_modules(tmp_path)
        assert modules == [tmp_path]


class TestModuleName:
    def test_child_module(self, multi_module_maven_repo: Path) -> None:
        api_path = multi_module_maven_repo / "api"
        assert module_name(api_path, multi_module_maven_repo) == "api"

    def test_nested_module(self, tmp_path: Path) -> None:
        nested = tmp_path / "consent-management" / "consent-core-api"
        nested.mkdir(parents=True)
        result = module_name(nested, tmp_path)
        assert result == "consent-management/consent-core-api"

    def test_root_module(self, maven_repo: Path) -> None:
        # module_path == repo_root → relative path is "."
        result = module_name(maven_repo, maven_repo)
        assert result == "."

    def test_unrelated_path_falls_back_to_name(self, tmp_path: Path) -> None:
        other = tmp_path.parent / "other"
        other.mkdir(exist_ok=True)
        result = module_name(other, tmp_path)
        assert result == "other"
