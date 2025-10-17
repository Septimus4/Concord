import re
from typing import Any, List

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
}


def extract_text_segments(data: Any) -> List[str]:
    texts: List[str] = []

    def extract_text(value: Any) -> None:
        if hasattr(value, "model_dump"):
            extract_text(value.model_dump())
        elif isinstance(value, dict):
            for child in value.values():
                extract_text(child)
        elif isinstance(value, list):
            for item in value:
                extract_text(item)
        elif isinstance(value, str):
            texts.append(value)

    extract_text(data)
    return texts


def preprocess_documents(documents: List[str]) -> List[str]:
    """Lightweight document normalisation without external dependencies."""

    processed_docs: List[str] = []
    for doc in documents:
        tokens = [
            token.lower() for token in _TOKEN_PATTERN.findall(doc)
            if token.lower() not in _STOP_WORDS
        ]
        processed_docs.append(" ".join(tokens))
    return processed_docs
