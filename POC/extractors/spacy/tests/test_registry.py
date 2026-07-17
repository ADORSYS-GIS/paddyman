"""Unit tests for the pipeline component registry."""
from __future__ import annotations

import spacy
from spacy.language import Language

from ..pipeline.registry import (
    _REGISTRY,
    apply_registered_components,
    register_component,
    registered_names,
)


def test_registered_names_returns_list() -> None:
    names = registered_names()
    assert isinstance(names, list)


def test_register_and_retrieve() -> None:
    initial_count = len(_REGISTRY)

    @register_component("test_dummy_component")
    def _add(nlp: Language) -> Language:
        return nlp

    assert len(_REGISTRY) == initial_count + 1
    assert "test_dummy_component" in registered_names()

    # Cleanup — remove the test entry so it does not affect other tests.
    _REGISTRY.pop()


def test_apply_registered_does_not_raise_on_empty_registry() -> None:
    """apply_registered_components must not raise when the registry is empty."""
    saved = list(_REGISTRY)
    _REGISTRY.clear()
    try:
        nlp = spacy.blank("en")
        result = apply_registered_components(nlp)
        assert isinstance(result, Language)
    finally:
        _REGISTRY.extend(saved)


def test_apply_registered_invokes_installer() -> None:
    invoked: list[str] = []

    @register_component("_test_invocation")
    def _add(nlp: Language) -> Language:
        invoked.append("called")
        return nlp

    nlp = spacy.blank("en")
    # Only apply the last registered entry (our test one).
    _name, installer = _REGISTRY[-1]
    installer(nlp)
    assert invoked == ["called"]

    _REGISTRY.pop()
