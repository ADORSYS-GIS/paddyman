"""Tests for bundle-level Java entity normalization."""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

_POC_ROOT = Path(__file__).resolve().parents[2]
_PARSERS_ROOT = _POC_ROOT / "2_Parsers"
for _path in (str(_POC_ROOT), str(_PARSERS_ROOT)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from java_module_output import write_java_module_normalized_jsons
from normalized_json import build_normalized_json
from parser_bundle_entities import collect_parser_bundle_artifacts


def test_collect_parser_bundle_artifacts_normalizes_contract_shape(tmp_path: Path) -> None:
    out_dir = tmp_path / "parsed"
    out_dir.mkdir()
    payload = {
        "documents": [{"document_id": "doc-1", "provenance": {"path": "/abs/Foo.java"}}],
        "entities": [
            {
                "type": "Class",
                "name": "Foo",
                "source": "doc-1",
                "qualified_name": "com.example.Foo",
                "package": "com.example",
                "repository": "repo",
                "module": "mod",
                "file_path": "/abs/Foo.java",
                "annotations": [],
            },
            {
                "type": "Method",
                "name": "run",
                "source": "doc-1",
                "qualified_class": "com.example.Foo",
                "return_type": "String",
                "file_path": "/abs/Foo.java",
                "annotations": [],
            },
            {
                "type": "Parameter",
                "name": "value",
                "source": "doc-1",
                "method_qualified_name": "com.example.Foo.run",
                "parameter_type": "String",
                "position": 0,
                "file_path": "/abs/Foo.java",
            },
        ],
    }
    (out_dir / "repo_module.json").write_text(json.dumps(payload), encoding="utf-8")

    artifacts = collect_parser_bundle_artifacts(out_dir)
    class_entity = next(entity for entity in artifacts["entities"] if entity["type"] == "Class")
    method_entity = next(entity for entity in artifacts["entities"] if entity["type"] == "Method")

    assert class_entity["id"]
    assert class_entity["properties"]["fully_qualified_name"] == "com.example.Foo"
    assert class_entity["properties"]["package"] == "com.example"
    assert method_entity["properties"]["return_type"] == "String"
    assert method_entity["properties"]["signature"] == "String com.example.Foo.run(String value)"


def test_aspsp_xs2a_entities_appear_in_normalized_bundle(tmp_path: Path) -> None:
    repo_root = _POC_ROOT / "DataSource" / "code_projects" / "aspsp-xs2a"
    source_root = tmp_path / "source"
    repo_copy = source_root / "aspsp-xs2a"
    repo_copy.mkdir(parents=True)
    (repo_copy / "pom.xml").write_text("<project><modelVersion>4.0.0</modelVersion></project>", encoding="utf-8")

    aspsp_source = repo_root / "aspsp-profile" / "aspsp-profile-api" / "src" / "main" / "java" / "de" / "adorsys" / "psd2" / "aspsp" / "profile" / "domain"
    target_dir = repo_copy / "aspsp-profile" / "aspsp-profile-api" / "src" / "main" / "java" / "de" / "adorsys" / "psd2" / "aspsp" / "profile" / "domain"
    target_dir.mkdir(parents=True)
    for file_name in ("AspspSettings.java", "MulticurrencyAccountLevel.java"):
        shutil.copy2(aspsp_source / file_name, target_dir / file_name)
    (target_dir / "ContractProbe.java").write_text(
        "package de.adorsys.psd2.aspsp.profile.domain;\n"
        "@Deprecated\n"
        "public class ContractProbe {\n"
        "  private String probe;\n"
        "  public String probe(String value) { return value; }\n"
        "}\n",
        encoding="utf-8",
    )

    parser_output_dir = tmp_path / "parsed" / "java_code"
    parser_output_dir.mkdir(parents=True)
    paths = write_java_module_normalized_jsons(source_dir=source_root, output_dir=parser_output_dir)
    bundle = build_normalized_json(parser_output_dir=parser_output_dir)
    entities = bundle.to_dict()["entities"]

    assert paths
    assert entities
    assert any(entity["type"] == "Class" and entity["name"] == "AspspSettings" for entity in entities)
    assert any(entity["type"] == "Enum" and entity["name"] == "MulticurrencyAccountLevel" for entity in entities)

    aspsp_settings = next(entity for entity in entities if entity["type"] == "Class" and entity["name"] == "AspspSettings")
    methods = [entity for entity in entities if entity["type"] == "Method" and entity["name"] == "probe"]
    fields = [entity for entity in entities if entity["type"] == "Field" and entity["name"] == "probe"]

    assert aspsp_settings["properties"]["fully_qualified_name"].endswith("AspspSettings")
    assert aspsp_settings["properties"]["package"] == "de.adorsys.psd2.aspsp.profile.domain"
    assert aspsp_settings["properties"]["source_document"] == aspsp_settings["source"]
    assert methods and fields
    assert methods[0]["properties"]["signature"].startswith("String ")
    assert fields[0]["properties"]["type"] == "String"
    assert any(entity["properties"]["annotations"] for entity in entities if entity["type"] == "Class")