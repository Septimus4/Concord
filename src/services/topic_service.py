"""Topic processing services used by the API layer."""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from datetime import timedelta
from typing import List, Sequence

from services.graph_repository import GraphRepository

_TOKEN_PATTERN = re.compile(r"[a-zA-Z]{3,}")
_STOP_WORDS = {
    "the",
    "and",
    "for",
    "you",
    "with",
    "that",
    "this",
    "from",
    "have",
    "your",
    "about",
    "project",
    "there",
    "what",
    "when",
    "where",
    "will",
    "would",
    "could",
    "should",
    "into",
    "been",
    "them",
    "they",
    "their",
    "just",
    "like",
    "other",
    "more",
    "some",
    "also",
    "than",
    "each",
    "much",
}


@dataclass
class TopicCandidate:
    name: str
    weights: Counter

    def as_tuple(self) -> tuple[str, dict[str, float]]:
        total = sum(self.weights.values())
        if total == 0:
            return self.name, {self.name: 1.0}
        return self.name, {
            token: round(weight / total, 4) for token, weight in self.weights.items()
        }


class TopicExtractionService:
    """Performs lightweight topic extraction suitable for the MVP."""

    def __init__(self, repository: GraphRepository, *, max_topics: int = 5) -> None:
        self._repository = repository
        self._max_topics = max_topics

    def process_channel_messages(
        self, platform_id: str, channel_id: str, messages: Sequence[str]
    ) -> int:
        cleaned = [self._clean_text(message) for message in messages if message]
        cleaned = [text for text in cleaned if text]
        if not cleaned:
            return 0

        token_counts = Counter()
        for text in cleaned:
            token_counts.update(text.split())

        if not token_counts:
            return 0

        top_tokens = token_counts.most_common(self._max_topics)
        candidates: List[TopicCandidate] = []
        for token, _ in top_tokens:
            related_weights = Counter({token: token_counts[token]})
            candidates.append(TopicCandidate(name=token, weights=related_weights))

        topics_to_store = [candidate.as_tuple() for candidate in candidates]
        self._repository.store_channel_topics(
            platform_id,
            channel_id,
            topics_to_store,
            message_count=len(messages),
        )
        return len(messages)

    @staticmethod
    def _clean_text(message: str) -> str:
        tokens = [
            token.lower()
            for token in _TOKEN_PATTERN.findall(message)
            if token.lower() not in _STOP_WORDS
        ]
        return " ".join(tokens)


class TopicQueryService:
    """Provides read operations for topics and related channels."""

    def __init__(self, repository: GraphRepository) -> None:
        self._repository = repository

    def get_channel_topics(self, platform_id: str, channel_id: str) -> List[str]:
        return self._repository.get_channel_topics(platform_id, channel_id)

    def get_related_channels(
        self, platform_id: str, channel_id: str, max_channels: int
    ) -> List[tuple[str, str, float]]:
        return self._repository.get_related_channels(
            platform_id, channel_id, max_channels
        )


class TrendingService:
    """Computes trending topics based on recent updates."""

    def __init__(self, repository: GraphRepository) -> None:
        self._repository = repository

    def trending_topics(
        self,
        *,
        time_window: timedelta,
        topic_limit: int,
        channel_limit: int,
    ) -> List[tuple[str, List[tuple[str, str, float]]]]:
        return self._repository.get_trending_topics(
            time_window=time_window,
            topic_limit=topic_limit,
            channel_limit=channel_limit,
        )


def parse_time_window(raw: str | None) -> timedelta:
    """Parse a human friendly time window (e.g. ``"24h"`` or ``"7d"``)."""

    if not raw:
        return timedelta(hours=24)

    match = re.match(r"^(\d+)([hdm])$", raw.strip())
    if not match:
        return timedelta(hours=24)

    amount, unit = match.groups()
    value = int(amount)
    if unit == "h":
        return timedelta(hours=value)
    if unit == "d":
        return timedelta(days=value)
    if unit == "m":
        return timedelta(minutes=value)
    return timedelta(hours=24)
