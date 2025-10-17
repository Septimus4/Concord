# coding: utf-8

from fastapi.testclient import TestClient


def test_process_memory(client: TestClient):
    payload = {
        "createdAt": "2024-01-01T00:00:00Z",
        "structured": {
            "sentiment": "neutral",
            "additionalData": {
                "platform_id": "omi",
                "channel_id": "daily-sync",
            },
        },
        "pluginsResponse": [],
        "discarded": False,
        "transcriptSegments": [
            {
                "text": "We covered the graph analytics backlog and topic extraction goals.",
                "speaker": "Alex",
                "speaker_id": 1,
                "is_user": True,
                "start": 0,
                "end": 5,
            }
        ],
    }

    response = client.post("/process-memory", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert "Processed" in body["result"]


def test_setup_complete(client: TestClient):
    response = client.get("/setup-complete")
    assert response.status_code == 200
