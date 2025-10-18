# coding: utf-8

from services.graph_repository import InMemoryGraphRepository
from services.topic_service import TopicExtractionService


def test_cleaning_and_stopwords_behavior():
    repo = InMemoryGraphRepository()
    svc = TopicExtractionService(repo, max_topics=5)
    # Mixed case stop words and punctuation should be removed; numbers ignored
    messages = [
        "The QUICK brown fox jumps over 123 lazy dogs!!!",
        "And then, the quick fox...",
    ]
    processed = svc.process_channel_messages("p", "c", messages)
    assert processed == len(messages)
    topics = repo.get_channel_topics("p", "c")
    # Expect 'quick' and 'fox' to be among tokens; 'the/and' filtered
    assert "quick" in topics or "fox" in topics


def test_max_topics_respected_when_fewer_tokens():
    repo = InMemoryGraphRepository()
    svc = TopicExtractionService(repo, max_topics=10)
    # Only two distinct tokens -> topics should not exceed that
    processed = svc.process_channel_messages(
        "p",
        "small",
        ["alpha alpha", "beta"],
    )
    assert processed == 2
    topics = repo.get_channel_topics("p", "small")
    assert len(topics) <= 2
