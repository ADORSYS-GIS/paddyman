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
from java_parser.call_entity_linker import attach_call_entity_ids
from java_parser.method_call_entity_builder import build_method_call_entities
from java_parser.field_type_relationship_builder import build_has_type_relationships
from java_parser.method_return_type_relationship_builder import build_returns_relationships
from java_parser.parameter_type_relationship_builder import build_parameter_has_type_relationships
from java_parser.spring_bean_relationship_builder import build_injects_bean_relationships
from java_parser.package_entity_builder import package_entity_for_record, unique_package_entities
from java_parser.package_relationship_builder import build_package_relationships
from java_parser.parameter_orchestrator import parameter_entities_and_relationships_for_record
from java_parser.java_relationship_builder import build_module_relationship_dicts
from normalized_json import write_normalized_json
from shared.config import settings
from shared.models import NormalizedJson
from shared.provenance import ensure_provenance

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
                    package_entity = package_entity_for_record(repo_root, record, module_label_str)
                    if package_entity is not None:
                        entities.append(package_entity)

                    file_entities = entities_for_record(repo_root, record, doc.document_id, module_label_str)
                    entities.extend(file_entities)
                    file_entity_groups.append(file_entities)

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

            entities = unique_package_entities(entities) + [
                entity for entity in entities if entity.get("type") != "Package"
            ]

            try:
                relationships = build_module_relationship_dicts(repo_root, records, module_label_str, inventory.files)

                for file_entities in file_entity_groups:
                    import_rels = build_imports_relationships(file_entities)
                    relationships.extend(import_rels)

                field_entities = [e for e in entities if e.get("type") == "Field"]
                if field_entities:
                    type_rels = build_has_type_relationships(field_entities, entities)
                    relationships.extend(type_rels)

                method_entities = [e for e in entities if e.get("type") == "Method"]
                if method_entities:
                    return_rels = build_returns_relationships(method_entities, entities)
                    relationships.extend(return_rels)

                relationships.extend(all_has_parameter_rels)

                parameter_entities = [e for e in entities if e.get("type") == "Parameter"]
                if parameter_entities:
                    param_type_rels = build_parameter_has_type_relationships(parameter_entities, entities)
                    relationships.extend(param_type_rels)
                relationships.extend(build_injects_bean_relationships(entities))

                relationships.extend(build_package_relationships(entities, module_label_str))
                attach_call_entity_ids(relationships, entities)

                # Build MethodCall entities and a compact method_calls index
                # that will be emitted at the top-level of the module JSON.
                try:
                    method_call_entities, method_calls_index = build_method_call_entities(
                        relationships, entities, repo_root
                    )
                    if method_call_entities:
                        entities.extend(method_call_entities)
                    # Log resolved / unresolved counts for visibility
                    unresolved = sum(1 for item in method_calls_index if not item.get("resolved"))
                    logger.info(
                        "Module %s: method calls: %d (unresolved: %d)",
                        module_label_str,
                        len(method_calls_index),
                        unresolved,
                    )
                except Exception:
                    method_calls_index = []

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
            # Ensure every entity.source references a document_id from this bundle.
            if documents:
                first_doc_id = documents[0].document_id
                for ent in entities:
                    if ent.get("type") == "Package":
                        # Normalize package entity source and preserve legacy qualified names
                        old_src = ent.get("source")
                        props = ent.setdefault("properties", {})
                        if old_src and old_src != first_doc_id and "qualified_name" not in props and "qualified_name" not in ent:
                            props["qualified_name"] = old_src
                        ent["source"] = first_doc_id
                # Also normalize paths for document-level source metadata and
                # ensure it conforms to the canonical SourceMetadata dict shape.
                from shared.provenance import normalize_paths
                from shared.models import SourceMetadata as _SourceMetadata

                for doc in documents:
                    try:
                        # If doc.source_metadata is already a SourceMetadata.to_dict()
                        # shape, extract the original parser-provided attributes
                        # from the `metadata` bag so they are fed back into the
                        # parser-normalizer correctly. Otherwise assume it's
                        # already a parser-style dict with parser keys at top-level.
                        if isinstance(doc.source_metadata, dict) and "metadata" in doc.source_metadata:
                            parser_meta = dict(doc.source_metadata.get("metadata") or {})
                            # Preserve any path hints that exist on the outer dict
                            if doc.source_metadata.get("location") and "file_path" not in parser_meta:
                                parser_meta["file_path"] = doc.source_metadata.get("location")
                            if doc.source_metadata.get("relative_path") and "relative_path" not in parser_meta:
                                parser_meta["relative_path"] = doc.source_metadata.get("relative_path")
                        else:
                            parser_meta = doc.source_metadata if isinstance(doc.source_metadata, dict) else doc.source_metadata.to_dict()
                    except Exception:
                        parser_meta = {}
                    canonical_meta = normalize_paths(parser_meta, root=repo_root)
                    # Rebuild canonical SourceMetadata so callers can safely do
                    # `SourceMetadata(**doc.source_metadata)` without unexpected keys.
                    doc.source_metadata = _SourceMetadata.from_parser_metadata(canonical_meta).to_dict()

            # Namespace optional parser indices under `parser_indices` while
            # preserving top-level `method_calls` for backward compatibility.
            parser_indices: dict[str, Any] = {}
            if method_calls_index:
                parser_indices["method_calls"] = method_calls_index

            # Ensure canonical provenance and attach location objects to
            # entities, relationships and method_calls for downstream
            # consumers.
            def _abs_path(p: str) -> str:
                try:
                    return str((repo_root / p).resolve())
                except Exception:
                    return str(p or "")

            # Map document_id -> absolute path for source resolution
            doc_path_map: dict[str, str] = {}
            for doc in documents:
                # Ensure per-document provenance includes minimal keys
                prov = ensure_provenance(doc.provenance if isinstance(doc.provenance, dict) else {}, file_path=doc.provenance.get("path") if isinstance(doc.provenance, dict) else None, stage="java_parser", parser="java_parser", module=module_label_str)
                doc.provenance = prov
                doc_path_map[doc.document_id] = prov.get("path") or prov.get("location") or ""

            # Attach location to entities when missing
            for ent in entities:
                if not isinstance(ent, dict):
                    continue
                if ent.get("location"):
                    continue
                file_rel = ent.get("file_path") or (ent.get("properties") or {}).get("source_path") or ""
                abs_p = _abs_path(file_rel) if file_rel else (doc_path_map.get(ent.get("source")) or str(repo_root))
                start = ent.get("start_line") or (ent.get("properties") or {}).get("start_line") or 1
                end = ent.get("end_line") or start
                try:
                    start_i = int(start) if start is not None else 1
                except Exception:
                    start_i = 1
                try:
                    end_i = int(end) if end is not None else start_i
                except Exception:
                    end_i = start_i
                ent["location"] = {"path": abs_p, "start_line": start_i, "end_line": end_i}

            # Attach location to relationships when missing
            for rel in relationships:
                if not isinstance(rel, dict):
                    continue
                if rel.get("location"):
                    continue
                file_rel = rel.get("file_path") or (rel.get("properties") or {}).get("file_path") or ""
                abs_p = _abs_path(file_rel) if file_rel else str(repo_root)
                start = (rel.get("properties") or {}).get("call_site_line") or rel.get("call_site_line") or 1
                try:
                    start_i = int(start) if start is not None else 1
                except Exception:
                    start_i = 1
                rel["location"] = {"path": abs_p, "start_line": start_i, "end_line": start_i}

            # Ensure method_call entities also have location (they may have file_path/start_line)
            for ent in entities:
                if not isinstance(ent, dict):
                    continue
                if ent.get("type") == "MethodCall" and not ent.get("location"):
                    file_rel = ent.get("file_path") or ""
                    abs_p = _abs_path(file_rel) if file_rel else str(repo_root)
                    start = ent.get("start_line") or 1
                    try:
                        start_i = int(start)
                    except Exception:
                        start_i = 1
                    ent["location"] = {"path": abs_p, "start_line": start_i, "end_line": ent.get("end_line") or start_i}

            # Ensure top-level bundle provenance includes path/stage/parser
            bundle_prov = {"stage": "java_parser", "parser": "java_parser", "module": module_label_str}
            bundle_prov = ensure_provenance(bundle_prov, file_path=repo_root, stage="java_parser", parser="java_parser", module=module_label_str)

            bundle = NormalizedJson(
                documents=documents,
                entities=entities,
                relationships=relationships,
                method_calls=method_calls_index,
                parser_indices=parser_indices,
                source_metadata=[doc.source_metadata for doc in documents],
                provenance=bundle_prov,
                version_metadata={"contract": "parser-json", "version": "1.0", "summaries": summaries or {}},
            )
            paths.append(write_normalized_json(bundle, target_dir / f"{safe_name(repo_root.name, module_label_str)}.json"))
    return paths
