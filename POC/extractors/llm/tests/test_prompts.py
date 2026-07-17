"""Tests for the extraction prompt builder."""
from __future__ import annotations

import json

from ..client.base_client import CompletionRequest
from ..prompts.extractor_prompt import build_request


class TestBuildRequest:
    def test_returns_completion_request(self) -> None:
        req = build_request(text="Payment API", source_id="src-1")
        assert isinstance(req, CompletionRequest)

    def test_has_system_and_user_messages(self) -> None:
        req = build_request(text="text", source_id="src-1")
        roles = [m.role for m in req.messages]
        assert "system" in roles
        assert "user" in roles

    def test_system_message_is_first(self) -> None:
        req = build_request(text="text", source_id="src-1")
        assert req.messages[0].role == "system"

    def test_source_id_in_user_message(self) -> None:
        req = build_request(text="text", source_id="my-source")
        user_msg = next(m for m in req.messages if m.role == "user")
        assert "my-source" in user_msg.content

    def test_source_parser_in_user_message(self) -> None:
        req = build_request(text="text", source_id="s", source_parser="java_parser")
        user_msg = next(m for m in req.messages if m.role == "user")
        assert "java_parser" in user_msg.content

    def test_text_in_user_message(self) -> None:
        req = build_request(text="Payment consent", source_id="s")
        user_msg = next(m for m in req.messages if m.role == "user")
        assert "Payment consent" in user_msg.content

    def test_schema_in_user_message(self) -> None:
        req = build_request(text="x", source_id="s")
        user_msg = next(m for m in req.messages if m.role == "user")
        assert "entities" in user_msg.content
        assert "relationships" in user_msg.content

    def test_temperature_propagated(self) -> None:
        req = build_request(text="x", source_id="s", temperature=0.7)
        assert req.temperature == 0.7

    def test_max_tokens_propagated(self) -> None:
        req = build_request(text="x", source_id="s", max_tokens=512)
        assert req.max_tokens == 512

    def test_unknown_parser_uses_unknown_label(self) -> None:
        req = build_request(text="x", source_id="s", source_parser=None)
        user_msg = next(m for m in req.messages if m.role == "user")
        assert "unknown" in user_msg.content

    def test_messages_are_immutable(self) -> None:
        req = build_request(text="x", source_id="s")
        import pytest
        with pytest.raises((AttributeError, TypeError)):
            req.messages[0].role = "evil"  # type: ignore[misc]
