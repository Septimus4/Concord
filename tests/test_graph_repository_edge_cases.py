# coding: utf-8

from services.graph_repository import InMemoryGraphRepository


def test_get_related_channels_when_no_topics_or_missing_channel():
    repo = InMemoryGraphRepository()
    # No platform/channel stored yet
    assert repo.get_related_channels("plat", "missing", limit=5) == []

    # Register channel but store no topics
    repo.register_channel("plat", "empty")
    assert repo.get_related_channels("plat", "empty", limit=5) == []


def test_get_channel_topics_and_limit_behavior():
    repo = InMemoryGraphRepository()
    # Unknown channel returns empty
    assert repo.get_channel_topics("p", "c") == []

    # Store topics for two channels; limit should cap related results
    repo.store_channel_topics("p", "c1", [("a", {"a": 1.0})], message_count=1)
    repo.store_channel_topics("p", "c2", [("a", {"a": 1.0})], message_count=1)
    repo.store_channel_topics("p", "c3", [("a", {"a": 1.0})], message_count=1)
    related = repo.get_related_channels("p", "c1", limit=1)
    assert len(related) == 1


def test_related_channels_no_overlap_and_zero_limit():
    repo = InMemoryGraphRepository()
    repo.store_channel_topics("p", "c1", [("x", {"x": 1.0})], message_count=1)
    repo.store_channel_topics("p", "c2", [("y", {"y": 1.0})], message_count=1)
    # No overlap -> no related
    assert repo.get_related_channels("p", "c1", limit=5) == []
    # limit=0 -> no results even if overlap
    repo.store_channel_topics("p", "c3", [("x", {"x": 1.0})], message_count=1)
    assert repo.get_related_channels("p", "c1", limit=0) == []
