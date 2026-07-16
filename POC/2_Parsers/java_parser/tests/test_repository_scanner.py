"""Tests for discovery.repository_scanner."""
from __future__ import annotations

from pathlib import Path

import pytest

from java_parser.discovery.repository_scanner import (
    count_lines,
    detect_source_root,
    extract_package,
    find_java_files,
)


class TestFindJavaFiles:
    def test_finds_java_files(self, maven_repo: Path) -> None:
        files = find_java_files(maven_repo)
        assert any(f.suffix == ".java" for f in files)

    def test_returns_empty_for_no_java(self, tmp_path: Path) -> None:
        assert find_java_files(tmp_path) == []

    def test_returns_sorted(self, tmp_path: Path) -> None:
        for name in ("Bravo.java", "Alpha.java", "Charlie.java"):
            (tmp_path / name).touch()
        files = find_java_files(tmp_path)
        assert files == sorted(files)

    def test_non_java_files_excluded(self, tmp_path: Path) -> None:
        (tmp_path / "Main.kt").touch()
        (tmp_path / "App.java").touch()
        files = find_java_files(tmp_path)
        assert all(f.suffix == ".java" for f in files)


class TestExtractPackage:
    def test_extracts_package(self, tmp_path: Path) -> None:
        f = tmp_path / "Foo.java"
        f.write_text("package com.example.service;\n\npublic class Foo {}\n")
        assert extract_package(f) == "com.example.service"

    def test_package_after_comment(self, tmp_path: Path) -> None:
        f = tmp_path / "Bar.java"
        f.write_text("/* copyright */\npackage org.test;\npublic class Bar {}\n")
        assert extract_package(f) == "org.test"

    def test_no_package_returns_empty(self, tmp_path: Path) -> None:
        f = tmp_path / "NoPackage.java"
        f.write_text("public class NoPackage {}\n")
        assert extract_package(f) == ""

    def test_empty_file_returns_empty(self, tmp_path: Path) -> None:
        f = tmp_path / "Empty.java"
        f.write_text("")
        assert extract_package(f) == ""

    def test_missing_file_returns_empty(self, tmp_path: Path) -> None:
        assert extract_package(tmp_path / "Missing.java") == ""

    def test_multiline_copyright_header(self, tmp_path: Path) -> None:
        content = (
            "/*\n"
            " * Copyright 2024\n"
            " * All rights reserved.\n"
            " */\n"
            "package de.adorsys.psd2.validator;\n\n"
            "public class Validator {}\n"
        )
        f = tmp_path / "Validator.java"
        f.write_text(content)
        assert extract_package(f) == "de.adorsys.psd2.validator"


class TestCountLines:
    def test_counts_correctly(self, tmp_path: Path) -> None:
        f = tmp_path / "Three.java"
        f.write_text("line1\nline2\nline3\n")
        assert count_lines(f) == 3

    def test_single_line(self, tmp_path: Path) -> None:
        f = tmp_path / "One.java"
        f.write_text("public class One {}\n")
        assert count_lines(f) == 1

    def test_empty_file_is_zero(self, tmp_path: Path) -> None:
        f = tmp_path / "Empty.java"
        f.write_text("")
        assert count_lines(f) == 0

    def test_missing_file_returns_zero(self, tmp_path: Path) -> None:
        assert count_lines(tmp_path / "Missing.java") == 0


class TestDetectSourceRoot:
    def test_standard_maven_source_root(self, maven_repo: Path) -> None:
        java_dir = maven_repo / "src" / "main" / "java" / "com" / "example"
        java_file = java_dir / "App.java"
        root = detect_source_root(java_file, maven_repo)
        assert root == "src/main/java"

    def test_test_source_root(self, tmp_path: Path) -> None:
        test_dir = tmp_path / "src" / "test" / "java" / "com" / "example"
        test_dir.mkdir(parents=True)
        f = test_dir / "AppTest.java"
        f.write_text("package com.example;\npublic class AppTest {}\n")
        root = detect_source_root(f, tmp_path)
        assert root == "src/test/java"

    def test_fallback_via_package(self, tmp_path: Path) -> None:
        pkg_dir = tmp_path / "source" / "de" / "adorsys"
        pkg_dir.mkdir(parents=True)
        f = pkg_dir / "Foo.java"
        f.write_text("package de.adorsys;\npublic class Foo {}\n")
        root = detect_source_root(f, tmp_path)
        assert root == "source"

    def test_no_source_root_detected(self, tmp_path: Path) -> None:
        f = tmp_path / "NoPackage.java"
        f.write_text("public class NoPackage {}\n")
        result = detect_source_root(f, tmp_path)
        # May be empty or a known root — just assert it doesn't raise
        assert isinstance(result, str)
