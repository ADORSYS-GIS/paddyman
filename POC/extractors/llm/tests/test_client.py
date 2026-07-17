"""Tests for the LLM client layer (base types, OpenAI-compat, factory)."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from ..client.base_client import (
    BaseLLMClient,
    CompletionRequest,
    CompletionResponse,
    LLMClientError,
    Message,
)
from ..client.openai_compat_client import OpenAICompatClient


def _make_request() -> CompletionRequest:
    return CompletionRequest(
        messages=(Message(role="system", content="sys"), Message(role="user", content="hi")),
    )


def _mock_sdk_response(content: str = '{"entities":[],"relationships":[]}') -> MagicMock:
    choice = MagicMock()
    choice.message.content = content
    resp = MagicMock()
    resp.choices = [choice]
    resp.model = "glm-4-flash"
    resp.usage.prompt_tokens = 10
    resp.usage.completion_tokens = 20
    resp.usage.total_tokens = 30
    return resp


class TestBaseLLMClientIsAbstract:
    def test_cannot_instantiate_directly(self) -> None:
        with pytest.raises(TypeError):
            BaseLLMClient()  # type: ignore[abstract]


class TestMessageAndRequest:
    def test_message_frozen(self) -> None:
        m = Message(role="user", content="hi")
        with pytest.raises((AttributeError, TypeError)):
            m.role = "system"  # type: ignore[misc]

    def test_completion_request_frozen(self) -> None:
        req = _make_request()
        with pytest.raises((AttributeError, TypeError)):
            req.temperature = 0.9  # type: ignore[misc]


class TestOpenAICompatClient:
    """Tests for :class:`OpenAICompatClient`."""

    def test_model_property(self) -> None:
        with patch("client.openai_compat_client.OpenAICompatClient.__init__", return_value=None):
            client = OpenAICompatClient.__new__(OpenAICompatClient)
            client._model = "test-model"
            assert client.model == "test-model"

    def test_complete_returns_response(self) -> None:
        sdk_resp = _mock_sdk_response()
        with patch("openai.OpenAI") as mock_cls:
            mock_sdk = MagicMock()
            mock_cls.return_value = mock_sdk
            mock_sdk.chat.completions.create.return_value = sdk_resp

            client = OpenAICompatClient(
                base_url="http://test", api_key="key", model="m"
            )
            result = client.complete(_make_request())

        assert isinstance(result, CompletionResponse)
        assert result.content == '{"entities":[],"relationships":[]}'
        assert result.model == "glm-4-flash"
        assert result.usage["total_tokens"] == 30

    def test_complete_raises_llm_client_error_on_exception(self) -> None:
        with patch("openai.OpenAI") as mock_cls:
            mock_sdk = MagicMock()
            mock_cls.return_value = mock_sdk
            mock_sdk.chat.completions.create.side_effect = RuntimeError("timeout")

            client = OpenAICompatClient(
                base_url="http://test", api_key="key", model="m"
            )
            with pytest.raises(LLMClientError, match="timeout"):
                client.complete(_make_request())

    def test_complete_passes_temperature_and_max_tokens(self) -> None:
        sdk_resp = _mock_sdk_response()
        with patch("openai.OpenAI") as mock_cls:
            mock_sdk = MagicMock()
            mock_cls.return_value = mock_sdk
            mock_sdk.chat.completions.create.return_value = sdk_resp

            client = OpenAICompatClient(
                base_url="http://test", api_key="key", model="m"
            )
            req = CompletionRequest(
                messages=(Message(role="user", content="x"),),
                temperature=0.5,
                max_tokens=512,
            )
            client.complete(req)

        call_kwargs = mock_sdk.chat.completions.create.call_args.kwargs
        assert call_kwargs["temperature"] == 0.5
        assert call_kwargs["max_tokens"] == 512


class TestFactoryRequiresApiKey:
    def test_raises_when_api_key_missing(self, monkeypatch) -> None:
        monkeypatch.delenv("LLM_API_KEY", raising=False)
        from shared.config.loader import ConfigurationError
        from client.factory import create_client
        with pytest.raises(ConfigurationError, match="LLM_API_KEY"):
            create_client()

    def test_returns_client_when_api_key_set(self) -> None:
        mock_cfg = MagicMock()
        mock_cfg.llm_api_key = "test-key"
        mock_cfg.llm_base_url = "https://api.test.example.com/v1"
        mock_cfg.llm_model = "test-model"
        mock_cfg.llm_timeout = 30
        # Patch the singleton so create_client()'s local `from shared.config import settings`
        # picks up the mock (frozen dataclass cannot be attribute-patched directly).
        with patch("shared.config.settings", mock_cfg), patch("openai.OpenAI"):
            from client.factory import create_client
            client = create_client()
        assert isinstance(client, BaseLLMClient)
