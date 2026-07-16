"""Integration tests for enriched CALLS relationships in module output."""
from __future__ import annotations

from pathlib import Path

from java_module_output import write_java_module_normalized_jsons
from normalized_json import load_normalized_json


def test_calls_include_enhanced_properties_and_entity_ids(tmp_path: Path) -> None:
    repo = tmp_path / "test-repo"
    repo.mkdir()
    (repo / "Service.java").write_text(
        "package com.example;\n"
        "class AccountRepository { java.util.List<String> findAll() { return java.util.List.of(); } }\n"
        "class Service {\n"
        "  private final AccountRepository accountRepository = new AccountRepository();\n"
        "  java.util.List<String> getAccounts() {\n"
        "    return accountRepository.findAll();\n"
        "  }\n"
        "}\n"
    )

    out_dir = tmp_path / "out"
    out_dir.mkdir()
    paths = write_java_module_normalized_jsons(source_dir=tmp_path, output_dir=out_dir)
    assert paths

    bundle = load_normalized_json(list(out_dir.glob("*.json"))[0])
    calls = [r for r in bundle.relationships if r.get("type") == "CALLS"]
    assert calls

    call = next(c for c in calls if c.get("target_method") == "findAll")
    props = call.get("properties", {})
    assert props.get("call_site_line") == 6
    assert props.get("argument_count") == 0
    assert props.get("argument_types") == []
    assert props.get("method_signature") == "findAll()"
    assert props.get("is_static") is False
    assert "source_entity_id" in call
    assert "target_entity_id" in call


def test_calls_argument_count_matches_source(tmp_path: Path) -> None:
    repo = tmp_path / "test-repo"
    repo.mkdir()
    (repo / "A.java").write_text(
        "package com.example;\n"
        "class A {\n"
        "  void run() {\n"
        "    Utils.format(\"x\", 1, 2);\n"
        "  }\n"
        "}\n"
        "class Utils { static String format(String a, int b, int c) { return a; } }\n"
    )

    out_dir = tmp_path / "out"
    out_dir.mkdir()
    write_java_module_normalized_jsons(source_dir=tmp_path, output_dir=out_dir)

    bundle = load_normalized_json(list(out_dir.glob("*.json"))[0])
    calls = [r for r in bundle.relationships if r.get("type") == "CALLS"]
    assert len(calls) == 1
    props = calls[0].get("properties", {})
    assert props.get("argument_count") == 3
    assert props.get("argument_types") == ["String", "int", "int"]
    assert props.get("method_signature") == "format(String, int, int)"
