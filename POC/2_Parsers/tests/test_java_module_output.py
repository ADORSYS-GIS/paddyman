"""Tests for Java module normalized document output."""
from __future__ import annotations

import json
import sys
from pathlib import Path

_POC_ROOT = Path(__file__).resolve().parents[2]
_PARSERS_ROOT = _POC_ROOT / "2_Parsers"
for _path in (str(_POC_ROOT), str(_PARSERS_ROOT)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from java_module_output import write_java_module_normalized_jsons


def _write_java(tmp_path: Path, source: str) -> Path:
    repo = tmp_path / "code" / "repo-a"
    java_dir = repo / "src" / "main" / "java" / "com"
    java_dir.mkdir(parents=True)
    (repo / "pom.xml").write_text(
        "<project><modelVersion>4.0.0</modelVersion></project>",
        encoding="utf-8",
    )
    (java_dir / "Example.java").write_text(source, encoding="utf-8")
    return tmp_path / "code"


def _source_metadata(tmp_path: Path, source: str) -> dict[str, object]:
    source_dir = _write_java(tmp_path, source)
    paths = write_java_module_normalized_jsons(
        source_dir=source_dir,
        output_dir=tmp_path / "parsed" / "java_code",
    )
    payload = json.loads(paths[0].read_text(encoding="utf-8"))
    return payload["documents"][0]["source_metadata"]


def test_java_document_metadata_contains_explicit_imports(tmp_path: Path) -> None:
    metadata = _source_metadata(
        tmp_path,
        "package com;\n"
        "import java.util.List;\n"
        "import java.util.Map;\n"
        "import java.time.Instant;\n"
        "import java.io.IOException;\n"
        "import lombok.extern.slf4j.Slf4j;\n"
        "class Example {}\n",
    )

    assert metadata["imports"] == [
        "java.util.List",
        "java.util.Map",
        "java.time.Instant",
        "java.io.IOException",
        "lombok.extern.slf4j.Slf4j",
    ]


def test_java_document_metadata_preserves_wildcard_import(tmp_path: Path) -> None:
    metadata = _source_metadata(
        tmp_path,
        "package com;\nimport java.io.*;\nclass Example {}\n",
    )

    assert metadata["imports"] == ["java.io.*"]


def test_java_document_metadata_has_empty_imports_for_no_imports(tmp_path: Path) -> None:
    metadata = _source_metadata(tmp_path, "package com;\nclass Example {}\n")

    assert metadata["imports"] == []


def test_java_module_output_emits_unique_packages_and_hierarchy(tmp_path: Path) -> None:
    source_dir = tmp_path / "code"
    repo = source_dir / "repo-a"
    (repo / "pom.xml").parent.mkdir(parents=True, exist_ok=True)
    (repo / "pom.xml").write_text(
        "<project><modelVersion>4.0.0</modelVersion></project>",
        encoding="utf-8",
    )
    parent_dir = repo / "src" / "main" / "java" / "com" / "example"
    child_dir = parent_dir / "internal"
    child_dir.mkdir(parents=True)
    (parent_dir / "Parent.java").write_text(
        "package com.example;\npublic class Parent {}\n",
        encoding="utf-8",
    )
    (child_dir / "Child.java").write_text(
        "package com.example.internal;\nimport com.example.Parent;\npublic class Child {}\n",
        encoding="utf-8",
    )

    out_dir = tmp_path / "parsed" / "java_code"
    paths = write_java_module_normalized_jsons(source_dir=source_dir, output_dir=out_dir)
    payload = json.loads(paths[0].read_text(encoding="utf-8"))
    packages = [e for e in payload["entities"] if e["type"] == "Package"]

    assert [p["qualified_name"] for p in packages] == ["com.example", "com.example.internal"]
    contains = [r for r in payload["relationships"] if r["type"] == "CONTAINS"]
    imports = [r for r in payload["relationships"] if r["type"] == "IMPORTS"]
    belongs_to = [r for r in payload["relationships"] if r["type"] == "BELONGS_TO"]
    assert any(
        r["source"] == "Package:com.example"
        and r["target"] == "Package:com.example.internal"
        for r in contains
    )
    assert any(
        r["source"] == "Package:com.example.internal"
        and r["target"] == "Package:com.example"
        for r in imports
    )
    assert any(r["source"] == "Package:com.example" and r["target"] == "Module:repo-a" for r in belongs_to)


def test_java_module_output_package_order_is_stable(tmp_path: Path) -> None:
    source_dir = tmp_path / "code"
    repo = source_dir / "repo-a"
    (repo / "pom.xml").parent.mkdir(parents=True, exist_ok=True)
    (repo / "pom.xml").write_text(
        "<project><modelVersion>4.0.0</modelVersion></project>",
        encoding="utf-8",
    )
    a_dir = repo / "src" / "main" / "java" / "com" / "example" / "a"
    b_dir = repo / "src" / "main" / "java" / "com" / "example" / "b"
    a_dir.mkdir(parents=True)
    b_dir.mkdir(parents=True)
    (a_dir / "A.java").write_text("package com.example.a; public class A {}", encoding="utf-8")
    (b_dir / "B.java").write_text("package com.example.b; public class B {}", encoding="utf-8")

    out_dir = tmp_path / "parsed" / "java_code"
    first = write_java_module_normalized_jsons(source_dir=source_dir, output_dir=out_dir)
    first_payload = json.loads(first[0].read_text(encoding="utf-8"))
    second = write_java_module_normalized_jsons(source_dir=source_dir, output_dir=out_dir)
    second_payload = json.loads(second[0].read_text(encoding="utf-8"))

    first_packages = [e["qualified_name"] for e in first_payload["entities"] if e["type"] == "Package"]
    second_packages = [e["qualified_name"] for e in second_payload["entities"] if e["type"] == "Package"]
    assert first_packages == second_packages == ["com.example.a", "com.example.b"]