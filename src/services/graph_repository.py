"""Simple in-memory graph repository for the MVP."""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Sequence
import uuid


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


class InMemoryGraphRepository:
    """Stores platforms, channels, topics and updates in memory."""

    def __init__(self) -> None:
        self._platforms: Dict[str, PlatformRecord] = {}
        self._topics: Dict[str, TopicRecord] = {}
        self._topic_updates: List[TopicUpdateRecord] = []
        # Map topic name -> topic_id to keep stable identifiers
        self._topic_lookup: Dict[str, str] = {}

    # ------------------------------------------------------------------
    # Platform and channel management
    # ------------------------------------------------------------------
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

    # ------------------------------------------------------------------
    # Topic persistence and queries
    # ------------------------------------------------------------------
    def store_channel_topics(
        self,
        platform_id: str,
        channel_id: str,
        topics: Sequence[tuple[str, Dict[str, float]]],
        *,
        message_count: int,
    ) -> List[TopicRecord]:
        """Store topics for a channel and record update metadata."""

        channel = self.register_channel(platform_id, channel_id)
        channel.messages_processed += message_count

        stored_topics: List[TopicRecord] = []
        timestamp = datetime.utcnow()

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

            stored_topics.append(topic)
            channel.topics[topic_id] = ChannelTopicLink(
                topic_id=topic_id,
                score=sum(weights.values()),
                message_count=message_count,
                last_updated=timestamp,
            )
            self._topic_updates.append(
                TopicUpdateRecord(
                    topic_id=topic.topic_id,
                    platform_id=platform_id,
                    channel_id=channel_id,
                    timestamp=timestamp,
                ))
        return stored_topics

    def get_channel_topics(
        self, platform_id: str, channel_id: str
    ) -> List[str]:
        platform = self._platforms.get(platform_id)
        if platform is None:
            return []
        channel = platform.channels.get(channel_id)
        if channel is None:
            return []
        ordered_links = sorted(
            channel.topics.values(),
            key=lambda link: (link.last_updated, link.score),
            reverse=True,
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
                related_scores.append((platform_id, other_id, score))

        related_scores.sort(key=lambda item: item[2], reverse=True)
        return related_scores[:limit]

    # ------------------------------------------------------------------
    # Trending queries
    # ------------------------------------------------------------------
    def get_trending_topics(
        self,
        *,
        time_window: timedelta,
        topic_limit: int,
        channel_limit: int,
    ) -> List[tuple[str, List[tuple[str, str, float]]]]:
        cutoff = datetime.utcnow() - time_window
        relevant_updates = [
            update for update in self._topic_updates if update.timestamp >= cutoff
        ]
        if not relevant_updates:
            return []

        topic_counts: Counter[str] = Counter()
        channels_by_topic: Dict[str, Dict[tuple[str, str], int]] = defaultdict(
            lambda: defaultdict(int))
        for update in relevant_updates:
            topic_counts[update.topic_id] += 1
            channels_by_topic[update.topic_id][
                (update.platform_id, update.channel_id)] += 1

        ranked_topics = topic_counts.most_common(topic_limit)
        trending: List[tuple[str, List[tuple[str, str, float]]]] = []
        for topic_id, _ in ranked_topics:
            topic = self._topics.get(topic_id)
            if topic is None:
                continue
            channel_entries: List[tuple[str, str, float]] = []
            counts = channels_by_topic[topic_id]
            sorted_channels = sorted(
                counts.items(), key=lambda item: item[1], reverse=True)
            for (platform_id, channel_id), count in sorted_channels[:channel_limit]:
                channel_entries.append((platform_id, channel_id, float(count)))
            trending.append((topic.name, channel_entries))
        return trending

    # ------------------------------------------------------------------
    # Utilities for tests and services
    # ------------------------------------------------------------------
    def clear(self) -> None:
        self._platforms.clear()
        self._topics.clear()
        self._topic_updates.clear()
        self._topic_lookup.clear()


# Singleton repository used by the API implementation
_repository_singleton: Optional[InMemoryGraphRepository] = None


def get_repository() -> InMemoryGraphRepository:
    global _repository_singleton
    if _repository_singleton is None:
        _repository_singleton = InMemoryGraphRepository()
    return _repository_singleton
