# coding: utf-8

from fastapi.testclient import TestClient


def test_process_memory_empty_transcript_returns_failure(client: TestClient):
    payload = {
        "createdAt": "2024-01-01T00:00:00Z",
        "structured": {"sentiment": "neutral"},
        "pluginsResponse": [],
        "discarded": False,
        # No transcript and no segments
    }

    response = client.post("/process-memory", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "failure"
    assert body["error"] == "empty_transcript"


def test_process_memory_uses_default_context_when_missing(client: TestClient):
    payload = {
        "createdAt": "2024-01-01T00:00:00Z",
        "structured": {"sentiment": "neutral"},
        "pluginsResponse": [],
        "discarded": False,
        "transcript": "Discussed analytics roadmap and topics.",
    }

    response = client.post("/process-memory", json=payload)
    assert response.status_code == 200
    body = response.json()
    # Should reference default platform/channel ids from resolver
    assert "external-platform/external-channel" in body["result"]
