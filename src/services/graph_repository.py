"""Graph repository implementations for Concord."""
from __future__ import annotations

import os
import uuid
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Protocol, Sequence, Tuple, runtime_checkable


@runtime_checkable
class GraphRepository(Protocol):
    """Interface describing operations supported by the graph repositories."""

    def register_platform(
        self,
        platform_id: str,
        *,
        name: str = "",
        description: str = "",
        contact_email: str = "",
        webhook_url: str = "",
        auth_token: str = "",
    ) -> object: ...

    def register_channel(
        self,
        platform_id: str,
        channel_id: str,
        *,
        name: str = "",
        description: str = "",
        language: str = "en",
    ) -> object: ...

    def store_channel_topics(
        self,
        platform_id: str,
        channel_id: str,
        topics: Sequence[tuple[str, Dict[str, float]]],
        *,
        message_count: int,
    ) -> None: ...

    def get_channel_topics(self, platform_id: str, channel_id: str) -> List[str]: ...

    def get_related_channels(
        self, platform_id: str, channel_id: str, limit: int
    ) -> List[tuple[str, str, float]]: ...

    def get_trending_topics(
        self,
        *,
        time_window: timedelta,
        topic_limit: int,
        channel_limit: int,
    ) -> List[tuple[str, List[tuple[str, str, float]]]]: ...

    def clear(self) -> None: ...


# ---------------------------------------------------------------------------
# In-memory repository used for testing and lightweight development
# ---------------------------------------------------------------------------


@dataclass
class TopicRecord:
    """Represents a topic stored in the repository."""

    topic_id: str
    name: str
    keywords: List[str]
    weights: Dict[str, float]
    updated_at: datetime


@dataclass
class ChannelTopicLink:
    """Metadata describing the association between a channel and a topic."""

    topic_id: str
    score: float
    message_count: int
    last_updated: datetime


@dataclass
class ChannelRecord:
    channel_id: str
    platform_id: str
    name: str
    description: str
    language: str = "en"
    activity_score: float = 0.0
    messages_processed: int = 0
    topics: Dict[str, ChannelTopicLink] = field(default_factory=dict)


@dataclass
class PlatformRecord:
    platform_id: str
    name: str = ""
    description: str = ""
    contact_email: str = ""
    webhook_url: str = ""
    auth_token: str = ""
    channels: Dict[str, ChannelRecord] = field(default_factory=dict)


@dataclass
class TopicUpdateRecord:
    topic_id: str
    platform_id: str
    channel_id: str
    timestamp: datetime


