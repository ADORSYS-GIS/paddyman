"""Validate that each source Markdown file has exactly one parser output.

Usage:
  python validate_markdown_outputs.py

Exits with non-zero code when validation fails.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from shared.config import settings


def _safe_filename(name: str) -> str:
    import re

    return re.sub(r"[^\w\s-]", "_", name).replace(" ", "_")


def main() -> int:
    base = Path(__file__).resolve().parents[3]
    md_dir = Path(settings.markdown_spec_dir)
    if not md_dir.is_absolute():
        md_dir = base / md_dir

    out_dir = Path(settings.parser_output_dir) / "markdown"
    if not out_dir.is_absolute():
        out_dir = base / out_dir

    if not md_dir.exists():
        print(f"Source markdown directory not found: {md_dir}")
        return 2
    if not out_dir.exists():
        print(f"Parser output directory not found: {out_dir}")
        return 2

    md_files = sorted(md_dir.rglob("*.md"))
    failures = 0

    for md in md_files:
        spec_name = md.relative_to(md_dir).with_suffix("").as_posix()
        expected = _safe_filename(spec_name) + ".json"
        out_path = out_dir / expected
        if not out_path.exists():
            print(f"MISSING output for {md} -> expected {out_path}")
            failures += 1
            continue

        # Validate content: exactly one document and correct source location
        try:
            data = json.loads(out_path.read_text(encoding="utf-8"))
        except Exception as exc:
            print(f"FAILED to read {out_path}: {exc}")
            failures += 1
            continue

        docs = data.get("documents") or []
        if len(docs) != 1:
            print(f"INVALID document count in {out_path}: {len(docs)} (expected 1)")
            failures += 1
            continue

        doc_meta = docs[0].get("source_metadata") or {}
        location = doc_meta.get("location") or doc_meta.get("path")
        # Normalize paths for comparison
        try:
            expected_loc = str(md.resolve())
        except Exception:
            expected_loc = str(md)

        if location != expected_loc:
            print(f"MISMATCH location in {out_path}: {location} != {expected_loc}")
            failures += 1

    if failures:
        print(f"Validation failed: {failures} problem(s) found.")
        return 1

    print("Validation succeeded: one parser output per source markdown file.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
