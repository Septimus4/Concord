# coding: utf-8

import bert.concord as concord_module
from services.graph_repository import InMemoryGraphRepository
from services.topic_service import TopicExtractionService


def test_concord_no_documents_returns_error_message(monkeypatch):
    processed, err = concord_module.concord(object(), "ch", "plat", [])
    assert processed == 0 and err == "no documents provided"


def test_concord_runs_extraction_pipeline(monkeypatch):
    # Use a fresh in-memory repo and inject a service that uses it
    repo = InMemoryGraphRepository()

    def _get_svc():
        return TopicExtractionService(repo)

    monkeypatch.setattr(concord_module, "get_topic_extraction_service", _get_svc)

    processed, err = concord_module.concord(
        object(), "chx", "platx", ["alpha beta", "alpha"]
    )
    assert err is None
    assert processed == 2
    assert repo.get_channel_topics("platx", "chx")
