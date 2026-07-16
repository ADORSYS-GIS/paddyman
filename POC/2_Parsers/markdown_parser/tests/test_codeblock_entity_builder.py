"""Unit tests for codeblock_entity_builder."""
from __future__ import annotations

import pytest
from markdown_parser.codeblock_entity_builder import create_codeblock_entities


class TestCreateCodeblockEntities:
    """Tests for create_codeblock_entities."""

    def test_json_code_block(self):
        """JSON code block: language, code, is_example=True, is_request=False."""
        text = '```json\n{"key": "value"}\n```'
        entities = create_codeblock_entities(text, "spec.md")

        assert len(entities) == 1
        props = entities[0]["properties"]
        assert props["language"] == "json"
        assert props["code"] == '{"key": "value"}'
        assert props["is_example"] is True
        assert props["is_request"] is False
        assert props["caption"] is None

    def test_xml_code_block(self):
        """XML code block is_example=True."""
        text = "```xml\n<root><child/></root>\n```"
        entities = create_codeblock_entities(text, "spec.md")

        assert len(entities) == 1
        assert entities[0]["properties"]["is_example"] is True
        assert entities[0]["properties"]["language"] == "xml"

    def test_http_code_block(self):
        """HTTP code block: is_request=True, is_example=False."""
        text = "```http\nPOST /v1/payments HTTP/1.1\nContent-Type: application/json\n```"
        entities = create_codeblock_entities(text, "spec.md")

        assert len(entities) == 1
        props = entities[0]["properties"]
        assert props["language"] == "http"
        assert props["is_request"] is True
        assert props["is_example"] is False

    def test_code_block_without_language_tag(self):
        """Code block without language tag defaults to 'plaintext'."""
        text = "```\nsome plain text\n```"
        entities = create_codeblock_entities(text, "spec.md")

        assert len(entities) == 1
        assert entities[0]["properties"]["language"] == "plaintext"
        assert entities[0]["properties"]["is_example"] is False
        assert entities[0]["properties"]["is_request"] is False

    def test_multiple_code_blocks_in_document(self):
        """Multiple code blocks are all extracted."""
        text = (
            "# Section\n\n"
            "```json\n{\"a\": 1}\n```\n\n"
            "Some text.\n\n"
            "```python\nprint('hi')\n```"
        )
        entities = create_codeblock_entities(text, "spec.md")

        assert len(entities) == 2
        languages = {e["properties"]["language"] for e in entities}
        assert languages == {"json", "python"}

    def test_code_block_line_numbers(self):
        """start_line and end_line are accurate (1-based)."""
        text = "line1\nline2\n```python\nx = 1\n```\nline6"
        entities = create_codeblock_entities(text, "spec.md")

        assert len(entities) == 1
        props = entities[0]["properties"]
        assert props["start_line"] == 3
        assert props["end_line"] == 6

    def test_empty_code_block(self):
        """Empty code block is extracted with empty code and line_count=0."""
        text = "```python\n```"
        entities = create_codeblock_entities(text, "spec.md")

        assert len(entities) == 1
        props = entities[0]["properties"]
        assert props["code"] == ""
        assert props["line_count"] == 0

    def test_code_content_preserved_exactly(self):
        """Code content is preserved without modification."""
        code = '{\n  "accountId": "12345",\n  "currency": "EUR"\n}'
        text = f"```json\n{code}\n```"
        entities = create_codeblock_entities(text, "spec.md")

        assert entities[0]["properties"]["code"] == code

    def test_entity_structure(self):
        """CodeBlock entity has required top-level fields."""
        text = "```json\n{}\n```"
        entities = create_codeblock_entities(text, "spec.md")

        entity = entities[0]
        assert entity["type"] == "CodeBlock"
        assert "id" in entity
        assert "name" in entity
        assert "source" in entity

    def test_source_identifier_format(self):
        """Source follows markdown_parser:<file>:codeblock:<line> format."""
        text = "```json\n{}\n```"
        entities = create_codeblock_entities(text, "spec.md")

        assert entities[0]["source"].startswith("markdown_parser:spec.md:codeblock:")

    def test_unclosed_code_block_ignored(self):
        """Unclosed code blocks are not extracted."""
        text = "```python\nprint('hi')"
        entities = create_codeblock_entities(text, "spec.md")

        assert len(entities) == 0

    def test_tilde_fence_supported(self):
        """Triple-tilde fences (~~~) are also extracted."""
        text = "~~~bash\necho hello\n~~~"
        entities = create_codeblock_entities(text, "spec.md")

        assert len(entities) == 1
        assert entities[0]["properties"]["language"] == "bash"

