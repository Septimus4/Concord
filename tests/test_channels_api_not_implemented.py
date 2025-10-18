# coding: utf-8

from fastapi import FastAPI
from fastapi.testclient import TestClient

from concord.server.apis import channels_api
from concord.server.apis.channels_api_base import BaseChannelsApi


def test_channels_api_endpoints_return_500_when_not_implemented(monkeypatch):
    # Force the BaseChannelsApi registry to be empty to trigger 500 path
    monkeypatch.setattr(BaseChannelsApi, "subclasses", tuple())

    app = FastAPI()
    app.include_router(channels_api.router)
    client = TestClient(app)

    # GET /topics
    r1 = client.get("/channels/plat/ch/topics")
    assert r1.status_code == 500
    assert r1.json()["detail"] == "Not implemented"

    # GET /related
    r2 = client.get("/channels/plat/ch/related")
    assert r2.status_code == 500
    assert r2.json()["detail"] == "Not implemented"

    # POST /messages (no body needed as handler bails out early)
    r3 = client.post("/channels/plat/ch/messages")
    assert r3.status_code == 500
    assert r3.json()["detail"] == "Not implemented"
