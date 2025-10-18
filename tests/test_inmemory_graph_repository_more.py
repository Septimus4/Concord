# coding: utf-8

from datetime import datetime, timedelta, timezone


import services.graph_repository as gr
from services.graph_repository import InMemoryGraphRepository


def test_store_channel_topics_updates_existing_topic_keywords_and_weights():
    repo = InMemoryGraphRepository()
    platform, channel = "p", "c"
    # Initial store with keywords alpha, beta
    repo.store_channel_topics(
        platform,
        channel,
        [("topicA", {"alpha": 0.6, "beta": 0.4})],
        message_count=2,
    )
    # Update store with changed keywords gamma, delta
    repo.store_channel_topics(
        platform,
        channel,
        [("topicA", {"gamma": 0.9, "delta": 0.1})],
        message_count=1,
    )

    # Find topic_id from channel links
    ch_record = repo._platforms[platform].channels[channel]
    topic_id = next(iter(ch_record.topics.keys()))
    topic = repo._topics[topic_id]
    assert topic.name == "topicA"
    assert set(topic.keywords) == {"gamma", "delta"}
    assert set(topic.weights.keys()) == {"gamma", "delta"}


def test_related_channels_jaccard_scoring_and_ordering():
    repo = InMemoryGraphRepository()
    p = "p"
    # ch1 topics: t1, t2
    repo.store_channel_topics(
        p, "ch1", [("t1", {"t1": 1}), ("t2", {"t2": 1})], message_count=1
    )
    # ch2 topics: t1
    repo.store_channel_topics(p, "ch2", [("t1", {"t1": 1})], message_count=1)
    # ch3 topics: t1, t2, t3
    repo.store_channel_topics(
        p,
        "ch3",
        [("t1", {"t1": 1}), ("t2", {"t2": 1}), ("t3", {"t3": 1})],
        message_count=1,
    )

    related = repo.get_related_channels(p, "ch1", limit=5)
    # Expect ch3 score = 2/3 = 0.666..., ch2 score = 1/2 = 0.5, ch3 first
    assert related[0][1] == "ch3"
    assert related[1][1] == "ch2"
    assert related[0][2] > related[1][2]


def test_trending_topics_time_window_filtering(monkeypatch):
    repo = InMemoryGraphRepository()

    # Fake datetime.now to control timestamps
    class FakeDateTime:
        CURRENT = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        @classmethod
        def now(cls, tz=None):
            return cls.CURRENT

    monkeypatch.setattr(gr, "datetime", FakeDateTime)

    # Older updates (at t0)
    FakeDateTime.CURRENT = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    repo.store_channel_topics("p", "old", [("old", {"old": 1.0})], message_count=1)

    # Recent updates (at t0 + 90 minutes)
    FakeDateTime.CURRENT = datetime(2025, 1, 1, 13, 30, 0, tzinfo=timezone.utc)
    repo.store_channel_topics("p", "new1", [("new", {"new": 1.0})], message_count=1)
    repo.store_channel_topics("p", "new2", [("new", {"new": 1.0})], message_count=1)

    # Query with 1 hour window should only include 'new' topic updates
    trending = repo.get_trending_topics(
        time_window=timedelta(hours=1), topic_limit=5, channel_limit=5
    )
    assert trending and trending[0][0] == "new"
    # Return to real datetime
    monkeypatch.setattr(gr, "datetime", __import__("datetime").datetime)


def test_clear_resets_topic_lookup_and_ids():
    repo = InMemoryGraphRepository()
    repo.store_channel_topics("p", "c", [("same", {"same": 1.0})], message_count=1)
    ch = repo._platforms["p"].channels["c"]
    topic_id_before = next(iter(ch.topics.keys()))
    # Clear state
    repo.clear()
    repo.store_channel_topics("p", "c", [("same", {"same": 1.0})], message_count=1)
    ch2 = repo._platforms["p"].channels["c"]
    topic_id_after = next(iter(ch2.topics.keys()))
    assert topic_id_before != topic_id_after
