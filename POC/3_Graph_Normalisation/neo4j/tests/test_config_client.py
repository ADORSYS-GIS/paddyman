"""Tests for Neo4j configuration loading and client initialization."""
from __future__ import annotations

import asyncio
from types import SimpleNamespace

from neo4j.client import Neo4jClient
from neo4j.config import Neo4jSettings

from conftest import FakeDriver, FakeSession, FakeTx


def test_configuration_loading_from_shared_settings() -> None:
    settings = SimpleNamespace(
        neo4j_uri="bolt://db:7687",
        neo4j_username="neo4j",
        neo4j_password="secret",
        neo4j_database="graph",
    )
    config = Neo4jSettings.from_shared_config(settings)
    assert config.uri == "bolt://db:7687"
    assert config.username == "neo4j"
    assert config.password == "secret"
    assert config.database == "graph"


def test_configuration_loading_uses_shared_env_loader(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    values = {
        "NEO4J_URI": "bolt://env:7687",
        "NEO4J_USERNAME": "env-user",
        "NEO4J_PASSWORD": "env-pass",
        "NEO4J_DATABASE": "env-db",
    }
    monkeypatch.setattr("neo4j.config.require_env", lambda name: values[name])
    config = Neo4jSettings.from_shared_config(SimpleNamespace())
    assert config.uri == "bolt://env:7687"
    assert config.database == "env-db"


def test_client_initialization_and_lifecycle(fake_tx: FakeTx) -> None:
    session = FakeSession(fake_tx)
    driver = FakeDriver(session)
    config = Neo4jSettings("bolt://db:7687", "neo4j", "secret", "graph")
    client = Neo4jClient(config=config, driver_factory=lambda uri, auth: driver)

    assert client.driver is driver
    assert client.session() is session
    assert driver.database == "graph"
    asyncio.run(client.verify_connectivity())
    asyncio.run(client.close())
    assert driver.verified is True
    assert driver.closed is True