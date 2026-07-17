"""
Handles writing markdown parser output to individual JSON files, one per specification.
"""
import logging
import re
import sys
from pathlib import Path
from typing import List
from datetime import datetime, timezone
from uuid import uuid5, NAMESPACE_URL

_PARSERS_ROOT = Path(__file__).resolve().parent
_POC_ROOT = _PARSERS_ROOT.parent
if str(_POC_ROOT) not in sys.path:
    sys.path.insert(0, str(_POC_ROOT))
if str(_PARSERS_ROOT) not in sys.path:
    sys.path.insert(0, str(_PARSERS_ROOT))

from shared.config import settings
from normalized_json import NormalizedJson, write_normalized_json
from shared.models import SourceMetadata
from markdown_parser.parser import markdown_to_normalized_docs
from shared.provenance import ensure_provenance

logger = logging.getLogger(name=__name__)


def _safe_filename(name: str) -> str:
    """Convert a string into a safe filename by replacing invalid characters with underscores."""
    return re.sub(r'[^\w\s-]', '_', name).replace(' ', '_')


def write_markdown_parser_output(markdown_spec_dir: Path, output_dir: Path):
    """
    Processes complete markdown specification files from markdown_spec_dir,
    parses each file, and writes a separate JSON file for each specification.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Created markdown parser output directory: {output_dir}")

    if not markdown_spec_dir.is_dir():
        logger.warning(f"Markdown specification directory not found: {markdown_spec_dir}")
        return

    # Walk every markdown file under the source directory and write one
    # normalized JSON output per source file. This guarantees a 1:1 mapping
    # from source Markdown -> parsed output bundle.
    md_files = sorted(markdown_spec_dir.rglob("*.md"))
    for md in md_files:
        if md.is_file():
            process_specification_file(md, output_dir, markdown_spec_dir)


def process_specification_file(md_file: Path, output_dir: Path, base_dir: Path | None = None):
    """
    Parses a single complete markdown specification file and writes it
    to a JSON output file.
    """
    logger.info(f"Processing specification file: {md_file.name}")

    # Parse the complete markdown file
    docs = markdown_to_normalized_docs(md_file)

    if not docs:
        logger.warning(f"No documents extracted from file: {md_file.name}")
        return

    # Use the file's path relative to the source directory as the spec name
    # when possible to ensure unique, human-readable output filenames.
    if base_dir is not None:
        try:
            spec_name = md_file.relative_to(base_dir).with_suffix("").as_posix()
        except Exception:
            spec_name = docs[0].document_id
    else:
        spec_name = docs[0].document_id

    # Extract entities and relationships
    from markdown_parser.entity_orchestrator import extract_entities_and_relationships
    text = docs[0].text
    entities, relationships = extract_entities_and_relationships(
        md_file, text, spec_name
    )

    output_filename = _safe_filename(spec_name) + ".json"
    output_path = output_dir / output_filename

    # Create source metadata (normalized)
    determinist_id = str(uuid5(NAMESPACE_URL, str(md_file.resolve())))
    determinist_ingested = datetime.fromtimestamp(md_file.stat().st_mtime, tz=timezone.utc).isoformat()

    parser_meta = {
        "file_path": str(md_file.absolute()),
        "file_name": md_file.name,
        "specification": spec_name,
        "source_parser": "markdown_parser",
        "entity_count": len(entities),
        "relationship_count": len(relationships),
        "id": determinist_id,
        "ingested_at": determinist_ingested,
    }
    from shared.provenance import normalize_paths
    canonical_meta = normalize_paths(parser_meta, root=md_file.parent)
    source_metadata = [SourceMetadata.from_parser_metadata(canonical_meta).to_dict()]

    normalized_json = NormalizedJson(
        provenance=ensure_provenance(
            {"specification": spec_name, "source_file": str(md_file)},
            file_path=md_file,
            stage="markdown_parser",
            parser="markdown_parser",
        ),
        documents=docs,
        entities=entities,
        relationships=relationships,
        source_metadata=source_metadata,
        version_metadata={"contract": "parser-json", "version": "1.0", "summaries": {}},
    )
    write_normalized_json(normalized_json, output_path)
    logger.info(
        f"Wrote {len(docs)} document(s), {len(entities)} entities, "
        f"and {len(relationships)} relationships to {output_path}"
    )


def main():
    """Main function to run the markdown parser output writer."""
    markdown_spec_dir = settings.markdown_spec_dir
    markdown_output_dir = settings.parser_output_dir / "markdown"

    write_markdown_parser_output(markdown_spec_dir, markdown_output_dir)


if __name__ == "__main__":
    main()