"""Dependency container for Concord services."""
from __future__ import annotations

from services.graph_repository import get_repository
from services.server_service import ServerService
from services.topic_service import (TopicExtractionService, TopicQueryService,
                                    TrendingService)


def get_topic_extraction_service() -> TopicExtractionService:
    repository = get_repository()
    return TopicExtractionService(repository)


def get_topic_query_service() -> TopicQueryService:
    return TopicQueryService(get_repository())


def get_trending_service() -> TrendingService:
    return TrendingService(get_repository())


def get_server_service() -> ServerService:
    return ServerService(get_repository())
