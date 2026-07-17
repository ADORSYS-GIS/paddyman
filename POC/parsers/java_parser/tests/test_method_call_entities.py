"""Tests for MethodCall entity emission and top-level method_calls index."""
from __future__ import annotations

from pathlib import Path

from java_module_output import write_java_module_normalized_jsons
from normalized_json import load_normalized_json


def test_method_call_entities_and_index_emitted(tmp_path: Path) -> None:
    repo = tmp_path / "test-repo"
    repo.mkdir()
    (repo / "A.java").write_text(
        "package com.example;\n"
        "class A {\n"
        "  void run() { new B().hello(); }\n"
        "}\n"
        "class B { void hello() {} }\n"
    )

    out_dir = tmp_path / "out"
    out_dir.mkdir()
    paths = write_java_module_normalized_jsons(source_dir=tmp_path, output_dir=out_dir)
    assert paths

    bundle = load_normalized_json(list(out_dir.glob("*.json"))[0])

    # Top-level method_calls index exists and is non-empty
    assert getattr(bundle, "method_calls", [])

    # There is at least one MethodCall entity in entities
    method_calls = [e for e in bundle.entities if e.get("type") == "MethodCall"]
    assert method_calls

    mc = method_calls[0]
    assert "callee_qualified_name" in mc
    assert "caller_uuid" in mc
    assert "file_path" in mc
    assert "start_line" in mc

    # Top-level compact index contains enriched call records
    index = getattr(bundle, "method_calls", [])
    assert index
    idx0 = index[0]
    assert "id" in idx0
    assert "source" in idx0
    assert "caller_context" in idx0
    assert "callee_name" in idx0
    assert idx0["callee_name"] == "hello"
    assert "location" in idx0 and "path" in idx0["location"] and "start_line" in idx0["location"]
