from pathlib import Path
from shared.provenance import normalize_paths


def test_normalize_paths_from_absolute(tmp_path):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    subdir = repo_root / "docs"
    subdir.mkdir()
    f = subdir / "readme.md"
    f.write_text("hello")
    meta = {"file_path": str(f)}
    out = normalize_paths(meta, root=repo_root)
    assert "path" in out
    assert Path(out["path"]).resolve() == f.resolve()
    assert out["location"] == out["path"]
    assert out["file_name"] == "readme.md"
    assert out.get("relative_path") == "docs/readme.md"


def test_normalize_paths_with_relative_only(tmp_path):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    meta = {"relative_path": "a/b/c.txt"}
    out = normalize_paths(meta, root=repo_root)
    assert out.get("relative_path") == "a/b/c.txt"
    assert out.get("location") == "a/b/c.txt"
