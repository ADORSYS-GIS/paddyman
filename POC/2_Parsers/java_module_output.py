"""Write Java parser normalized output as per-module JSON files."""
from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any

_PARSERS_ROOT = Path(__file__).resolve().parent
_POC_ROOT = _PARSERS_ROOT.parent
for _path in (str(_POC_ROOT), str(_PARSERS_ROOT)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from java_parser.discovery.inventory_builder import build_repository_inventory
from java_parser.document_builder import java_document, module_label, safe_name
from java_parser.java_entity_builder import entities_for_record
from java_parser.import_relationship_builder import build_imports_relationships
from java_parser.parameter_orchestrator import parameter_entities_and_relationships_for_record
from java_parser.java_relationship_builder import build_module_relationship_dicts
from normalized_json import write_normalized_json
from shared.config import settings
from shared.models import NormalizedJson

logger = logging.getLogger(__name__)


def write_java_module_normalized_jsons(
    summaries: dict[str, Any] | None = None,
    source_dir: Path | None = None,
    output_dir: Path | None = None,
) -> list[Path]:
    """Persist Java parser output as one normalized JSON file per module."""
    root = source_dir or settings.java_parser_source_dir
    target_dir = output_dir or settings.parser_output_dir / "java_code"
    target_dir.mkdir(parents=True, exist_ok=True)
    for old_file in target_dir.glob("*.json"):
        old_file.unlink()

    paths: list[Path] = []
    for repo_root in sorted(path for path in root.iterdir() if path.is_dir()):
        inventory = build_repository_inventory(repo_root)
        grouped: dict[str, list[Any]] = {}
        for record in inventory.files:
            grouped.setdefault(record.module, []).append(record)
        for module, records in sorted(grouped.items()):
            module_label_str = module_label(repo_root.name, module)
            documents = [java_document(repo_root, record, module_label_str) for record in records]
            
            # Extract entities for all files in module
            entities: list[Any] = []
            file_entity_groups: list[list[Any]] = []
            all_has_parameter_rels: list[Any] = []
            
            for doc, record in zip(documents, records):
                try:
                    file_entities = entities_for_record(repo_root, record, doc.document_id, module_label_str)
                    entities.extend(file_entities)
                    file_entity_groups.append(file_entities)
                    
                    # Extract parameter entities and relationships
                    param_entities, param_rels = parameter_entities_and_relationships_for_record(
                        repo_root, record, doc.document_id, module_label_str
                    )
                    entities.extend(param_entities)
                    all_has_parameter_rels.extend(param_rels)
                    
                    logger.debug(
                        "Extracted %d entities (%d parameters) from %s",
                        len(file_entities) + len(param_entities),
                        len(param_entities),
                        record.relative_path,
                    )
                except Exception as exc:
                    logger.error(
                        "Entity extraction failed for %s: %s",
                        record.relative_path,
                        exc,
                        exc_info=True,
                    )
                    file_entity_groups.append([])
            
            # Extract relationships for module
            try:
                relationships = build_module_relationship_dicts(repo_root, records, module_label_str, inventory.files)
                
                # Add IMPORTS relationships
                for file_entities in file_entity_groups:
                    import_rels = build_imports_relationships(file_entities)
                    relationships.extend(import_rels)
                
                # Add HAS_PARAMETER relationships
                relationships.extend(all_has_parameter_rels)
                
                logger.info(
                    "Module %s: %d entities, %d relationships from %d files",
                    module_label_str,
                    len(entities),
                    len(relationships),
                    len(records),
                )
            except Exception as exc:
                logger.error(
                    "Relationship extraction failed for module %s: %s",
                    module_label_str,
                    exc,
                    exc_info=True,
                )
                relationships = []
            
            bundle = NormalizedJson(
                documents=documents,
                entities=entities,
                relationships=relationships,
                source_metadata=[doc.source_metadata for doc in documents],
                provenance={"stage": "java_parser", "parser": "java_parser", "module": module_label_str},
                version_metadata={"contract": "parser-json", "version": "1.0", "summaries": summaries or {}},
            )
            paths.append(write_normalized_json(bundle, target_dir / f"{safe_name(repo_root.name, module_label_str)}.json"))
    return paths
