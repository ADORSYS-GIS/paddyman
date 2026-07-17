import sys
from pathlib import Path

# Ensure POC and parsers directories are on sys.path so tests can import
# shared modules when run from the repository root.
_PARSERS_ROOT = Path(__file__).resolve().parent
_POC_ROOT = _PARSERS_ROOT.parent
for _path in (str(_POC_ROOT), str(_PARSERS_ROOT)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from shared.models.normalized import NormalizedJson
from shared.models.openapi import BaseOpenApiEntity
from parsers.openapi_parser.document_entities_builder import build_openapi_document_with_entities
from parsers.openapi_parser.operation_relationships import build_operation_relationships
from parsers.openapi_parser.relationship_builder import build_openapi_relationships
from shared.config import settings
import logging
from typing import Any

from normalized_json import write_normalized_json

logger = logging.getLogger(__name__)


def write_openapi_file_normalized_jsons(
    summaries: dict[str, Any] | None = None,
    source_dir: Path | None = None,
    output_dir: Path | None = None,
) -> list[Path]:
    """Persist OpenAPI parser output as one normalized JSON file per YAML spec."""
    root = source_dir or settings.yaml_spec_dir
    target_dir = output_dir or settings.parser_output_dir / "openapi_specs"
    target_dir.mkdir(parents=True, exist_ok=True)
    for old_file in target_dir.glob("*.json"):
        old_file.unlink()

    paths: list[Path] = []
    for spec_path in _spec_files(root):
        doc, entities = build_openapi_document_with_entities(root, spec_path)
        relationships = build_openapi_relationships(entities)
        relationships.extend(build_operation_relationships(entities))
        logger.debug("Built %d relationships from %s", len(relationships), spec_path.name)

        entity_dicts = [entity.dict() if isinstance(entity, BaseOpenApiEntity) else entity for entity in entities]

        # Build openapi_refs index mapping component $ref paths to emitted entity ids.
        refs: dict[str, str] = {}
        for ent in entity_dicts:
            src_loc = ent.get("source_location")
            if isinstance(src_loc, str) and src_loc.startswith("#/components/schemas/"):
                ent_id = ent.get("id") or ent.get("uuid")
                if ent_id:
                    refs[src_loc] = ent_id

        bundle = NormalizedJson(
            documents=[doc],
            entities=entity_dicts,
            relationships=relationships,
            parser_indices={"openapi_refs": refs},
            source_metadata=[doc.source_metadata],
            provenance={"stage": "openapi_parser", "parser": "openapi_parser", "path": str(spec_path)},
            version_metadata={"contract": "parser-json", "version": "1.0", "summaries": summaries or {}},
        )
        output_path = target_dir / f"{_safe_spec_name(root, spec_path)}.json"
        paths.append(write_normalized_json(bundle, output_path))
    return paths



def _spec_files(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted({path for pattern in ("*.yaml", "*.yml") for path in root.rglob(pattern) if path.is_file()})


def _safe_spec_name(root: Path, path: Path) -> str:
    raw = path.relative_to(root).with_suffix("").as_posix()
    return "".join(char if char.isalnum() or char in {"-", "_"} else "_" for char in raw)