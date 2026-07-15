"""Tests for Neo4j constraint and index managers."""
from __future__ import annotations

import asyncio

from neo4j.client import Neo4jClient
from neo4j.config import Neo4jSettings
from neo4j.constraints import ConstraintManager
from neo4j.indexes import IndexManager
from neo4j.session import Neo4jSessionManager

from conftest import FakeDriver, FakeSession, FakeTx


def _sessions(session: FakeSession) -> Neo4jSessionManager:
    config = Neo4jSettings("bolt://db:7687", "neo4j", "secret", "graph")
    client = Neo4jClient(config=config, driver_factory=lambda uri, auth: FakeDriver(session))
    return Neo4jSessionManager(client)


def test_constraint_creation(fake_tx: FakeTx) -> None:
    asyncio.run(ConstraintManager(_sessions(FakeSession(fake_tx))).create_constraints())
    queries = [query for query, _ in fake_tx.runs]
    assert any("CREATE CONSTRAINT entity_id_unique IF NOT EXISTS" in q for q in queries)
    assert any("CREATE CONSTRAINT entity_canonical_id_unique IF NOT EXISTS" in q for q in queries)


def test_index_creation(fake_tx: FakeTx) -> None:
    asyncio.run(IndexManager(_sessions(FakeSession(fake_tx))).create_indexes())
    queries = [query for query, _ in fake_tx.runs]
    assert any("CREATE INDEX entity_id_index IF NOT EXISTS" in q for q in queries)
    assert any("CREATE INDEX entity_type_index IF NOT EXISTS" in q for q in queries)
    assert any("CREATE INDEX entity_repository_index IF NOT EXISTS" in q for q in queries)
    assert any("CREATE INDEX entity_module_index IF NOT EXISTS" in q for q in queries)