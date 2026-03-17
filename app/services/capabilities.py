from __future__ import annotations

import json
import os
import re
from functools import lru_cache
from typing import Any, Callable

from openai import BadRequestError, OpenAI
from pydantic import ValidationError

from app.core.errors import CapabilityError
from app.schemas import KeywordsInput, SummaryInput

Handler = Callable[[dict[str, Any]], dict[str, Any]]


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


@lru_cache(maxsize=1)
def _get_client() -> OpenAI:
    api_key = os.getenv("AI_API_KEY")
    if not api_key:
        raise CapabilityError(
            code="MODEL_CONFIG_ERROR",
            message="Missing AI_API_KEY in environment.",
            status_code=500,
        )

    base_url = os.getenv("AI_BASE_URL")
    client_kwargs: dict[str, Any] = {"api_key": api_key}
    if base_url:
        client_kwargs["base_url"] = base_url
    return OpenAI(**client_kwargs)


def _get_model_name() -> str:
    return os.getenv("AI_MODEL", "gpt-4o-mini")


def _call_model(system_prompt: str, user_prompt: str, max_output_tokens: int = 300) -> str:
    # Some OpenAI-compatible gateways only support /chat/completions.
    # Try Responses API first, then gracefully fall back on 400 errors.
    try:
        response = _get_client().responses.create(
            model=_get_model_name(),
            input=[
                {
                    "role": "system",
                    "content": [{"type": "input_text", "text": system_prompt}],
                },
                {
                    "role": "user",
                    "content": [{"type": "input_text", "text": user_prompt}],
                },
            ],
            max_output_tokens=max_output_tokens,
            temperature=0.2,
        )
        text = (response.output_text or "").strip()
    except BadRequestError:
        try:
            chat_response = _get_client().chat.completions.create(
                model=_get_model_name(),
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=max_output_tokens,
                temperature=0.2,
            )
            content = chat_response.choices[0].message.content
            text = (content or "").strip()
        except Exception as exc:
            raise CapabilityError(
                code="MODEL_API_ERROR",
                message="Failed to call model API.",
                status_code=502,
                details={"reason": str(exc)},
            ) from exc
    except CapabilityError:
        raise
    except Exception as exc:
        raise CapabilityError(
            code="MODEL_API_ERROR",
            message="Failed to call model API.",
            status_code=502,
            details={"reason": str(exc)},
        ) from exc

    if not text:
        raise CapabilityError(
            code="MODEL_EMPTY_RESPONSE",
            message="Model returned an empty response.",
            status_code=502,
        )
    return text


def _parse_keywords_json(raw_text: str) -> list[str]:
    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```[a-zA-Z0-9]*\n", "", cleaned)
        cleaned = cleaned.removesuffix("```").strip()

    start = cleaned.find("[")
    end = cleaned.rfind("]")
    if start == -1 or end == -1 or end < start:
        raise CapabilityError(
            code="MODEL_INVALID_OUTPUT",
            message="Model output is not a valid JSON array for keywords.",
            status_code=502,
            details={"raw_output": raw_text},
        )

    try:
        payload = json.loads(cleaned[start : end + 1])
    except json.JSONDecodeError as exc:
        raise CapabilityError(
            code="MODEL_INVALID_OUTPUT",
            message="Failed to parse keywords JSON from model output.",
            status_code=502,
            details={"raw_output": raw_text},
        ) from exc

    if not isinstance(payload, list):
        raise CapabilityError(
            code="MODEL_INVALID_OUTPUT",
            message="Keywords output must be a JSON array.",
            status_code=502,
            details={"raw_output": raw_text},
        )

    normalized: list[str] = []
    seen: set[str] = set()
    for item in payload:
        if not isinstance(item, str):
            continue
        keyword = item.strip().lower()
        if not keyword or keyword in seen:
            continue
        seen.add(keyword)
        normalized.append(keyword)

    if not normalized:
        raise CapabilityError(
            code="NO_KEYWORDS_FOUND",
            message="No extractable keywords were found in the model output.",
            status_code=502,
        )

    return normalized


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
    summary = _call_model(
        system_prompt=(
            "You are a concise summarization assistant. "
            "Return only the summary text without any labels."
        ),
        user_prompt=(
            f"Please summarize the following text in at most {parsed.max_length} characters.\n\n"
            f"Text:\n{text}"
        ),
        max_output_tokens=300,
    )
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

    text = _normalize_text(parsed.text)
    raw_keywords = _call_model(
        system_prompt=(
            "You extract keywords from text. "
            "Return only a JSON array of lowercase keywords, no prose."
        ),
        user_prompt=(
            f"Extract the most important {parsed.top_k} keywords from this text. "
            "The response must be a JSON array of strings only.\n\n"
            f"Text:\n{text}"
        ),
        max_output_tokens=200,
    )
    keywords = _parse_keywords_json(raw_keywords)[: parsed.top_k]
    if not keywords:
        raise CapabilityError(
            code="NO_KEYWORDS_FOUND",
            message="No extractable keywords were found in the model output.",
            status_code=502,
        )
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
