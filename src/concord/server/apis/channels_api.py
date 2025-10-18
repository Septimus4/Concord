# coding: utf-8

from typing import Dict, List  # noqa: F401
import importlib
import pkgutil

from concord.server.apis.channels_api_base import BaseChannelsApi
import openapi_server.impl

from fastapi import (  # noqa: F401
    APIRouter,
    Body,
    Cookie,
    Depends,
    Form,
    Header,
    HTTPException,
    Path,
    Query,
    Response,
    Security,
    status,
)

from concord.server.models.extra_models import TokenModel  # noqa: F401
from concord.server.models.channel_messages_request import ChannelMessagesRequest
from concord.server.models.channel_messages_response import ChannelMessagesResponse
from concord.server.models.channel_related_response import ChannelRelatedResponse
from concord.server.models.channel_topics_response import ChannelTopicsResponse

router = APIRouter()

ns_pkg = openapi_server.impl
for _, name, _ in pkgutil.iter_modules(ns_pkg.__path__, ns_pkg.__name__ + "."):
    importlib.import_module(name)


@router.get(
    "/channels/{platform_id}/{channel_id}/topics",
    responses={
        200: {
            "model": ChannelTopicsResponse,
            "description": "Topics for the channel retrieved.",
        },
        404: {"description": "Channel or topics not found."},
    },
    tags=["channels"],
    summary="Get extracted topics for a channel",
    response_model_by_alias=True,
)
async def get_channel_topics(
    platform_id: str = Path(..., description=""),
    channel_id: str = Path(..., description=""),
) -> ChannelTopicsResponse:
    """Returns extracted topics for the specified channel."""
    if not BaseChannelsApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseChannelsApi.subclasses[0]().get_channel_topics(
        platform_id, channel_id
    )


@router.get(
    "/channels/{platform_id}/{channel_id}/related",
    responses={
        200: {
            "model": ChannelRelatedResponse,
            "description": "Related channels list retrieved.",
        },
        404: {"description": "Channel not found."},
    },
    tags=["channels"],
    summary="Retrieve related channels by topic",
    response_model_by_alias=True,
)
async def get_related_channels(
    platform_id: str = Path(..., description=""),
    channel_id: str = Path(..., description=""),
    max_channels: int = Query(10, description="", alias="max_channels"),
) -> ChannelRelatedResponse:
    """Fetches channels discussing topics similar to the specified channel."""
    if not BaseChannelsApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseChannelsApi.subclasses[0]().get_related_channels(
        platform_id, channel_id, max_channels
    )


@router.post(
    "/channels/{platform_id}/{channel_id}/messages",
    responses={
        200: {
            "model": ChannelMessagesResponse,
            "description": "Messages processed successfully.",
        },
        400: {"description": "Invalid input data."},
    },
    tags=["channels"],
    summary="Upload channel messages for processing",
    response_model_by_alias=True,
)
async def post_channel_messages(
    platform_id: str = Path(..., description=""),
    channel_id: str = Path(..., description=""),
    channel_messages_request: ChannelMessagesRequest = Body(None, description=""),
) -> ChannelMessagesResponse:
    """Processes a message feed from a specified channel and updates associated topics."""
    if not BaseChannelsApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseChannelsApi.subclasses[0]().post_channel_messages(
        platform_id, channel_id, channel_messages_request
    )
