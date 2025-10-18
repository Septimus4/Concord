# coding: utf-8

from datetime import timedelta

from services.graph_repository import InMemoryGraphRepository


def test_inmemory_related_and_trending_and_clear():
    repo = InMemoryGraphRepository()

    # Seed topics across channels
    repo.store_channel_topics(
        "plat", "ch1", [("graph", {"graph": 1.0})], message_count=2
    )
    repo.store_channel_topics(
        "plat", "ch2", [("graph", {"graph": 0.8})], message_count=3
    )
    repo.store_channel_topics(
        "plat", "ch3", [("topic", {"topic": 1.0})], message_count=1
    )

    # Related: ch1 should find ch2 (shared topic), but not ch3
    related = repo.get_related_channels("plat", "ch1", limit=5)
    assert (
        "plat",
        "ch2",
    ) == (related[0][0], related[0][1])
    assert related[0][2] > 0

    # Trending: "graph" should appear with two channels
    trending = repo.get_trending_topics(
        time_window=timedelta(days=1), topic_limit=10, channel_limit=10
    )
    topic_names = [name for name, _ in trending]
    assert "graph" in topic_names

    # Clear: wipe state
    repo.clear()
    assert repo.get_channel_topics("plat", "ch1") == []
