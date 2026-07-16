"""Unit tests for cross-document prose reference extraction."""
from __future__ import annotations

from markdown_parser.cross_document_reference_extractor import (
    extract_cross_document_references,
)
from markdown_parser.reference_entity_builder import create_reference_entities


def test_section_reference_extraction() -> None:
    refs = extract_cross_document_references("See Section 4.2 for details", "spec.md")
    section_refs = [r for r in refs if r["properties"].get("reference_type") == "section"]
    assert len(section_refs) == 1
    assert section_refs[0]["properties"]["target_section"] == "4.2"


def test_citation_reference_extraction() -> None:
    refs = extract_cross_document_references("Refer to [PSD2] article 66", "spec.md")
    spec_refs = [r for r in refs if r["properties"].get("reference_type") == "external_spec"]
    assert len(spec_refs) == 1
    assert spec_refs[0]["properties"]["target_spec"] == "PSD2"


def test_article_reference_extraction() -> None:
    refs = extract_cross_document_references("as defined in article 66", "spec.md")
    article_refs = [r for r in refs if r["properties"].get("reference_type") == "article"]
    assert len(article_refs) == 1
    assert article_refs[0]["properties"]["target_article"] == "66"


def test_hyperlink_extraction_available_via_reference_entities() -> None:
    refs = create_reference_entities("see [guide](https://example.com)", "spec.md")
    links = [r for r in refs if r["properties"].get("ref_type") == "link"]
    assert len(links) == 1
    assert links[0]["properties"]["target_url"] == "https://example.com"


def test_multiple_references_in_one_paragraph() -> None:
    refs = extract_cross_document_references(
        "See Section 4.2 and [PSD2] article 66 for details.",
        "spec.md",
    )
    types = {r["properties"].get("reference_type") for r in refs}
    assert {"section", "external_spec", "article"}.issubset(types)
