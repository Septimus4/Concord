# coding: utf-8

from fastapi import HTTPException

from concord.server.apis.channels_api_base import BaseChannelsApi
from concord.server.models.channel_messages_request import ChannelMessagesRequest
from concord.server.models.channel_messages_response import ChannelMessagesResponse
from concord.server.models.channel_related_response import ChannelRelatedResponse
from concord.server.models.channel_topics_response import ChannelTopicsResponse
from concord.server.models.related_channel import RelatedChannel
from services.container import get_topic_extraction_service, get_topic_query_service


class ChannelsApiImpl(BaseChannelsApi):
    """Concrete implementation backed by the in-memory graph repository."""

    def __init__(self) -> None:
        self._extraction = get_topic_extraction_service()
        self._queries = get_topic_query_service()

    async def get_channel_topics(
        self,
        platform_id: str,
        channel_id: str,
    ) -> ChannelTopicsResponse:
        topics = self._queries.get_channel_topics(platform_id, channel_id)
        return ChannelTopicsResponse(
            platform_id=platform_id,
            channel_id=channel_id,
            topics=topics,
        )

    async def get_related_channels(
        self,
        platform_id: str,
        channel_id: str,
        max_channels: int,
    ) -> ChannelRelatedResponse:
        related = self._queries.get_related_channels(
            platform_id, channel_id, max_channels
        )
        related_models = [
            RelatedChannel(
                platform_id=platform,
                channel_id=channel,
                similarity_score=round(score, 4),
            )
            for platform, channel, score in related
        ]
        return ChannelRelatedResponse(related_channels=related_models)

    async def post_channel_messages(
        self,
        platform_id: str,
        channel_id: str,
        channel_messages_request: ChannelMessagesRequest,
    ) -> ChannelMessagesResponse:
        messages = (
            channel_messages_request.messages if channel_messages_request else None
        )
        if not messages:
            raise HTTPException(
                status_code=400, detail="No messages provided for processing"
            )

        processed_count = self._extraction.process_channel_messages(
            platform_id, channel_id, messages
        )
        if processed_count == 0:
            raise HTTPException(
                status_code=400, detail="Messages did not contain extractable content"
            )

        return ChannelMessagesResponse(success=True, processed_messages=processed_count)
