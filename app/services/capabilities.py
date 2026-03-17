from __future__ import annotations

import re
from collections import Counter
from typing import Any, Callable

from pydantic import ValidationError

from app.core.errors import CapabilityError
from app.schemas import KeywordsInput, SummaryInput

Handler = Callable[[dict[str, Any]], dict[str, Any]]

_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "this",
    "to",
    "with",
}


def _normalize_text(text: str) -> str:
    normalized = re.sub(r"\s+", " ", text).strip()
    if not normalized:
        raise CapabilityError(
            code="INVALID_INPUT",
            message="Input text cannot be empty after normalization.",
        )
    return normalized


def _shorten(text: str, max_length: int) -> str:
    if len(text) <= max_length:
        return text
    cutoff = max(0, max_length - 3)
    return text[:cutoff].rstrip() + "..."


def run_text_summary(payload: dict[str, Any]) -> dict[str, Any]:
    try:
        parsed = SummaryInput.model_validate(payload)
    except ValidationError as exc:
        raise CapabilityError(
            code="INVALID_INPUT",
            message="Invalid input for text_summary capability.",
            details={"validation_errors": exc.errors()},
        ) from exc

    text = _normalize_text(parsed.text)
    sentences = [segment.strip() for segment in re.split(r"(?<=[.!?。！？])\s+", text) if segment.strip()]

    if not sentences:
        summary = _shorten(text, parsed.max_length)
        return {"result": summary}

    collected: list[str] = []
    current_length = 0
    for sentence in sentences:
        next_length = current_length + len(sentence) + (1 if collected else 0)
        if next_length > parsed.max_length and collected:
            break
        collected.append(sentence)
        current_length = next_length
        if current_length >= parsed.max_length:
            break

    summary = " ".join(collected) if collected else _shorten(text, parsed.max_length)
    summary = _shorten(summary, parsed.max_length)
    return {"result": summary}


def run_text_keywords(payload: dict[str, Any]) -> dict[str, Any]:
    try:
        parsed = KeywordsInput.model_validate(payload)
    except ValidationError as exc:
        raise CapabilityError(
            code="INVALID_INPUT",
            message="Invalid input for text_keywords capability.",
            details={"validation_errors": exc.errors()},
        ) from exc

    text = _normalize_text(parsed.text.lower())
    tokens = re.findall(r"[a-zA-Z]{2,}", text)
    filtered_tokens = [token for token in tokens if token not in _STOPWORDS]

    if not filtered_tokens:
        raise CapabilityError(
            code="NO_KEYWORDS_FOUND",
            message="No extractable keywords were found in the input text.",
        )

    counter = Counter(filtered_tokens)
    keywords = [token for token, _ in counter.most_common(parsed.top_k)]
    return {"result": keywords}


CAPABILITY_REGISTRY: dict[str, Handler] = {
    "text_summary": run_text_summary,
    "text_keywords": run_text_keywords,
}


def execute_capability(capability: str, payload: dict[str, Any]) -> dict[str, Any]:
    handler = CAPABILITY_REGISTRY.get(capability)
    if handler is None:
        raise CapabilityError(
            code="UNSUPPORTED_CAPABILITY",
            message=f"Unsupported capability: {capability}",
            status_code=404,
            details={"supported_capabilities": sorted(CAPABILITY_REGISTRY)},
        )
    return handler(payload)
