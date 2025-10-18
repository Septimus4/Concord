# coding: utf-8

from fastapi import FastAPI
from fastapi.testclient import TestClient

import concord.server.app_lifespan as al


def test_lifespan_handles_model_and_neo4j_failures(capsys, monkeypatch):
    # Make model initialization raise to exercise fallback print
    def boom_model():
        raise RuntimeError("model boom")

    # Make neo4j initialization raise to exercise fallback print
    def boom_neo4j():
        raise RuntimeError("neo4j boom")

    monkeypatch.setattr(al.ModelManager, "initialize_model", boom_model)
    monkeypatch.setattr(al, "initialize_neo4j", boom_neo4j)

    app = FastAPI(lifespan=al.lifespan)

    @app.get("/ping")
    async def ping():  # noqa: D401
        return {"ok": True}

    # Using context manager triggers startup/shutdown events
    with TestClient(app) as client:
        resp = client.get("/ping")
        assert resp.status_code == 200
        assert resp.json() == {"ok": True}

    captured = capsys.readouterr().out
    assert "Model initialisation failed" in captured
    assert "Neo4j initialisation skipped" in captured
