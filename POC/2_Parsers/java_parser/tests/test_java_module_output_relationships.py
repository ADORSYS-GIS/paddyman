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


def test_write_java_module_normalized_jsons_includes_returns(tmp_path: Path) -> None:
    repo = tmp_path / "test-repo"
    repo.mkdir()
    java_file = repo / "Service.java"
    java_file.write_text(
        "package com.example;\n"
        "class Account {}\n"
        "class Service {\n"
        "  Account getAccount() { return new Account(); }\n"
        "  java.util.List<Account> getAccounts() { return java.util.List.of(); }\n"
        "  void refresh() {}\n"
        "}\n"
    )

    out_dir = tmp_path / "out"
    out_dir.mkdir()

    paths = write_java_module_normalized_jsons(source_dir=tmp_path, output_dir=out_dir)
    assert paths

    bundle = load_normalized_json(list(out_dir.glob("*.json"))[0])
    method_entities = [e for e in bundle.entities if e.get("type") == "Method"]
    returns = [r for r in bundle.relationships if r.get("type") == "RETURNS"]
    entity_uuids = {e.get("uuid") for e in bundle.entities if e.get("uuid")}

    assert len(method_entities) == 3
    assert len(returns) == 3
    assert all(rel.get("source") in {m.get("uuid") for m in method_entities} for rel in returns)
    assert all(
        rel.get("target") in entity_uuids
        or rel.get("properties", {}).get("target_resolved") is False
        for rel in returns
    )


def test_write_java_module_normalized_jsons_includes_parameter_has_type(tmp_path: Path) -> None:
    repo = tmp_path / "test-repo"
    repo.mkdir()
    java_file = repo / "Api.java"
    java_file.write_text(
        "package com.example;\n"
        "class Account {}\n"
        "class Api {\n"
        "  void save(String name, int count, java.util.List<Account> accounts, String... values) {}\n"
        "}\n"
    )

    out_dir = tmp_path / "out"
    out_dir.mkdir()

    paths = write_java_module_normalized_jsons(source_dir=tmp_path, output_dir=out_dir)
    assert paths

    bundle = load_normalized_json(list(out_dir.glob("*.json"))[0])
    parameter_entities = [e for e in bundle.entities if e.get("type") == "Parameter"]
    parameter_uuids = {e.get("uuid") for e in parameter_entities}
    has_type_rels = [
        r
        for r in bundle.relationships
        if r.get("type") == "HAS_TYPE" and r.get("source") in parameter_uuids
    ]
    entity_uuids = {e.get("uuid") for e in bundle.entities if e.get("uuid")}

    assert parameter_entities
    assert len(has_type_rels) == len(parameter_entities)
    assert all(rel.get("source") in parameter_uuids for rel in has_type_rels)
    assert all(
        rel.get("target") in entity_uuids
        or rel.get("properties", {}).get("target_resolved") is False
        for rel in has_type_rels
    )
