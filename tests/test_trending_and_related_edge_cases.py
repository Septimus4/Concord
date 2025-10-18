# coding: utf-8

from datetime import timedelta

from services.graph_repository import InMemoryGraphRepository


def test_trending_no_updates_returns_empty():
    repo = InMemoryGraphRepository()
    trending = repo.get_trending_topics(
        time_window=timedelta(hours=1), topic_limit=5, channel_limit=5
    )
    assert trending == []


def test_trending_respects_topic_and_channel_limits():
    repo = InMemoryGraphRepository()
    # Create 2 topics with multiple channels
    for ch in ("a1", "a2", "a3"):
        repo.store_channel_topics("p", ch, [("alpha", {"alpha": 1})], message_count=1)
    for ch in ("b1", "b2"):
        repo.store_channel_topics("p", ch, [("beta", {"beta": 1})], message_count=1)

    trending = repo.get_trending_topics(
        time_window=timedelta(days=1), topic_limit=1, channel_limit=2
    )
    # Only top 1 topic and top 2 channels under that topic
    assert len(trending) == 1
    name, channels = trending[0]
    assert name in {"alpha", "beta"}
    assert len(channels) == 2


def test_related_channels_ties_and_presence():
    repo = InMemoryGraphRepository()
    # base shares 'x' with c2 and c3 equally
    repo.store_channel_topics("p", "base", [("x", {"x": 1})], message_count=1)
    repo.store_channel_topics("p", "c2", [("x", {"x": 1})], message_count=1)
    repo.store_channel_topics("p", "c3", [("x", {"x": 1})], message_count=1)
    related = repo.get_related_channels("p", "base", limit=5)
    # Order not guaranteed; ensure both present
    channels = {(plat, ch) for plat, ch, _ in related}
    assert ("p", "c2") in channels and ("p", "c3") in channels


def test_channel_topics_ordering_by_update_time():
    repo = InMemoryGraphRepository()
    repo.store_channel_topics("p", "c", [("old", {"old": 1})], message_count=1)
    repo.store_channel_topics("p", "c", [("new", {"new": 1})], message_count=1)
    topics = repo.get_channel_topics("p", "c")
    # Most recently updated topic first
    assert topics[0] == "new"
