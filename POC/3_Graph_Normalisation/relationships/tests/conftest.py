"""Shared fixtures for relationship normalisation tests."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

_HERE = Path(__file__).resolve().parent
_REL_ROOT = _HERE.parent
_GRAPH_ROOT = _REL_ROOT.parent
_POC_ROOT = _HERE.parents[2]

for _p in (str(_POC_ROOT), str(_GRAPH_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from entities.models import CanonicalEntity


@pytest.fixture()
def canonical_entities() -> list[CanonicalEntity]:
    return [
        CanonicalEntity(
            id="PaymentController",
            type="api_component",
            aliases=["PaymentController"],
        ),
        CanonicalEntity(
            id="PaymentService",
            type="service_component",
            aliases=["PaymentService"],
        ),
        CanonicalEntity(
            id="PaymentRequest",
            type="api_schema",
            aliases=["PaymentDTO", "Payment Initiation Request"],
        ),
        CanonicalEntity(
            id="PaymentDocumentation",
            type="concept",
            aliases=["Payment Initiation"],
        ),
    ]