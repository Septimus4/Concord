# coding: utf-8

from fastapi.testclient import TestClient

def test_register_server(client: TestClient):
    payload = {
        "webhook_url": "https://example.com/webhook",
        "name": "Open Source Guild",
        "description": "A community for open-source maintainers",
        "auth_token": "secret",
        "platform": "discord",
        "contact_email": "ops@example.com",
    }

    response = client.post("/servers/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["platform_id"] == "discord:open-source-guild"
    assert data["status"] == "registered"
