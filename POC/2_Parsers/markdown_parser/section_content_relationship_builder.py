"""Section content relationship builder for markdown.

Creates relationships linking sections to their content elements like
headings, tables, lists, paragraphs, and code blocks.
"""
from __future__ import annotations

import logging
from typing import Any

from .relationship_utils import create_relationship, is_in_range

logger = logging.getLogger(__name__)


def create_section_content_relationships(
    section_entities: list[dict[str, Any]],
    heading_entities: list[dict[str, Any]],
    table_entities: list[dict[str, Any]],
    list_entities: list[dict[str, Any]],
    paragraph_entities: list[dict[str, Any]],
    codeblock_entities: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Create relationships linking sections to their content elements.

    Creates HAS_HEADING, HAS_TABLE, HAS_LIST, HAS_PARAGRAPH, HAS_CODE relationships.

    Args:
        section_entities:   List of Section entity dicts.
        heading_entities:   List of Heading entity dicts.
        table_entities:     List of Table entity dicts.
        list_entities:      List of List entity dicts.
        paragraph_entities: List of Paragraph entity dicts.
        codeblock_entities: List of CodeBlock entity dicts.

    Returns:
        List of content relationship dicts.
    """
    relationships: list[dict[str, Any]] = []

    for section in section_entities:
        section_start = section["properties"]["start_line"]
        section_end = section["properties"]["end_line"]

        # Link headings
        for heading in heading_entities:
            if is_in_range(heading["properties"]["start_line"], section_start, section_end):
                relationships.append(create_relationship(
                    section["id"],
                    heading["id"],
                    "HAS_HEADING",
                    {"relationship_type": "section_to_heading"}
                ))

        # Link tables
        for table in table_entities:
            if is_in_range(table["properties"]["start_line"], section_start, section_end):
                relationships.append(create_relationship(
                    section["id"],
                    table["id"],
                    "HAS_TABLE",
                    {"relationship_type": "section_to_table"}
                ))

        # Link lists
        for list_entity in list_entities:
            if is_in_range(list_entity["properties"]["start_line"], section_start, section_end):
                relationships.append(create_relationship(
                    section["id"],
                    list_entity["id"],
                    "HAS_LIST",
                    {"relationship_type": "section_to_list"}
                ))

        # Link paragraphs
        for paragraph in paragraph_entities:
            if is_in_range(paragraph["properties"]["start_line"], section_start, section_end):
                relationships.append(create_relationship(
                    section["id"],
                    paragraph["id"],
                    "HAS_PARAGRAPH",
                    {"relationship_type": "section_to_paragraph"}
                ))

        # Link code blocks
        for codeblock in codeblock_entities:
            if is_in_range(codeblock["properties"]["start_line"], section_start, section_end):
                relationships.append(create_relationship(
                    section["id"],
                    codeblock["id"],
                    "HAS_CODE_BLOCK",
                    {"relationship_type": "section_to_code_block"}
                ))

    return relationships
