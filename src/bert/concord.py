# concord.py
from __future__ import annotations

from typing import Sequence

from services.container import get_topic_extraction_service


def concord(
    topic_model: object,
    channel_id: str,
    platform_id: str,
    documents: Sequence[str],
) -> tuple[int, str | None]:
    """Run the Concord ingestion pipeline for a batch of documents.

    The ``topic_model`` parameter is accepted for backwards compatibility with
    earlier iterations that required a BERTopic instance. The MVP implementation
    relies on :class:`TopicExtractionService` which performs lightweight
    frequency based topic extraction and persists the results through the shared
    repository. The ``topic_model`` is therefore unused but kept to avoid
    breaking the import surface expected by the API layer.
    """

    if not documents:
        return 0, "no documents provided"

    extraction_service = get_topic_extraction_service()
    processed = extraction_service.process_channel_messages(
        platform_id, channel_id, list(documents)
    )
    if processed == 0:
        return 0, "no content after preprocessing"
    return processed, None
