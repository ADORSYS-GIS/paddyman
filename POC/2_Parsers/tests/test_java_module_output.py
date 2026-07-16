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