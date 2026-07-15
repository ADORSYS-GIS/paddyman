"""Tests for async Neo4j entity and relationship writers."""
from __future__ import annotations

import asyncio

import pytest

from neo4j.client import Neo4jClient
from neo4j.config import Neo4jSettings
from neo4j.entity_writer import EntityWriter
from neo4j.graph_writer import GraphWriter
from neo4j.relationship_writer import RelationshipWriter
from neo4j.session import Neo4jSessionManager

from conftest import FakeDriver, FakeSession, FakeTx


def _client(session: FakeSession) -> Neo4jClient:
    config = Neo4jSettings("bolt://db:7687", "neo4j", "secret", "graph")
    return Neo4jClient(config=config, driver_factory=lambda uri, auth: FakeDriver(session))


def test_entity_merge(canonical_entity, fake_tx: FakeTx) -> None:  # type: ignore[no-untyped-def]
    writer = EntityWriter(Neo4jSessionManager(_client(FakeSession(fake_tx))))
    count = asyncio.run(writer.write_entities([canonical_entity]))
    query, params = fake_tx.runs[0]
    assert count == 1
    assert "MERGE (e:Entity {id: $id})" in query
    assert params["id"] == "PaymentController"
    assert params["properties"]["aliases"] == ["PaymentController"]
    assert params["properties"]["repository"] == ["xs2a"]
    assert "provenance" in params["properties"]


def test_relationship_merge(normalized_relationship, fake_tx: FakeTx) -> None:  # type: ignore[no-untyped-def]
    writer = RelationshipWriter(Neo4jSessionManager(_client(FakeSession(fake_tx))))
    count = asyncio.run(writer.write_relationships([normalized_relationship]))
    query, params = fake_tx.runs[0]
    assert count == 1
    assert "MERGE (source)-[r:RELATIONSHIP {id: $id}]->(target)" in query
    assert params["source_id"] == "PaymentController"
    assert params["target_id"] == "PaymentService"
    assert params["properties"]["original_type"] == "CALLS"
    assert isinstance(params["properties"]["provenance"], str)


def test_duplicate_writes_use_merge(canonical_entity, fake_tx: FakeTx) -> None:  # type: ignore[no-untyped-def]
    writer = EntityWriter(Neo4jSessionManager(_client(FakeSession(fake_tx))))
    asyncio.run(writer.write_entities([canonical_entity, canonical_entity]))
    assert len(fake_tx.runs) == 2
    assert all("MERGE" in query for query, _ in fake_tx.runs)


def test_graph_writer_writes_entities_before_relationships(
    canonical_entity, normalized_relationship, fake_tx: FakeTx  # type: ignore[no-untyped-def]
) -> None:
    graph = GraphWriter(_client(FakeSession(fake_tx)))
    result = asyncio.run(graph.write_graph([canonical_entity], [normalized_relationship]))
    queries = [query for query, _ in fake_tx.runs]
    assert result == {"entities": 1, "relationships": 1}
    assert "MERGE (e:Entity" in queries[0]
    assert "MERGE (source)-[r:RELATIONSHIP" in queries[1]


def test_transaction_failure_is_propagated(canonical_entity, fake_tx: FakeTx) -> None:  # type: ignore[no-untyped-def]
    writer = EntityWriter(Neo4jSessionManager(_client(FakeSession(fake_tx, fail=True))))
    with pytest.raises(RuntimeError, match="transaction failed"):
        asyncio.run(writer.write_entities([canonical_entity]))