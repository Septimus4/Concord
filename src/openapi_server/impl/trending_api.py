# coding: utf-8

from concord.server.apis.trending_api_base import BaseTrendingApi
from concord.server.models.related_channel import RelatedChannel
from concord.server.models.trending_topic import TrendingTopic
from concord.server.models.trending_topics_response import TrendingTopicsResponse
from services.container import get_trending_service
from services.topic_service import parse_time_window


class TrendingApiImpl(BaseTrendingApi):
    """Trending API backed by the in-memory repository."""

    def __init__(self) -> None:
        self._service = get_trending_service()

    async def get_trending_topics(
        self,
        time_window: str | None,
        topic_limit: int,
        channel_limit: int,
    ) -> TrendingTopicsResponse:
        window = parse_time_window(time_window)
        trending = self._service.trending_topics(
            time_window=window,
            topic_limit=topic_limit,
            channel_limit=channel_limit,
        )

        topics = [
            TrendingTopic(
                topic=topic_name,
                channels=[
                    RelatedChannel(
                        platform_id=platform_id,
                        channel_id=channel_id,
                        similarity_score=round(score, 4),
                    )
                    for platform_id, channel_id, score in channel_entries
                ],
            )
            for topic_name, channel_entries in trending
        ]
        return TrendingTopicsResponse(time_window=time_window, topics=topics)
