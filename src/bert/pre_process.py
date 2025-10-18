import re
from functools import lru_cache
from typing import Any, List, Set

_TOKEN_PATTERN = re.compile(r"[a-zA-Z]{3,}")


@lru_cache(maxsize=1)
def _stop_words() -> Set[str]:
    """Return English stopwords using NLTK, downloading if needed.

    Falls back to a minimal set if the corpus is unavailable.
    """
    try:
        from nltk.corpus import stopwords  # type: ignore

        try:
            return set(stopwords.words("english"))
        except LookupError:
            import nltk  # type: ignore

            nltk.download("stopwords", quiet=True)
            return set(stopwords.words("english"))
    except Exception:
        return {"the", "and", "for", "you", "with", "that", "this", "from"}


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

    sw = _stop_words()
    processed_docs: List[str] = []
    for doc in documents:
        tokens = [
            token.lower()
            for token in _TOKEN_PATTERN.findall(doc)
            if token.lower() not in sw
        ]
        processed_docs.append(" ".join(tokens))
    return processed_docs
