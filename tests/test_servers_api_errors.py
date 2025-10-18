# coding: utf-8

from fastapi.testclient import TestClient


def test_register_server_missing_name_returns_400(client: TestClient):
    payload = {
        "platform": "discord",
    }
    r = client.post("/servers/register", json=payload)
    assert r.status_code == 400
    assert "name" in r.json()["detail"].lower()


def test_register_server_missing_platform_returns_400(client: TestClient):
    payload = {
        "name": "Guild",
    }
    r = client.post("/servers/register", json=payload)
    assert r.status_code == 400
    assert "platform" in r.json()["detail"].lower()
