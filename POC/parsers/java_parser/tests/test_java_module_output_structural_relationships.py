"""Tests that module-level normalized JSON contains structural relationships."""
from __future__ import annotations

from pathlib import Path

from java_module_output import write_java_module_normalized_jsons
from normalized_json import load_normalized_json


def _write_and_load(tmp_path: Path, src_files: dict[str, str]):
    repo = tmp_path / "repo"
    repo.mkdir()
    for name, content in src_files.items():
        (repo / name).write_text(content)

    out_dir = tmp_path / "out"
    out_dir.mkdir()
    paths = write_java_module_normalized_jsons(source_dir=tmp_path, output_dir=out_dir)
    assert paths
    json_files = list(out_dir.glob("*.json"))
    assert json_files
    return load_normalized_json(json_files[0])


def test_extends_relationship(tmp_path: Path) -> None:
    src = {
        "A.java": "package com.example; public class A extends B {}",
        "B.java": "package com.example; public class B {}",
    }
    bundle = _write_and_load(tmp_path, src)
    ext = [r for r in bundle.relationships if r.get("type") == "EXTENDS"]
    assert ext, f"expected EXTENDS, got: {bundle.relationships}"
    rel = ext[0]
    assert rel["source"].endswith(".A")
    assert rel["target"].endswith(".B")
    assert rel.get("target_module") is not None


def test_implements_relationships(tmp_path: Path) -> None:
    src = {
        "X.java": "package com.example; public interface X {}",
        "Y.java": "package com.example; public interface Y {}",
        "C.java": "package com.example; public class C implements X, Y {}",
    }
    bundle = _write_and_load(tmp_path, src)
    impls = [r for r in bundle.relationships if r.get("type") == "IMPLEMENTS"]
    assert len(impls) >= 2
    targets = {r["target"].split(".")[-1] for r in impls}
    assert "X" in targets and "Y" in targets


def test_di_injects_relationship(tmp_path: Path) -> None:
    src = {
        "Svc.java": "package com.example; public class Svc {}",
        "Ctrl.java": (
            "package com.example;\n"
            "import org.springframework.beans.factory.annotation.Autowired;\n"
            "public class Ctrl { @Autowired private Svc svc; }"
        ),
    }
    bundle = _write_and_load(tmp_path, src)
    inj = [r for r in bundle.relationships if r.get("type") == "INJECTS"]
    assert inj, f"expected INJECTS relationships, got: {bundle.relationships}"
    rel = inj[0]
    assert rel.get("field_name") == "svc"
    assert rel.get("target_module") is not None
