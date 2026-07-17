"""Verify parser outputs include canonical locations and provenance."""
from __future__ import annotations

import json
import sys
from pathlib import Path

_POC_ROOT = Path(__file__).resolve().parents[2]
_PARSERS_ROOT = _POC_ROOT / "2_Parsers"
for _p in (str(_POC_ROOT), str(_PARSERS_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from java_module_output import write_java_module_normalized_jsons


def test_bundle_contains_locations_and_canonical_provenance(tmp_path: Path) -> None:
    repo = tmp_path / "code" / "repo-a"
    java_dir = repo / "src" / "main" / "java" / "com"
    java_dir.mkdir(parents=True)
    (repo / "pom.xml").write_text("<project></project>", encoding="utf-8")
    (java_dir / "Example.java").write_text("package com; class Example { void hello() {} }", encoding="utf-8")

    out_dir = tmp_path / "parsed" / "java_code"
    paths = write_java_module_normalized_jsons(source_dir=tmp_path / "code", output_dir=out_dir)
    assert paths, "No output produced"
    payload = json.loads(paths[0].read_text(encoding="utf-8"))

    # Bundle provenance
    prov = payload.get("provenance") or {}
    assert isinstance(prov, dict)
    assert prov.get("path"), "Bundle provenance missing path"
    assert prov.get("stage") == "java_parser"
    assert prov.get("parser") == "java_parser"

    # Documents provenance
    docs = payload.get("documents") or []
    for d in docs:
        p = d.get("provenance") or {}
        assert p.get("path")
        assert p.get("parser") == "java_parser"

    # Entities contain location objects
    ents = payload.get("entities") or []
    assert ents, "No entities in payload"
    for e in ents:
        assert isinstance(e, dict)
        assert e.get("location") is not None, f"Entity missing location: {e.get('name')}"
        loc = e.get("location")
        assert loc.get("path")
        assert isinstance(loc.get("start_line"), int)

    # Relationships (if any) should contain location
    rels = payload.get("relationships") or []
    for r in rels:
        assert r.get("location") is not None
