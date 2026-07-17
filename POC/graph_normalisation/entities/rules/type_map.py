"""TypeMapRule — normalise source-specific entity type labels.

Maps parser-specific type strings to the controlled vocabulary of canonical
types used by the graph normalisation and persistence stages.  The mapping is
extensible — pass a custom ``type_map`` dict to :class:`TypeMapRule`.
"""
from __future__ import annotations

# Default type mapping.
# Keys are lower-cased source type labels; values are canonical type strings.
DEFAULT_TYPE_MAP: dict[str, str] = {
    # ── Java parser ──────────────────────────────────────────────────────────
    "class": "domain_entity",
    "controller": "api_component",
    "restcontroller": "api_component",
    "service": "service_component",
    "repository": "data_component",
    "entity": "domain_entity",
    "interface": "domain_entity",
    "component": "service_component",
    "field": "attribute",
    "method": "operation",
    # ── OpenAPI parser ───────────────────────────────────────────────────────
    "endpoint": "api_operation",
    "schema": "api_schema",
    "property": "attribute",
    # ── spaCy / LLM extractor ────────────────────────────────────────────────
    "concept": "concept",
    "payment_type": "domain_entity",
    "account_type": "domain_entity",
    "regulation": "concept",
    "role": "concept",
    "action": "operation",
    # ── Canonical pass-through (already normalised) ──────────────────────────
    "domain_entity": "domain_entity",
    "api_component": "api_component",
    "service_component": "service_component",
    "data_component": "data_component",
    "api_operation": "api_operation",
    "api_schema": "api_schema",
    "attribute": "attribute",
    "operation": "operation",
}

#: Fallback type when the source type is unknown.
FALLBACK_TYPE = "concept"


class TypeMapRule:
    """Normalise entity type labels to canonical graph types.

    Unlike the name-normalisation rules, this class is not a
    :class:`~rules.base.NormalizationRule` — it normalises *types*, not names.
    It is invoked directly by :class:`~normalizer.EntityNormalizer`.
    """

    def __init__(self, type_map: dict[str, str] | None = None) -> None:
        self._map = type_map if type_map is not None else DEFAULT_TYPE_MAP

    def normalise_type(self, entity_type: str) -> str:
        """Return the canonical type for *entity_type*.

        Falls back to :data:`FALLBACK_TYPE` when the type is unknown.
        """
        return self._map.get(entity_type.lower().strip(), FALLBACK_TYPE)