class InMemoryGraphRepository(GraphRepository):
    """Stores platforms, channels, topics and updates in memory."""

    def __init__(self) -> None:
        self._platforms: Dict[str, PlatformRecord] = {}
        self._topics: Dict[str, TopicRecord] = {}
        self._topic_updates: List[TopicUpdateRecord] = []
        # Map topic name -> topic_id to keep stable identifiers
        self._topic_lookup: Dict[str, str] = {}

    def register_platform(
        self,
        platform_id: str,
        *,
        name: str = "",
        description: str = "",
        contact_email: str = "",
        webhook_url: str = "",
        auth_token: str = "",
    ) -> PlatformRecord:
        platform = self._platforms.get(platform_id)
        if platform is None:
            platform = PlatformRecord(
                platform_id=platform_id,
                name=name,
                description=description,
                contact_email=contact_email,
                webhook_url=webhook_url,
                auth_token=auth_token,
            )
            self._platforms[platform_id] = platform
        else:
            # Update metadata when re-registering
            platform.name = name or platform.name
            platform.description = description or platform.description
            platform.contact_email = contact_email or platform.contact_email
            platform.webhook_url = webhook_url or platform.webhook_url
            platform.auth_token = auth_token or platform.auth_token
        return platform

    def register_channel(
        self,
        platform_id: str,
        channel_id: str,
        *,
        name: str = "",
        description: str = "",
        language: str = "en",
    ) -> ChannelRecord:
        platform = self.register_platform(platform_id)
        channel = platform.channels.get(channel_id)
        if channel is None:
            channel = ChannelRecord(
                channel_id=channel_id,
                platform_id=platform_id,
                name=name or f"Channel {channel_id}",
                description=description,
                language=language,
            )
            platform.channels[channel_id] = channel
        else:
            channel.name = name or channel.name
            channel.description = description or channel.description
            channel.language = language or channel.language
        return channel

    def store_channel_topics(
        self,
        platform_id: str,
        channel_id: str,
        topics: Sequence[tuple[str, Dict[str, float]]],
        *,
        message_count: int,
    ) -> None:
        """Store topics for a channel and record update metadata."""

        channel = self.register_channel(platform_id, channel_id)
        channel.messages_processed += message_count

        timestamp = datetime.now(timezone.utc)

        for name, weights in topics:
            topic_id = self._topic_lookup.get(name)
            if topic_id is None:
                topic_id = uuid.uuid4().hex
                self._topic_lookup[name] = topic_id
                topic = TopicRecord(
                    topic_id=topic_id,
                    name=name,
                    keywords=list(weights.keys()),
                    weights=dict(weights),
                    updated_at=timestamp,
                )
                self._topics[topic_id] = topic
            else:
                topic = self._topics[topic_id]
                topic.keywords = list(weights.keys())
                topic.weights = dict(weights)
                topic.updated_at = timestamp

            score = sum(weights.values()) if weights else 0.0
            channel.topics[topic_id] = ChannelTopicLink(
                topic_id=topic_id,
                score=score,
                message_count=message_count,
                last_updated=timestamp,
            )

            self._topic_updates.append(
                TopicUpdateRecord(
                    topic_id=topic_id,
                    platform_id=platform_id,
                    channel_id=channel_id,
                    timestamp=timestamp,
                )
            )

    def get_channel_topics(self, platform_id: str, channel_id: str) -> List[str]:
        platform = self._platforms.get(platform_id)
        if platform is None:
            return []
        channel = platform.channels.get(channel_id)
        if channel is None:
            return []
        ordered_links = sorted(
            channel.topics.values(), key=lambda link: link.last_updated, reverse=True
        )
        return [self._topics[link.topic_id].name for link in ordered_links]

    def get_related_channels(
        self, platform_id: str, channel_id: str, limit: int
    ) -> List[tuple[str, str, float]]:
        platform = self._platforms.get(platform_id)
        if platform is None or channel_id not in platform.channels:
            return []

        base_channel = platform.channels[channel_id]
        base_topics = {link.topic_id for link in base_channel.topics.values()}
        if not base_topics:
            return []

        related_scores: List[tuple[str, str, float]] = []
        for other_id, channel in platform.channels.items():
            if other_id == channel_id:
                continue
            other_topics = {link.topic_id for link in channel.topics.values()}
            if not other_topics:
                continue
            intersection = base_topics & other_topics
            union = base_topics | other_topics
            if not union:
                continue
            score = len(intersection) / len(union)
            if score > 0:
                related_scores.append((platform_id, other_id, float(score)))

        related_scores.sort(key=lambda item: item[2], reverse=True)
        return related_scores[:limit]

    def get_trending_topics(
        self,
        *,
        time_window: timedelta,
        topic_limit: int,
        channel_limit: int,
    ) -> List[tuple[str, List[tuple[str, str, float]]]]:
        cutoff = datetime.now(timezone.utc) - time_window
        relevant_updates = [
            update for update in self._topic_updates if update.timestamp >= cutoff
        ]
        if not relevant_updates:
            return []

        topic_counts: Counter[str] = Counter()
        channels_by_topic: Dict[str, Dict[tuple[str, str], int]] = defaultdict(
            lambda: defaultdict(int)
        )
        for update in relevant_updates:
            topic_counts[update.topic_id] += 1
            channels_by_topic[update.topic_id][
                (update.platform_id, update.channel_id)
            ] += 1

        ranked_topics = topic_counts.most_common(topic_limit)
        trending: List[tuple[str, List[tuple[str, str, float]]]] = []
        for topic_id, _ in ranked_topics:
            topic = self._topics.get(topic_id)
            if topic is None:
                continue
            channel_entries: List[tuple[str, str, float]] = []
            counts = channels_by_topic[topic_id]
            sorted_channels = sorted(
                counts.items(), key=lambda item: item[1], reverse=True
            )
            for (platform_key, channel_id), count in sorted_channels[:channel_limit]:
                channel_entries.append((platform_key, channel_id, float(count)))
            trending.append((topic.name, channel_entries))
        return trending

    def clear(self) -> None:
        self._platforms.clear()
        self._topics.clear()
        self._topic_updates.clear()
        self._topic_lookup.clear()


