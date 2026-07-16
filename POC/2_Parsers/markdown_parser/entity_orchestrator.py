"""Orchestrate entity extraction from markdown documents.

Coordinates all entity extractors and relationship builders to produce
a complete set of entities and relationships for a markdown document.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from .document_entity_builder import create_document_entity
from .section_entity_builder import create_section_entities
from .heading_entity_builder import create_heading_entities
from .frontmatter_entity_builder import create_frontmatter_entity
from .table_entity_builder import (
    create_table_entities,
    create_table_sequential_relationships,
)
from .list_entity_builder import create_list_entities
from .list_relationship_builder import create_list_relationships
from .paragraph_entity_builder import create_paragraph_entities
from .codeblock_entity_builder import create_codeblock_entities
from .reference_entity_builder import create_reference_entities
from .relationship_builder import (
    create_document_relationships,
    create_section_hierarchy_relationships,
)
from .section_hierarchy import (
    build_sibling_relationships,
    build_first_child_relationships,
    enrich_section_depth_and_path,
)
from .section_content_relationship_builder import create_section_content_relationships
from .reference_relationship_builder import create_reference_relationships
from .heading_relationship_builder import create_heading_relationships

logger = logging.getLogger(__name__)


def extract_entities_and_relationships(
    file_path: Path,
    text: str,
    document_id: str,
    specification_metadata: dict[str, Any] | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Extract all entities and relationships from a markdown document.

    Args:
        file_path:   Path to the markdown file.
        text:        Full text content of the document.
        document_id: Unique identifier for the document.
        specification_metadata: Optional specification metadata dict.

    Returns:
        Tuple of (entities, relationships) where both are lists of dicts.
    """
    entities: list[dict[str, Any]] = []
    relationships: list[dict[str, Any]] = []

    file_name = file_path.name

    # Extract entities
    logger.debug(f"Extracting entities from {file_name}")

    document_entity = create_document_entity(
        file_path, text, document_id, specification_metadata
    )
    entities.append(document_entity)

    section_entities = create_section_entities(text, file_name)
    entities.extend(section_entities)

    heading_entities = create_heading_entities(text, file_name)
    entities.extend(heading_entities)

    frontmatter_entity = create_frontmatter_entity(text, file_name)
    if frontmatter_entity:
        entities.append(frontmatter_entity)

    table_entities = create_table_entities(text, file_name)
    entities.extend(table_entities)

    list_entities = create_list_entities(text, file_name)
    entities.extend(list_entities)

    paragraph_entities = create_paragraph_entities(text, file_name)
    entities.extend(paragraph_entities)

    codeblock_entities = create_codeblock_entities(text, file_name)
    entities.extend(codeblock_entities)

    reference_entities = create_reference_entities(text, file_name)
    entities.extend(reference_entities)

    logger.info(
        f"Extracted {len(entities)} entities from {file_name}: "
        f"Document=1, Sections={len(section_entities)}, "
        f"Headings={len(heading_entities)}, "
        f"Frontmatter={1 if frontmatter_entity else 0}, "
        f"Tables={len(table_entities)}, "
        f"Lists={len(list_entities)}, Paragraphs={len(paragraph_entities)}, "
        f"CodeBlocks={len(codeblock_entities)}, References={len(reference_entities)}"
    )

    # Build relationships
    logger.debug(f"Building relationships for {file_name}")

    doc_rels = create_document_relationships(document_entity, section_entities)
    relationships.extend(doc_rels)

    hierarchy_rels = create_section_hierarchy_relationships(section_entities)
    relationships.extend(hierarchy_rels)

    sibling_rels = build_sibling_relationships(section_entities, hierarchy_rels)
    relationships.extend(sibling_rels)

    first_child_rels = build_first_child_relationships(section_entities, hierarchy_rels)
    relationships.extend(first_child_rels)

    enrich_section_depth_and_path(section_entities, hierarchy_rels)

    content_rels = create_section_content_relationships(
        section_entities,
        heading_entities,
        table_entities,
        list_entities,
        paragraph_entities,
        codeblock_entities,
    )
    relationships.extend(content_rels)

    ref_rels = create_reference_relationships(
        reference_entities,
        section_entities,
        paragraph_entities,
    )
    relationships.extend(ref_rels)

    heading_rels = create_heading_relationships(
        document_entity,
        section_entities,
        heading_entities,
        frontmatter_entity,
    )
    relationships.extend(heading_rels)

    table_seq_rels = create_table_sequential_relationships(table_entities)
    relationships.extend(table_seq_rels)

    list_rels = create_list_relationships(list_entities)
    relationships.extend(list_rels)

    logger.info(f"Created {len(relationships)} relationships for {file_name}")

    return entities, relationships
