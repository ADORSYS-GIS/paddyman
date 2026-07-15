"""
Handles writing markdown parser output to individual JSON files, one per specification.
"""
import logging
import re
import sys
from pathlib import Path
from typing import List

_PARSERS_ROOT = Path(__file__).resolve().parent
_POC_ROOT = _PARSERS_ROOT.parent
if str(_POC_ROOT) not in sys.path:
    sys.path.insert(0, str(_POC_ROOT))
if str(_PARSERS_ROOT) not in sys.path:
    sys.path.insert(0, str(_PARSERS_ROOT))

from shared.config import settings
from normalized_json import NormalizedJson, write_normalized_json
from markdown_parser.parser import markdown_to_normalized_docs

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

    # Process each markdown file
    for md_file in markdown_spec_dir.glob("*.md"):
        if md_file.is_file():
            process_specification_file(md_file, output_dir)


def process_specification_file(md_file: Path, output_dir: Path):
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

    # Use the document ID as the spec name
    spec_name = docs[0].document_id

    # Extract entities and relationships
    from markdown_parser.entity_orchestrator import extract_entities_and_relationships
    text = docs[0].text
    entities, relationships = extract_entities_and_relationships(
        md_file, text, spec_name
    )

    output_filename = _safe_filename(spec_name) + ".json"
    output_path = output_dir / output_filename

    # Create source metadata
    source_metadata = [{
        "file_path": str(md_file.absolute()),
        "file_name": md_file.name,
        "specification": spec_name,
        "source_parser": "markdown_parser",
        "entity_count": len(entities),
        "relationship_count": len(relationships),
    }]

    normalized_json = NormalizedJson(
        provenance={
            "stage": "markdown_parser",
            "parser": "markdown_parser",
            "specification": spec_name,
            "source_file": str(md_file),
        },
        documents=docs,
        entities=entities,
        relationships=relationships,
        source_metadata=source_metadata,
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