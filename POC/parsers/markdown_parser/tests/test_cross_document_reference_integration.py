"""Integration tests for reference entities in markdown entity orchestration."""
from __future__ import annotations

from pathlib import Path

from markdown_parser.entity_orchestrator import extract_entities_and_relationships


def test_spec_document_has_reference_entities(tmp_path: Path) -> None:
    text = """
# 4 Overview

See Section 4.2 for details as defined by article 66 of [PSD2].

## 4.2 Authentication

OAuth2 details.
"""
    path = tmp_path / "spec.md"
    path.write_text(text)

    entities, _ = extract_entities_and_relationships(path, text, "spec")
    refs = [e for e in entities if e.get("type") == "Reference"]
    assert refs


def test_reference_counts_match_manual_expectation() -> None:
    text = "See Section 1.1 and [RFC6749] article 10 plus [guide](./guide.md)"
    entities, _ = extract_entities_and_relationships(Path("spec.md"), text, "spec")
    refs = [e for e in entities if e.get("type") == "Reference"]
    # Section + citation + article + hyperlink
    assert len(refs) >= 4
