# coding: utf-8

from fastapi import FastAPI

from bert.pre_process import extract_text_segments
from concord.server.apis.external_integration_api_base import BaseExternalIntegrationApi
from concord.server.models.memory_request import MemoryRequest
from concord.server.models.plugin_response import PluginResponse
from concord.server.models.setup_complete200_response import SetupComplete200Response
from services.container import get_topic_extraction_service, get_topic_query_service

app = FastAPI()


def _resolve_context(memory_request: MemoryRequest) -> tuple[str, str]:
    additional = getattr(memory_request.structured, "additional_data", {}) or {}
    platform_id = additional.get("platform_id", "external-platform")
    channel_id = additional.get("channel_id", "external-channel")
    return platform_id, channel_id


class ExternalIntegrationApiImpl(BaseExternalIntegrationApi):
    async def process_memory(self, memory_request: MemoryRequest) -> PluginResponse:
        messages = extract_text_segments(memory_request.transcript_segments)
        if not messages and memory_request.transcript:
            messages = [memory_request.transcript]

        if not messages:
            return PluginResponse(
                plugin_name="Concord",
                status="failure",
                result="No transcript content provided.",
                error="empty_transcript",
            )

        platform_id, channel_id = _resolve_context(memory_request)
        extraction = get_topic_extraction_service()
        processed = extraction.process_channel_messages(
            platform_id, channel_id, messages
        )
        queries = get_topic_query_service()
        related = queries.get_related_channels(platform_id, channel_id, 3)
        related_summary = (
            ", ".join(f"{channel}" for _, channel, _ in related) if related else "none"
        )

        return PluginResponse(
            plugin_name="Concord",
            result=(
                f"Processed {processed} messages for {platform_id}/{channel_id}."
                f" Related channels: {related_summary}."
            ),
            status="success",
        )

    async def setup_complete(self) -> SetupComplete200Response:
        return SetupComplete200Response()
