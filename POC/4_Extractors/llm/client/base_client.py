"""Abstract base and data types for LLM completion clients.

All provider implementations must satisfy the :class:`BaseLLMClient`
interface so that the extraction pipeline is provider-agnostic.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Message:
    """A single turn in a chat-completion exchange."""

    role: str  # "system" | "user" | "assistant"
    content: str


@dataclass(frozen=True)
class CompletionRequest:
    """Typed input for one completion call."""

    messages: tuple[Message, ...]
    temperature: float = 0.1
    max_tokens: int = 2048
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class CompletionResponse:
    """Normalised output from one completion call."""

    content: str
    model: str
    usage: dict[str, int] = field(default_factory=dict)


class LLMClientError(Exception):
    """Raised on non-retryable errors from the LLM provider."""


class BaseLLMClient(ABC):
    """Provider-agnostic interface for chat-completion.

    To add a new provider implement :meth:`complete` and :attr:`model`.
    No other file needs to change.
    """

    @property
    @abstractmethod
    def model(self) -> str:
        """Return the model identifier in use."""

    @abstractmethod
    def complete(self, request: CompletionRequest) -> CompletionResponse:
        """Send *request* to the provider and return the normalised response.

        Raises:
            LLMClientError: on unrecoverable provider errors.
        """
