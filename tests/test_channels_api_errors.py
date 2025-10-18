# coding: utf-8

from fastapi.testclient import TestClient


def test_post_channel_messages_empty_list_returns_400(client: TestClient):
    response = client.post(
        "/channels/discord/empty/messages",
        json={"messages": []},
    )
    assert response.status_code == 400
    assert "No messages" in response.json()["detail"]


def test_post_channel_messages_no_extractable_content_returns_400(
    client: TestClient,
):
    # Only stop words / numbers -> extractor should produce 0 processed
    response = client.post(
        "/channels/discord/noextract/messages",
        json={"messages": ["the and for", "123 456 789"]},
    )
    assert response.status_code == 400
    assert "extractable" in response.json()["detail"]