# ---------------------------------------------------------------------------
# Neo4j-backed repository used for persistent deployments
# ---------------------------------------------------------------------------


class Neo4jGraphRepository(GraphRepository):
    """Graph repository backed by Neo4j via neomodel."""

    def __init__(self) -> None:
        try:
            from graph.graph import initialize_neo4j
            from graph.schema import Channel, Platform, Topic, TopicUpdate
            from neomodel import db
            from neomodel.exceptions import DoesNotExist, MultipleNodesReturned
        except ImportError as exc:  # pragma: no cover - requires optional deps
            raise RuntimeError(
                "Neo4j backend requires neomodel and related dependencies"
            ) from exc

        initialize_neo4j()
        self._Channel = Channel
        self._Platform = Platform
        self._Topic = Topic
        self._TopicUpdate = TopicUpdate
        self._DoesNotExist = DoesNotExist
        self._MultipleNodesReturned = MultipleNodesReturned
        self._db = db

    # Utility helpers -----------------------------------------------------
    def _get_or_none(self, node_cls, **kwargs):
        try:
            return node_cls.nodes.get(**kwargs)
        except (self._DoesNotExist, self._MultipleNodesReturned):
            return None

    # Platform and channel management ------------------------------------
    def register_platform(
        self,
        platform_id: str,
        *,
        name: str = "",
        description: str = "",
        contact_email: str = "",
        webhook_url: str = "",
        auth_token: str = "",
    ) -> object:
        platform = self._get_or_none(self._Platform, platform_id=platform_id)
        if platform is None:
            platform = self._Platform(
                platform_id=platform_id,
                name=name or platform_id,
                description=description or "",
                contact_email=contact_email or "",
                webhook_url=webhook_url or "",
                auth_token=auth_token or "",
            ).save()
        else:
            if name:
                platform.name = name
            if description:
                platform.description = description
            if contact_email:
                platform.contact_email = contact_email
            if webhook_url:
                platform.webhook_url = webhook_url
            if auth_token:
                platform.auth_token = auth_token
            platform.save()
        return platform

    def register_channel(
        self,
        platform_id: str,
        channel_id: str,
        *,
        name: str = "",
        description: str = "",
        language: str = "en",
    ) -> object:
        platform = self.register_platform(platform_id)
        channel = self._get_or_none(
            self._Channel, channel_id=channel_id, platform_id=platform_id
        )
        if channel is None:
            channel = self._Channel(
                channel_id=channel_id,
                platform_id=platform_id,
                name=name or f"Channel {channel_id}",
                description=description or "",
                language=language or "en",
                activity_score=0.0,
            ).save()
        else:
            if getattr(channel, "platform_id", None) != platform_id:
                channel.platform_id = platform_id
            if name:
                channel.name = name
            if description:
                channel.description = description
            if language:
                channel.language = language
            channel.save()

        if platform and not platform.channels.is_connected(channel):
            platform.channels.connect(channel)
        return channel

    def store_channel_topics(
        self,
        platform_id: str,
        channel_id: str,
        topics: Sequence[tuple[str, Dict[str, float]]],
        *,
        message_count: int,
    ) -> None:
        channel = self.register_channel(
            platform_id,
            channel_id,
        )
        timestamp = datetime.now(timezone.utc)

        for name, weights in topics:
            keywords = list(weights.keys())
            metadata = {"weights": {k: float(v) for k, v in weights.items()}}
            topic = self._get_or_none(self._Topic, name=name)
            if topic is None:
                topic = self._Topic(
                    name=name,
                    keywords=keywords,
                    bertopic_metadata=metadata,
                ).save()
            else:
                topic.keywords = keywords
                topic.bertopic_metadata = metadata
                topic.updated_at = timestamp
                topic.save()

            score = float(sum(weights.values())) if weights else 0.0
            rel_props = {
                "topic_score": score,
                "keywords_weights": [float(weights[token]) for token in keywords],
                "message_count": int(message_count),
                "last_updated": timestamp,
                "trend": "stable",
            }
            relation = channel.topics.relationship(topic)
            if relation:
                for key, value in rel_props.items():
                    setattr(relation, key, value)
                relation.save()
            else:
                channel.topics.connect(topic, rel_props)

            update = self._TopicUpdate.create_topic_update(keywords, score)
            update.timestamp = timestamp
            update.save()
            update.channel.connect(channel)
            update.topic.connect(topic)

    def get_channel_topics(self, platform_id: str, channel_id: str) -> List[str]:
        channel = self._get_or_none(
            self._Channel, channel_id=channel_id, platform_id=platform_id
        )
        if channel is None:
            return []
        topics = channel.topics.all()
        topics.sort(
            key=lambda topic: getattr(topic, "updated_at", datetime.min),
            reverse=True,
        )
        return [topic.name for topic in topics]

    def get_related_channels(
        self, platform_id: str, channel_id: str, limit: int
    ) -> List[tuple[str, str, float]]:
        channel = self._get_or_none(
            self._Channel, channel_id=channel_id, platform_id=platform_id
        )
        if channel is None:
            return []
        base_topics = {topic.topic_id for topic in channel.topics.all()}
        if not base_topics:
            return []

        related: List[tuple[str, str, float]] = []
        for other in self._Channel.nodes.filter(platform_id=platform_id):
            if other.channel_id == channel_id:
                continue
            other_topics = {topic.topic_id for topic in other.topics.all()}
            if not other_topics:
                continue
            intersection = base_topics & other_topics
            union = base_topics | other_topics
            if not union:
                continue
            score = len(intersection) / len(union)
            if score > 0:
                related.append((platform_id, other.channel_id, float(score)))

        related.sort(key=lambda item: item[2], reverse=True)
        return related[:limit]

    def get_trending_topics(
        self,
        *,
        time_window: timedelta,
        topic_limit: int,
        channel_limit: int,
    ) -> List[tuple[str, List[tuple[str, str, float]]]]:
        cutoff = datetime.now(timezone.utc) - time_window
        updates = self._TopicUpdate.nodes.filter(timestamp__gte=cutoff)
        if not updates:
            return []

        topic_counts: Counter[str] = Counter()
        channels_by_topic: Dict[str, Dict[Tuple[str, str], int]] = defaultdict(
            lambda: defaultdict(int)
        )
        for update in updates:
            topic = update.topic.single()
            channel = update.channel.single()
            if topic is None or channel is None:
                continue
            topic_counts[topic.topic_id] += 1
            key = (channel.platform_id, channel.channel_id)
            channels_by_topic[topic.topic_id][key] += 1

        if not topic_counts:
            return []

        ranked_topics = topic_counts.most_common(topic_limit)
        results: List[tuple[str, List[tuple[str, str, float]]]] = []
        for topic_id, _ in ranked_topics:
            topic = self._get_or_none(self._Topic, topic_id=topic_id)
            if topic is None:
                continue
            channel_entries: List[tuple[str, str, float]] = []
            counts = channels_by_topic.get(topic_id, {})
            sorted_channels = sorted(
                counts.items(), key=lambda item: item[1], reverse=True
            )
            for (platform_key, channel_id_val), count in sorted_channels[:channel_limit]:
                channel_entries.append((platform_key, channel_id_val, float(count)))
            results.append((topic.name, channel_entries))
        return results

    def clear(self) -> None:
        # Avoid destructive behaviour by default. Tests rely on the in-memory backend.
        return None


# ---------------------------------------------------------------------------
# Repository factory
# ---------------------------------------------------------------------------


_repository_singleton: Optional[GraphRepository] = None
_repository_backend: Optional[str] = None


def get_repository() -> GraphRepository:
    """Return a singleton repository instance based on configuration."""

    global _repository_singleton, _repository_backend
    backend = os.getenv("CONCORD_GRAPH_BACKEND", "memory").lower()
    if _repository_singleton is None or _repository_backend != backend:
        if backend == "neo4j":
            _repository_singleton = Neo4jGraphRepository()
        else:
            _repository_singleton = InMemoryGraphRepository()
        _repository_backend = backend
    return _repository_singleton
