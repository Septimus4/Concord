# coding: utf-8

from fastapi.testclient import TestClient


def test_get_trending_topics(client: TestClient):
    platform = "discord"
    for idx in range(3):
        channel = f"ch-{idx}"
        response = client.post(
            f"/channels/{platform}/{channel}/messages",
            json={
                "messages": [
                    "Topic modeling helps uncover discussions.",
                    "Community updates improve engagement.",
                ]
            },
        )
        assert response.status_code == 200

    response = client.get(
        "/trending/topics",
        params={"time_window": "24h", "topic_limit": 5, "channel_limit": 2},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["topics"], "Expected at least one trending topic"
