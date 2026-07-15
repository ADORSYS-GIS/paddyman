"""Shared test doubles and fixtures for Neo4j writer tests."""
from __future__ import annotations

import sys
from pathlib import Path
from uuid import uuid5, NAMESPACE_URL

import pytest

_HERE = Path(__file__).resolve().parent
_NEO4J_ROOT = _HERE.parent
_GRAPH_ROOT = _NEO4J_ROOT.parent
_POC_ROOT = _HERE.parents[2]

for _p in (str(_POC_ROOT), str(_GRAPH_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from entities.models import CanonicalEntity, EntitySource
from shared.models import Entity, Relationship


class FakeTx:
    def __init__(self) -> None:
        self.runs: list[tuple[str, dict]] = []

    async def run(self, query: str, **params) -> None:  # type: ignore[no-untyped-def]
        self.runs.append((query, params))


class FakeSession:
    def __init__(self, tx: FakeTx, fail: bool = False) -> None:
        self.tx = tx
        self.fail = fail
        self.closed = False
        self.write_count = 0

    async def __aenter__(self) -> "FakeSession":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:  # type: ignore[no-untyped-def]
        self.closed = True

    async def execute_write(self, callback, *args):  # type: ignore[no-untyped-def]
        self.write_count += 1
        if self.fail:
            raise RuntimeError("transaction failed")
        return await callback(self.tx, *args)


class FakeDriver:
    def __init__(self, session: FakeSession) -> None:
        self._session = session
        self.closed = False
        self.database: str | None = None
        self.verified = False

    def session(self, database: str):  # type: ignore[no-untyped-def]
        self.database = database
        return self._session

    async def verify_connectivity(self) -> None:
        self.verified = True

    async def close(self) -> None:
        self.closed = True


@pytest.fixture()
def fake_tx() -> FakeTx:
    return FakeTx()


@pytest.fixture()
def canonical_entity() -> CanonicalEntity:
    raw = Entity(type="controller", name="PaymentController", source="java_parser")
    source = EntitySource(
        source_parser="java_parser",
        original_name="PaymentController",
        repository="xs2a",
        module="impl",
        document="payments.md",
        file_path="PaymentController.java",
        version_tag="v2",
        confidence=0.9,
        entity_ref=raw,
    )
    return CanonicalEntity(
        id="PaymentController",
        type="api_component",
        aliases=["PaymentController"],
        sources=[source],
        confidence=0.9,
    )


@pytest.fixture()
def normalized_relationship() -> Relationship:
    return Relationship(
        id=uuid5(NAMESPACE_URL, "rel"),
        source_entity_id=uuid5(NAMESPACE_URL, "source"),
        target_entity_id=uuid5(NAMESPACE_URL, "target"),
        type="USES",
        confidence=0.8,
        properties={
            "source": "PaymentController",
            "target": "PaymentService",
            "original_type": "CALLS",
            "source_parser": "java_parser",
            "repository": "xs2a",
            "provenance": [{"source_parser": "java_parser"}],
        },
    )