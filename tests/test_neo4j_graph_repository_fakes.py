# coding: utf-8

from datetime import datetime, timedelta, timezone

from services.graph_repository import Neo4jGraphRepository


def test_neo4j_graph_repository_core_paths():
    # Build a repository instance without running its real __init__
    repo = Neo4jGraphRepository.__new__(Neo4jGraphRepository)

    # In-memory stores for fakes
    platforms = {}
    channels = {}
    topics = {}
    topic_updates = []

    # Fakes --------------------------------------------------------------
    class RelationFake:
        def __init__(self):
            self.saved = False

        def save(self):
            self.saved = True
            return self

    class PlatformFake:
        def __init__(
            self, platform_id, name, description, contact_email, webhook_url, auth_token
        ):
            self.platform_id = platform_id
            self.name = name
            self.description = description
            self.contact_email = contact_email
            self.webhook_url = webhook_url
            self.auth_token = auth_token
            self._connected = set()

            class ChannelsRel:
                def __init__(self, outer):
                    self._outer = outer

                def is_connected(self, channel):
                    return channel.channel_id in self._outer._connected

                def connect(self, channel):
                    self._outer._connected.add(channel.channel_id)

            self.channels = ChannelsRel(self)

        @classmethod
        def nodes(cls):  # type: ignore[return-type]
            return cls

        def save(self):
            platforms[self.platform_id] = self
            return self

    class TopicsRel:
        def __init__(self, channel):
            self._channel = channel
            self._rels = {}  # topic_id -> RelationFake

        def relationship(self, topic):
            return self._rels.get(topic.topic_id)

        def connect(self, topic, rel_props):
            rel = RelationFake()
            for k, v in rel_props.items():
                setattr(rel, k, v)
            self._rels[topic.topic_id] = rel

        def all(self):
            return [topics[tid] for tid in self._rels.keys()]

    class ChannelFake:
        class _Nodes:
            @staticmethod
            def filter(platform_id=None, **kwargs):
                return [
                    c
                    for (p, _), c in channels.items()
                    if platform_id is None or p == platform_id
                ]

        nodes = _Nodes()

        def __init__(
            self,
            channel_id,
            platform_id,
            name,
            description,
            language,
            activity_score=0.0,
        ):
            self.channel_id = channel_id
            self.platform_id = platform_id
            self.name = name
            self.description = description
            self.language = language
            self.activity_score = activity_score
            self.topics = TopicsRel(self)

        def save(self):
            channels[(self.platform_id, self.channel_id)] = self
            return self

    class TopicFake:
        def __init__(self, name, keywords, bertopic_metadata):
            self.name = name
            self.keywords = keywords
            self.bertopic_metadata = bertopic_metadata
            self.updated_at = datetime.now(timezone.utc)
            self.topic_id = name

        @classmethod
        def nodes(cls):  # type: ignore[return-type]
            return cls

        def save(self):
            topics[self.topic_id] = self
            return self

    class Rel:
        def __init__(self, target):
            self._target = target

        def connect(self, target):
            self._target = target

    class TopicUpdateFake:
        def __init__(self, keywords, score):
            self.timestamp = datetime.now(timezone.utc)
            self._topic = None
            self._channel = None

            class _Rel:
                def __init__(self, parent, attr):
                    self._parent = parent
                    self._attr = attr

                def connect(self, obj):
                    setattr(self._parent, self._attr, obj)

                def single(self):
                    return getattr(self._parent, self._attr)

            self.topic = _Rel(self, "_topic")
            self.channel = _Rel(self, "_channel")

        @classmethod
        def create_topic_update(cls, keywords, score):
            inst = TopicUpdateFake(keywords, score)
            topic_updates.append(inst)
            return inst

        def save(self):
            return self

        class _Nodes:
            @staticmethod
            def filter(timestamp__gte):
                return [u for u in topic_updates if u.timestamp >= timestamp__gte]

        nodes = _Nodes()

    # Wire fakes into repo instance attributes
    repo._Platform = PlatformFake
    repo._Channel = ChannelFake
    repo._Topic = TopicFake
    repo._TopicUpdate = TopicUpdateFake
    repo._DoesNotExist = Exception
    repo._MultipleNodesReturned = Exception

    # Override _get_or_none to use our in-memory stores
    def _get_or_none(node_cls, **kwargs):
        if node_cls is PlatformFake:
            return platforms.get(kwargs.get("platform_id"))
        if node_cls is ChannelFake:
            return channels.get((kwargs.get("platform_id"), kwargs.get("channel_id")))
        if node_cls is TopicFake:
            # lookup by name or id
            name = kwargs.get("name")
            tid = kwargs.get("topic_id") or name
            return topics.get(tid)
        return None

    repo._get_or_none = _get_or_none  # type: ignore[method-assign]

    # Exercise: register/create flows
    repo.register_platform("plat", name="P1")
    repo.register_channel("plat", "chan", name="C1", description="d", language="en")

    # Store topics: create then update existing
    repo.store_channel_topics(
        "plat",
        "chan",
        [("alpha", {"a": 0.7, "b": 0.3}), ("beta", {"b": 1.0})],
        message_count=3,
    )

    repo.store_channel_topics(
        "plat",
        "chan",
        [("alpha", {"a": 1.0})],  # update existing topic and relation
        message_count=1,
    )

    # get_channel_topics path
    names = repo.get_channel_topics("plat", "chan")
    assert set(names) >= {"alpha", "beta"}

    # related_channels path with another channel
    repo.register_channel("plat", "chan2", name="C2")
    repo.store_channel_topics("plat", "chan2", [("alpha", {"a": 1.0})], message_count=1)
    rel = repo.get_related_channels("plat", "chan", limit=5)
    assert rel and rel[0][1] == "chan2"

    # trending topics path
    result = repo.get_trending_topics(
        time_window=timedelta(days=1), topic_limit=5, channel_limit=5
    )
    assert result and any(name == "alpha" for name, _ in result)
