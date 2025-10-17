import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from concord.server.main import app as application
from services.graph_repository import get_repository


@pytest.fixture
def app() -> FastAPI:
    application.dependency_overrides = {}
    get_repository().clear()

    return application


@pytest.fixture
def client(app) -> TestClient:
    return TestClient(app)
