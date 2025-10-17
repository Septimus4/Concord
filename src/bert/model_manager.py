# model_manager.py
"""Provides a lazily initialised topic model instance.

The MVP performs topic extraction through :class:`TopicExtractionService`
instead of an expensive BERTopic model. The manager still attempts to load
BERTopic when available to preserve compatibility with future upgrades, but it
falls back to a lightweight placeholder when dependencies are missing.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class _PlaceholderTopicModel:
    """A placeholder object returned when BERTopic is unavailable."""

    reason: str = "placeholder"


class ModelManager:
    _model: Any | None = None

    @classmethod
    def initialize_model(cls) -> None:
        try:
            from bertopic import BERTopic  # type: ignore
            from bertopic.representation import KeyBERTInspired  # type: ignore
            from sentence_transformers import SentenceTransformer  # type: ignore
        except Exception as exc:  # pragma: no cover - import failure path
            cls._model = _PlaceholderTopicModel(reason=str(exc))
            return

        try:
            embedding_model = SentenceTransformer("all-mpnet-base-v2")
            representation_model = KeyBERTInspired()
            cls._model = BERTopic(
                embedding_model=embedding_model,
                verbose=False,
                representation_model=representation_model,
                min_topic_size=2,
                n_gram_range=(1, 2),
            )
        except Exception as exc:  # pragma: no cover - heavy dependency failure
            cls._model = _PlaceholderTopicModel(reason=str(exc))

    @classmethod
    def get_model(cls) -> Any:
        if cls._model is None:
            cls.initialize_model()
        return cls._model
