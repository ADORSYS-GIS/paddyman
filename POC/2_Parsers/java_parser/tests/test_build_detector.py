"""Tests for discovery.build_detector."""
from __future__ import annotations

from pathlib import Path

import pytest

from java_parser.discovery.build_detector import (
    detect_build_system,
    find_build_files,
    find_gradle_build_files,
    find_pom_files,
)
from java_parser.discovery.models import BuildSystem


class TestDetectBuildSystem:
    def test_maven_repo_detected(self, maven_repo: Path) -> None:
        assert detect_build_system(maven_repo) == BuildSystem.MAVEN

    def test_gradle_repo_detected(self, gradle_repo: Path) -> None:
        assert detect_build_system(gradle_repo) == BuildSystem.GRADLE

    def test_unknown_when_no_build_files(self, tmp_path: Path) -> None:
        assert detect_build_system(tmp_path) == BuildSystem.UNKNOWN

    def test_maven_preferred_when_both_present(self, tmp_path: Path) -> None:
        (tmp_path / "pom.xml").touch()
        (tmp_path / "build.gradle").touch()
        assert detect_build_system(tmp_path) == BuildSystem.MAVEN

    def test_non_directory_returns_unknown(self, tmp_path: Path) -> None:
        f = tmp_path / "file.txt"
        f.touch()
        assert detect_build_system(f) == BuildSystem.UNKNOWN

    def test_gradle_kts_detected(self, tmp_path: Path) -> None:
        (tmp_path / "build.gradle.kts").touch()
        assert detect_build_system(tmp_path) == BuildSystem.GRADLE

    def test_settings_gradle_detected(self, tmp_path: Path) -> None:
        (tmp_path / "settings.gradle").touch()
        assert detect_build_system(tmp_path) == BuildSystem.GRADLE


class TestFindPomFiles:
    def test_finds_all_poms(self, multi_module_maven_repo: Path) -> None:
        poms = find_pom_files(multi_module_maven_repo)
        names = [p.parent.name for p in poms]
        assert "api" in names
        assert "impl" in names

    def test_empty_directory(self, tmp_path: Path) -> None:
        assert find_pom_files(tmp_path) == []

    def test_returns_sorted(self, tmp_path: Path) -> None:
        for name in ("b", "a", "c"):
            d = tmp_path / name
            d.mkdir()
            (d / "pom.xml").touch()
        poms = find_pom_files(tmp_path)
        assert poms == sorted(poms)


class TestFindGradleBuildFiles:
    def test_finds_gradle_file(self, gradle_repo: Path) -> None:
        files = find_gradle_build_files(gradle_repo)
        assert any(f.name == "build.gradle" for f in files)

    def test_empty_when_no_gradle(self, tmp_path: Path) -> None:
        assert find_gradle_build_files(tmp_path) == []


class TestFindBuildFiles:
    def test_returns_dict_with_both_keys(self, maven_repo: Path) -> None:
        result = find_build_files(maven_repo)
        assert BuildSystem.MAVEN in result
        assert BuildSystem.GRADLE in result

    def test_maven_repo_has_poms(self, maven_repo: Path) -> None:
        result = find_build_files(maven_repo)
        assert len(result[BuildSystem.MAVEN]) >= 1
