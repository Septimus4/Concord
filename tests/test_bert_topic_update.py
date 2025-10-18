# coding: utf-8

from datetime import datetime, timezone

import types
import sys


def _install_fake_graph():
    # Fake Topic, TopicUpdate, Channel with minimal behaviour used by update_channel_topics
    class FakeTopic:
        def __init__(
            self, name, topic_embedding=None, topic_score=0.0, updated_at=None
        ):
            self.name = name
            self.topic_embedding = topic_embedding
            self.topic_score = topic_score
            self.updated_at = updated_at or datetime.now(timezone.utc)
            self.topic_id = name
            self.keywords = []

        def save(self):
            return self

        def add_update(self, keywords, score):
            self.keywords = keywords

    class FakeRel:
        def __init__(self):
            self._connected = None

        def connect(self, node):
            self._connected = node

    class FakeTopicUpdate:
        def __init__(self):
            self.topic = FakeRel()

        @classmethod
        def create_topic_update(cls, keywords, score_delta):
            return FakeTopicUpdate()

        def save(self):
            return self

    class FakeChannelNode:
        def __init__(self, channel_id):
            self.channel_id = channel_id

        def associate_with_topic(self, topic_node, score, keywords, count, trend):
            pass

    class FakeChannel:
        class _Nodes:
            def get(self, channel_id=None, **kwargs):
                if channel_id is None:
                    channel_id = kwargs.get("channel_id")
                return FakeChannelNode(channel_id)

        nodes = _Nodes()

    fake_graph_schema = types.ModuleType("graph.schema")
    fake_graph_schema.Topic = FakeTopic
    fake_graph_schema.TopicUpdate = FakeTopicUpdate
    fake_graph_schema.Channel = FakeChannel
    sys.modules["graph.schema"] = fake_graph_schema


def test_topic_update_amplify_new_and_diminish(monkeypatch):
    _install_fake_graph()
    # Install fake sklearn.cosine_similarity
    fake_sklearn = types.ModuleType("sklearn.metrics.pairwise")

    def cosine_similarity(a, b):
        # Return high similarity when embeddings share the same first value
        return [[1.0 if a[0][0] == b[0][0] else 0.0]]

    fake_sklearn.cosine_similarity = cosine_similarity
    sys.modules["sklearn.metrics.pairwise"] = fake_sklearn

    from bert.topic_update import update_channel_topics

    # Existing topics: one similar to new ('match'), one different ('other')
    class Existing:
        def __init__(self, name, emb, score):
            self.name = name
            self.topic_embedding = emb
            self.topic_score = score
            self.keywords = [name]
            self.topic_id = name

        def save(self):
            return self

    channel_topics = [Existing("match", [1, 0], 0.5), Existing("other", [0, 1], 0.5)]
    new_topics = [
        {"name": "match", "embedding": [1, 0], "weight": 0.9},  # amplify existing
        {"name": "new", "embedding": [2, 2], "weight": 0.2},  # create new
    ]

    updates = update_channel_topics(channel_topics, new_topics, channel_id="cid")
    # Should have created at least one TopicUpdate (for amplify and possibly diminish)
    assert isinstance(updates, list)
    assert any(hasattr(u, "topic") for u in updates)
    # Amplified topic score increased
    assert channel_topics[0].topic_score > 0.5
    # Diminish applied to topic not in new_topics ('other')
    assert channel_topics[1].topic_score < 0.5
