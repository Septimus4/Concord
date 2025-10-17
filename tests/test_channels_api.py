# coding: utf-8

from fastapi.testclient import TestClient


def _ingest(client: TestClient, platform_id: str, channel_id: str, messages: list[str]):
    response = client.post(
        f"/channels/{platform_id}/{channel_id}/messages",
        json={"messages": messages},
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["success"] is True
    assert payload["processed_messages"] == len(messages)


def test_get_channel_topics(client: TestClient):
    platform = "discord"
    channel = "dev"
    messages = [
        "We discussed API integration for the developer portal today.",
        "API authentication tokens should be rotated regularly.",
    ]
    _ingest(client, platform, channel, messages)

    response = client.get(f"/channels/{platform}/{channel}/topics")
    assert response.status_code == 200
    body = response.json()
    assert body["topics"], "Expected at least one topic"
    assert body["channel_id"] == channel
    assert body["platform_id"] == platform


def test_get_related_channels(client: TestClient):
    platform = "discord"
    base_channel = "general"
    related_channel = "general-2"

    _ingest(
        client,
        platform,
        base_channel,
        [
            "Graph databases power the recommendation engine.",
            "We need better graph analytics for topics.",
        ],
    )

    _ingest(
        client,
        platform,
        related_channel,
        [
            "Graph analytics provide insights into relationships.",
            "Topic recommendations rely on graph similarity.",
        ],
    )

    response = client.get(
        f"/channels/{platform}/{base_channel}/related",
        params={"max_channels": 5},
    )
    assert response.status_code == 200
    related = response.json()["related_channels"]
    assert related, "Expected a related channel"
    assert related[0]["channel_id"] == related_channel


def test_post_channel_messages(client: TestClient):
    _ingest(
        client,
        "slack",
        "alerts",
        ["Deployment succeeded", "Alerts for CPU usage are nominal"],
    )
