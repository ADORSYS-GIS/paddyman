"""Build the normalized JSON contract from parser-stage outputs."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

_PARSERS_ROOT = Path(__file__).resolve().parent
_POC_ROOT = _PARSERS_ROOT.parent
if str(_POC_ROOT) not in sys.path:
    sys.path.insert(0, str(_POC_ROOT))
if str(_PARSERS_ROOT) not in sys.path:
    sys.path.insert(0, str(_PARSERS_ROOT))

from shared.config import settings
from shared.models import NormalizedDocument, NormalizedJson

PARSER_OUTPUT_FILENAME = "java_openapi_markdown_parser_output.json"
PARSER_SOURCES = {
    "java_parser": ("java_parser_source_dir", ("*.java",)),
    "openapi_parser": ("yaml_spec_dir", ("*.yaml", "*.yml")),
}
PARSER_SINGLE_FILE_OUTPUTS = {}


def build_normalized_json(summaries: dict[str, Any] | None = None) -> NormalizedJson:
    """Create the parser-agnostic JSON bundle consumed by extraction."""
    documents = [
        *_documents_from_files(settings.java_parser_source_dir, "java_parser", ("*.java",)),
        *_documents_from_files(settings.yaml_spec_dir, "openapi_parser", ("*.yaml", "*.yml")),
    ]
    metadata = [doc.source_metadata for doc in documents]
    return NormalizedJson(
        documents=documents,
        source_metadata=metadata,
        provenance={"stage": "parser_pipeline", "parser_order": ["java_parser", "openapi_parser"]},
        version_metadata={"contract": "normalized-json", "version": "1.0", "summaries": summaries or {}},
    )


def build_parser_normalized_json(
    source_parser: str,
    summaries: dict[str, Any] | None = None,
    source_dir: Path | None = None,
) -> NormalizedJson:
    """Create a normalized JSON bundle for one parser source."""
    if source_parser not in PARSER_SOURCES:
        raise ValueError(f"Unknown parser source: {source_parser}")
    setting_name, patterns = PARSER_SOURCES[source_parser]
    root = source_dir or getattr(settings, setting_name)
    documents = _documents_from_files(root, source_parser, patterns)
    return NormalizedJson(
        documents=documents,
        source_metadata=[doc.source_metadata for doc in documents],
        provenance={"stage": source_parser, "parser": source_parser},
        version_metadata={"contract": "parser-json", "version": "1.0", "summaries": summaries or {}},
    )


def write_normalized_json(bundle: NormalizedJson, output_path: Path | None = None) -> Path:
    """Persist *bundle* as the single parser-to-extraction contract."""
    path = output_path or settings.parser_output_dir / PARSER_OUTPUT_FILENAME
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(bundle.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    return path


def write_current_normalized_json(summaries: dict[str, Any] | None = None) -> Path:
    """Build and persist the current normalized parser output."""
    return write_normalized_json(build_normalized_json(summaries))


def write_parser_normalized_json(
    source_parser: str,
    summaries: dict[str, Any] | None = None,
    source_dir: Path | None = None,
) -> Path:
    """Build and persist the output for one direct parser command."""
    if source_parser not in PARSER_SINGLE_FILE_OUTPUTS:
        raise ValueError(f"{source_parser} does not support single-file direct output")
    filename = PARSER_SINGLE_FILE_OUTPUTS[source_parser]
    path = settings.parser_output_dir / filename
    return write_normalized_json(build_parser_normalized_json(source_parser, summaries, source_dir), path)


def load_normalized_json(path: Path) -> NormalizedJson:
    """Load a normalized JSON bundle from *path*."""
    return NormalizedJson.from_dict(json.loads(path.read_text(encoding="utf-8")))


def _documents_from_files(root: Path, source_parser: str, patterns: tuple[str, ...]) -> list[NormalizedDocument]:
    if not root.exists():
        return []
    documents: list[NormalizedDocument] = []
    for path in sorted({match for pattern in patterns for match in root.rglob(pattern)}):
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        metadata = {"file_path": str(path), "source_parser": source_parser}
        documents.append(
            NormalizedDocument(
                document_id=f"{source_parser}:{path.relative_to(root)}",
                text=text,
                source_parser=source_parser,
                source_metadata=metadata,
                provenance={"path": str(path), "stage": "parser_pipeline"},
            )
        )
    return documents

