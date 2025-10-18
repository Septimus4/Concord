# coding: utf-8

from typing import Dict, List  # noqa: F401
import importlib
import pkgutil

from concord.server.apis.trending_api_base import BaseTrendingApi
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
from concord.server.models.trending_topics_response import TrendingTopicsResponse

router = APIRouter()

ns_pkg = openapi_server.impl
for _, name, _ in pkgutil.iter_modules(ns_pkg.__path__, ns_pkg.__name__ + "."):
    importlib.import_module(name)


@router.get(
    "/trending/topics",
    responses={
        200: {
            "model": TrendingTopicsResponse,
            "description": "Trending topics list retrieved.",
        },
        400: {"description": "Invalid parameters."},
    },
    tags=["trending"],
    summary="Get trending topics",
    response_model_by_alias=True,
)
async def get_trending_topics(
    time_window: str = Query(None, description="", alias="time_window"),
    topic_limit: int = Query(10, description="", alias="topic_limit"),
    channel_limit: int = Query(5, description="", alias="channel_limit"),
) -> TrendingTopicsResponse:
    """Retrieves trending topics and associated channels for a specified time window."""
    if not BaseTrendingApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseTrendingApi.subclasses[0]().get_trending_topics(
        time_window, topic_limit, channel_limit
    )
