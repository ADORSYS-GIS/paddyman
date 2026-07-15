"""Tests for writing module-level normalized JSON with relationships."""
from __future__ import annotations

from pathlib import Path

from java_module_output import write_java_module_normalized_jsons
from normalized_json import load_normalized_json


def test_write_java_module_normalized_jsons_includes_calls(tmp_path: Path) -> None:
    # Create a fake repository with one Java file containing a method call
    repo = tmp_path / "test-repo"
    repo.mkdir()
    java_file = repo / "A.java"
    java_file.write_text(
        "package com.example;\n"
        "public class A { public void a() { b.c(); } }\n"
        "class B { public void c() {} }\n"
    )

    out_dir = tmp_path / "out"
    out_dir.mkdir()

    paths = write_java_module_normalized_jsons(source_dir=tmp_path, output_dir=out_dir)
    assert paths

    json_files = list(out_dir.glob("*.json"))
    assert len(json_files) == 1

    bundle = load_normalized_json(json_files[0])
    calls = [r for r in bundle.relationships if r.get("type") == "CALLS"]
    assert calls, f"expected CALLS relationships, got: {bundle.relationships}"
    rel = calls[0]
    assert "source" in rel and "target" in rel and "repository" in rel and "module" in rel
