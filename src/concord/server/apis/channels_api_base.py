# coding: utf-8

from typing import ClassVar, Dict, List, Tuple  # noqa: F401

from concord.server.models.channel_messages_request import ChannelMessagesRequest
from concord.server.models.channel_messages_response import ChannelMessagesResponse
from concord.server.models.channel_related_response import ChannelRelatedResponse
from concord.server.models.channel_topics_response import ChannelTopicsResponse


class BaseChannelsApi:
    subclasses: ClassVar[Tuple] = ()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        BaseChannelsApi.subclasses = BaseChannelsApi.subclasses + (cls,)

    async def get_channel_topics(
        self,
        platform_id: str,
        channel_id: str,
    ) -> ChannelTopicsResponse:
        """Returns extracted topics for the specified channel."""
        ...

    async def get_related_channels(
        self,
        platform_id: str,
        channel_id: str,
        max_channels: int,
    ) -> ChannelRelatedResponse:
        """Fetches channels discussing topics similar to the specified channel."""
        ...

    async def post_channel_messages(
        self,
        platform_id: str,
        channel_id: str,
        channel_messages_request: ChannelMessagesRequest,
    ) -> ChannelMessagesResponse:
        """Processes a message feed from a specified channel and updates associated topics."""
        ...
