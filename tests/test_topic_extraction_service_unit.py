# coding: utf-8

from services.graph_repository import InMemoryGraphRepository
from services.topic_service import TopicExtractionService


def test_topic_extraction_no_clean_tokens_returns_zero():
    repo = InMemoryGraphRepository()
    svc = TopicExtractionService(repo)
    count = svc.process_channel_messages(
        "discord",
        "noise",
        ["the and for", "### !!! 123"],
    )
    assert count == 0


def test_topic_extraction_happy_path_stores_topics():
    repo = InMemoryGraphRepository()
    svc = TopicExtractionService(repo, max_topics=3)
    messages = [
        "Graph analytics improve recommendations",
        "Graph modeling and analytics",
    ]
    count = svc.process_channel_messages("discord", "recs", messages)
    assert count == len(messages)
    topics = repo.get_channel_topics("discord", "recs")
    assert topics, "Expected stored topics"
