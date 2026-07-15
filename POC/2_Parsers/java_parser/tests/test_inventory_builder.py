"""Tests for discovery.inventory_builder."""
from __future__ import annotations

from pathlib import Path

import pytest

from java_parser.discovery.inventory_builder import (
    build_all_inventories,
    build_module_records,
    build_repository_inventory,
)
from java_parser.discovery.models import BuildSystem


class TestBuildRepositoryInventory:
    def test_maven_repo_inventory(self, maven_repo: Path) -> None:
        inv = build_repository_inventory(maven_repo)
        assert inv.repository == maven_repo.name
        assert inv.build_system == BuildSystem.MAVEN
        assert inv.maven_metadata is not None
        assert inv.maven_metadata.artifact_id == "my-app"
        assert len(inv.files) >= 1

    def test_gradle_repo_inventory(self, gradle_repo: Path) -> None:
        inv = build_repository_inventory(gradle_repo)
        assert inv.build_system == BuildSystem.GRADLE
        assert inv.gradle_metadata is not None
        assert inv.gradle_metadata.project_name == "my-gradle-app"
        assert len(inv.files) >= 1

    def test_multi_module_maven_inventory(
        self, multi_module_maven_repo: Path
    ) -> None:
        inv = build_repository_inventory(multi_module_maven_repo)
        assert inv.build_system == BuildSystem.MAVEN
        module_names = set(inv.modules)
        assert "api" in module_names
        assert "impl" in module_names
        assert len(inv.files) >= 2

    def test_file_record_fields(self, maven_repo: Path) -> None:
        inv = build_repository_inventory(maven_repo)
        record = inv.files[0]
        assert record.repository == maven_repo.name
        assert record.file.endswith(".java")
        assert record.package == "com.example"
        assert record.build_system == "maven"
        assert record.lines > 0
        assert "/" not in record.file  # bare filename only

    def test_empty_repo_returns_no_files(self, tmp_path: Path) -> None:
        inv = build_repository_inventory(tmp_path)
        assert inv.files == []
        assert inv.build_system == BuildSystem.UNKNOWN

    def test_errors_list_populated_on_bad_pom(self, tmp_path: Path) -> None:
        (tmp_path / "pom.xml").write_text("<project>BAD", encoding="utf-8")
        inv = build_repository_inventory(tmp_path)
        assert len(inv.errors) > 0

    def test_relative_path_uses_forward_slashes(self, maven_repo: Path) -> None:
        inv = build_repository_inventory(maven_repo)
        for record in inv.files:
            assert "\\" not in record.relative_path

    def test_to_dict_has_expected_keys(self, maven_repo: Path) -> None:
        inv = build_repository_inventory(maven_repo)
        d = inv.files[0].to_dict()
        expected_keys = {
            "repository", "module", "file", "relative_path",
            "package", "source_root", "lines", "build_system", "project_metadata",
        }
        assert expected_keys == set(d.keys())


class TestBuildModuleRecords:
    def test_records_created_for_java_files(self, maven_repo: Path) -> None:
        records = build_module_records(
            maven_repo, maven_repo, maven_repo.name, BuildSystem.MAVEN
        )
        assert len(records) >= 1

    def test_no_java_files_returns_empty(self, tmp_path: Path) -> None:
        records = build_module_records(
            tmp_path, tmp_path, "repo", BuildSystem.UNKNOWN
        )
        assert records == []


class TestBuildAllInventories:
    def test_discovers_multiple_repos(self, tmp_path: Path) -> None:
        for repo in ("repo-a", "repo-b"):
            d = tmp_path / repo
            (d / "src" / "main" / "java" / "com").mkdir(parents=True)
            (d / "pom.xml").write_text(
                f"<?xml version='1.0'?>"
                f"<project xmlns='http://maven.apache.org/POM/4.0.0'>"
                f"<groupId>com</groupId>"
                f"<artifactId>{repo}</artifactId>"
                f"<version>1</version></project>",
                encoding="utf-8",
            )
        inventories = build_all_inventories(tmp_path)
        names = {i.repository for i in inventories}
        assert "repo-a" in names
        assert "repo-b" in names

    def test_non_directory_entries_skipped(self, tmp_path: Path) -> None:
        (tmp_path / "file.txt").write_text("not a repo")
        (tmp_path / "repo").mkdir()
        inventories = build_all_inventories(tmp_path)
        assert all(i.root_path.is_dir() for i in inventories)

    def test_missing_base_dir_returns_empty(self, tmp_path: Path) -> None:
        result = build_all_inventories(tmp_path / "nonexistent")
        assert result == []

    def test_returns_sorted_by_repo_name(self, tmp_path: Path) -> None:
        for name in ("zzz", "aaa", "mmm"):
            (tmp_path / name).mkdir()
        inventories = build_all_inventories(tmp_path)
        names = [i.repository for i in inventories]
        assert names == sorted(names)
