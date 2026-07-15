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

from shared.config import settings
from shared.models import NormalizedJson, SourceMetadata, SourceType

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
            bundle = NormalizedJson.from_dict(json.loads(path.read_text(encoding="utf-8")))
        except Exception as exc:
            logger.warning("Skipping invalid normalized JSON %s: %s", path, exc)
            continue
        records.extend(_records_from_bundle(bundle))
    return records


def load_markdown_records(source_dir: Path | None = None) -> list[ExtractionRecord]:
    """Return Markdown records from the normalized contract."""
    return _filter_by_parser(load_normalized_records(source_dir or settings.extraction_input_dir), "markdown_parser")


def load_openapi_records(source_dir: Path | None = None) -> list[ExtractionRecord]:
    """Return OpenAPI records from the normalized contract."""
    return _filter_by_parser(load_normalized_records(source_dir or settings.extraction_input_dir), "openapi_parser")


def load_java_records(source_dir: Path | None = None) -> list[ExtractionRecord]:
    """Return Java records from the normalized contract."""
    return _filter_by_parser(load_normalized_records(source_dir or settings.extraction_input_dir), "java_parser")


def _records_from_bundle(bundle: NormalizedJson) -> list[ExtractionRecord]:
    records: list[ExtractionRecord] = []
    for doc in bundle.documents:
        metadata = dict(doc.source_metadata)
        location = str(metadata.get("file_path") or metadata.get("location") or doc.document_id)
        source = SourceMetadata(
            source_id=doc.document_id,
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