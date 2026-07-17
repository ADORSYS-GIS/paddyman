"""Normalized JSON loader for the extraction pipeline."""
from __future__ import annotations

import json
import logging
import sys
from dataclasses import dataclass
from pathlib import Path

_POC_ROOT = Path(__file__).resolve().parents[1]
if str(_POC_ROOT) not in sys.path:
    sys.path.insert(0, str(_POC_ROOT))
_PARSERS_ROOT = _POC_ROOT / "2_Parsers"
if str(_PARSERS_ROOT) not in sys.path:
    sys.path.insert(0, str(_PARSERS_ROOT))

from shared.config import settings
from shared.models import NormalizedJson, SourceMetadata, SourceType
from shared.id_factory import normalize_document_id
from shared.validators import validate_bundle_contract, BundleValidationError
from parsers.normalized_json import PARSER_OUTPUT_FILENAME

logger = logging.getLogger(__name__)


@dataclass
class ExtractionRecord:
    """A normalized document ready for spaCy and GLM extraction."""

    text: str
    source_metadata: SourceMetadata
    source_parser: str


def load_all_records(input_dir: Path | None = None) -> list[ExtractionRecord]:
    """Load extraction records from the normalized parser JSON contract."""
    records = load_normalized_records(input_dir or settings.extraction_input_dir)
    logger.info("Total normalized extraction records loaded: %d", len(records))
    return records


def load_normalized_records(input_dir: Path) -> list[ExtractionRecord]:
    """Load all normalized JSON files from *input_dir*."""
    if not input_dir.exists():
        logger.warning("Normalized parser output directory not found: %s", input_dir)
        return []

    files = sorted(input_dir.rglob("*.json")) if input_dir.is_dir() else [input_dir]
    records: list[ExtractionRecord] = []
    for path in files:
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            logger.warning("Skipping invalid normalized JSON %s: %s", path, exc)
            continue

        # Determine expected contract: the aggregated top-level file must be
        # the normalized-json contract (by convention); all other files are
        # parser-level bundles.
        expected = "normalized-json" if path.name == PARSER_OUTPUT_FILENAME else "parser-json"
        try:
            validate_bundle_contract(raw, expected)
        except BundleValidationError as exc:
            logger.warning("Skipping %s due to bundle contract validation: %s", path, exc)
            continue

        try:
            bundle = NormalizedJson.from_dict(raw)
        except Exception as exc:
            logger.warning("Skipping invalid normalized JSON %s: %s", path, exc)
            continue
        records.extend(_records_from_bundle(bundle))
    return records


def load_markdown_records(source_dir: Path | None = None) -> list[ExtractionRecord]:
    """Return Markdown records from the normalized contract."""
    # Prefer normalized contract if available
    input_dir = source_dir or settings.extraction_input_dir
    records = _filter_by_parser(load_normalized_records(input_dir), "markdown_parser")
    if records:
        return records

    # Fallback: no normalized bundles found — try reading raw markdown files
    try:
        from markdown_parser.reader import load_documents as _md_reader
    except Exception:
        return []

    try:
        docs = _md_reader(input_dir)
    except Exception:
        logger.warning("markdown reader failed for %s", input_dir)
        return []

    out: list[ExtractionRecord] = []
    for doc in docs:
        text = getattr(doc, "text", doc.get("text") if isinstance(doc, dict) else "")
        metadata = getattr(doc, "metadata", doc.get("specification_metadata") if isinstance(doc, dict) else {}) or {}
        file_path = (
            getattr(doc, "metadata", {}).get("file_path")
            if hasattr(doc, "metadata") and isinstance(getattr(doc, "metadata"), dict)
            else (doc.get("file_path") if isinstance(doc, dict) else None)
        )
        location = str(file_path or input_dir)
        source = SourceMetadata(
            source_id=normalize_document_id(getattr(doc, "document_id", doc.get("document_id") if isinstance(doc, dict) else str(location))),
            source_type=_source_type("markdown_parser"),
            location=location,
            metadata={**(metadata if isinstance(metadata, dict) else {}), "source_parser": "markdown_parser"},
        )
        out.append(ExtractionRecord(text=text or "", source_metadata=source, source_parser="markdown_parser"))
    return out


def load_openapi_records(source_dir: Path | None = None) -> list[ExtractionRecord]:
    """Return OpenAPI records from the normalized contract."""
    input_dir = source_dir or settings.extraction_input_dir
    records = _filter_by_parser(load_normalized_records(input_dir), "openapi_parser")
    if records:
        return records

    try:
        from openapi_parser.readers import read_local as _openapi_reader
    except Exception:
        return []

    try:
        docs = _openapi_reader(input_dir)
    except Exception:
        logger.warning("openapi reader failed for %s", input_dir)
        return []

    out: list[ExtractionRecord] = []
    for doc in docs:
        text = getattr(doc, "text", doc.get("text") if isinstance(doc, dict) else "")
        metadata = getattr(doc, "metadata", doc.metadata if hasattr(doc, "metadata") else (doc.get("metadata") if isinstance(doc, dict) else {})) or {}
        file_path = metadata.get("file_path") if isinstance(metadata, dict) else None
        location = str(file_path or input_dir)
        source = SourceMetadata(
            source_id=normalize_document_id(str(file_path or getattr(doc, "id_", "openapi"))),
            source_type=_source_type("openapi_parser"),
            location=location,
            metadata={**(metadata if isinstance(metadata, dict) else {}), "source_parser": "openapi_parser"},
        )
        out.append(ExtractionRecord(text=text or "", source_metadata=source, source_parser="openapi_parser"))
    return out


def load_java_records(source_dir: Path | None = None) -> list[ExtractionRecord]:
    """Return Java records from the normalized contract."""
    return _filter_by_parser(load_normalized_records(source_dir or settings.extraction_input_dir), "java_parser")


def _records_from_bundle(bundle: NormalizedJson) -> list[ExtractionRecord]:
    records: list[ExtractionRecord] = []
    for doc in bundle.documents:
        metadata = dict(doc.source_metadata)
        location = str(metadata.get("file_path") or metadata.get("location") or doc.document_id)
        source = SourceMetadata(
            source_id=normalize_document_id(doc.document_id),
            source_type=_source_type(doc.source_parser),
            location=location,
            metadata={**metadata, "source_parser": doc.source_parser},
        )
        records.append(ExtractionRecord(text=doc.text, source_metadata=source, source_parser=doc.source_parser))
    return records


def _source_type(source_parser: str) -> SourceType:
    return SourceType.API if source_parser == "openapi_parser" else SourceType.DOCUMENT


def _filter_by_parser(records: list[ExtractionRecord], source_parser: str) -> list[ExtractionRecord]:
    return [record for record in records if record.source_parser == source_parser]