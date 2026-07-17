"""Pipeline component registry.

The registry decouples component authors from the pipeline builder.  New
Phase 4 extractors register themselves here so that
:func:`~pipeline.build_pipeline` can discover and install them without
any changes to existing code.

Usage — registering a new component
------------------------------------

In your extractor module::

    from spacy.pipeline.registry import register_component

    @register_component("my_extractor", after="domain_entity_ruler")
    def add_my_extractor(nlp):
        nlp.add_pipe("my_extractor_component")
        return nlp

The component will be added to every pipeline built after registration.

Usage — building the pipeline
------------------------------

:func:`~pipeline.pipeline.build_pipeline` calls
:func:`apply_registered_components` automatically.
"""
from __future__ import annotations

import logging
from typing import Callable

from spacy.language import Language

logger = logging.getLogger(__name__)

# Registry: list of (name, installer_fn) pairs in insertion order.
_REGISTRY: list[tuple[str, Callable[[Language], Language]]] = []


def register_component(
    name: str,
) -> Callable[[Callable[[Language], Language]], Callable[[Language], Language]]:
    """Decorator — register a pipeline-component installer function.

    Args:
        name: Human-readable identifier used in log messages.

    Returns:
        A decorator that registers the wrapped function and returns it
        unchanged.

    Example::

        @register_component("endpoint_extractor")
        def _add(nlp):
            nlp.add_pipe("my_endpoint_extractor")
            return nlp
    """

    def decorator(
        fn: Callable[[Language], Language],
    ) -> Callable[[Language], Language]:
        _REGISTRY.append((name, fn))
        logger.debug("Pipeline component registered: '%s'", name)
        return fn

    return decorator


def apply_registered_components(nlp: Language) -> Language:
    """Apply every registered component installer to *nlp* in order.

    Args:
        nlp: spaCy Language pipeline under construction.

    Returns:
        The mutated *nlp* instance.
    """
    for name, installer in _REGISTRY:
        try:
            nlp = installer(nlp)
            logger.debug("Applied registered component: '%s'", name)
        except Exception as exc:  # noqa: BLE001
            logger.error(
                "Failed to apply registered component '%s': %s", name, exc
            )
            raise

    return nlp


def registered_names() -> list[str]:
    """Return the names of all currently registered components."""
    return [name for name, _ in _REGISTRY]
