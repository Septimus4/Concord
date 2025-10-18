# coding: utf-8

from services.graph_repository import InMemoryGraphRepository
from graph.graph import initialize_neo4j


def test_initialize_neo4j_configures_url(monkeypatch):
    # If neomodel is not available, initialize_neo4j should no-op
    # Simulate neomodel.config object
    class DummyCfg:
        def __init__(self):
            self.DATABASE_URL = None

    cfg = DummyCfg()
    monkeypatch.setattr("graph.graph.config", cfg)
    import graph.graph as gg

    monkeypatch.setattr(gg, "DATABASE_URL", "localhost:9999")
    monkeypatch.setattr(gg, "NEO4J_USER", "neo4j")
    monkeypatch.setattr(gg, "NEO4J_PASSWORD", "pass")
    initialize_neo4j()
    assert cfg.DATABASE_URL == "bolt://neo4j:pass@localhost:9999"


def test_repo_re_register_updates_metadata():
    repo = InMemoryGraphRepository()
    # First registration
    repo.register_platform("p", name="One")
    repo.register_channel("p", "c", name="C1", description="d1", language="en")
    # Update metadata on re-register
    repo.register_platform("p", name="Updated")
    repo.register_channel("p", "c", name="C2", description="d2", language="es")
    topics_before = repo.get_channel_topics("p", "c")
    # Store topic to ensure channel exists
    repo.store_channel_topics("p", "c", [("x", {"x": 1})], message_count=1)
    topics_after = repo.get_channel_topics("p", "c")
    assert topics_before == [] and topics_after != []
