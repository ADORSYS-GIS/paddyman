"""Prompt builder for structured entity and relationship extraction.

The schema is embedded directly in the prompt so the LLM always produces
output that the response parser can validate — no fine-tuning required.
"""
from __future__ import annotations

import json
from typing import Any

from client.base_client import CompletionRequest, Message

# ---------------------------------------------------------------------------
# Embedded response schema — shown to the LLM in every request.
# ---------------------------------------------------------------------------
_RESPONSE_SCHEMA: dict[str, Any] = {
    "entities": [
        {
            "type": "entity",
            "name": "<string>",
            "label": "<DOMAIN_ENTITY | API_ENDPOINT | SCHEMA | OTHER>",
            "properties": {},
        }
    ],
    "relationships": [
        {
            "source": "<entity name>",
            "target": "<entity name>",
            "type": "<RELATIONSHIP_TYPE>",
            "confidence": 0.9,
        }
    ],
}

_SYSTEM_PROMPT = (
    "You are a precise information extraction assistant for a financial API "
    "knowledge graph. Extract named entities and directed relationships from "
    "the provided text. Return ONLY valid JSON matching the exact schema "
    "provided — no markdown, no explanations, no code fences."
)


def build_request(
    text: str,
    source_id: str,
    source_parser: str | None = None,
    temperature: float = 0.1,
    max_tokens: int = 2048,
) -> CompletionRequest:
    """Build a :class:`~client.base_client.CompletionRequest` for extraction.

    Args:
        text:          Parsed document text to extract entities from.
        source_id:     Provenance identifier (used as context in the prompt).
        source_parser: Upstream parser that produced *text*.
        temperature:   Generation temperature passed to the provider.
        max_tokens:    Token budget for the response.

    Returns:
        A ready-to-send :class:`~client.base_client.CompletionRequest`.
    """
    user_content = (
        f"Source: {source_id}\n"
        f"Parser: {source_parser or 'unknown'}\n\n"
        "Return JSON matching this schema:\n"
        f"{json.dumps(_RESPONSE_SCHEMA, indent=2)}\n\n"
        f"TEXT:\n{text}"
    )
    return CompletionRequest(
        messages=(
            Message(role="system", content=_SYSTEM_PROMPT),
            Message(role="user", content=user_content),
        ),
        temperature=temperature,
        max_tokens=max_tokens,
    )
