from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class CapabilityRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    capability: str = Field(min_length=1, max_length=64)
    input: dict[str, Any]
    request_id: str | None = Field(default=None, max_length=128)


class SummaryInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str = Field(min_length=1, max_length=20000)
    max_length: int = Field(default=120, ge=20, le=1000)


class KeywordsInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str = Field(min_length=1, max_length=20000)
    top_k: int = Field(default=5, ge=1, le=20)


class ErrorBody(BaseModel):
    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class ResponseMeta(BaseModel):
    request_id: str
    capability: str
    elapsed_ms: int


class SuccessResponse(BaseModel):
    ok: bool = True
    data: dict[str, Any]
    meta: ResponseMeta


class ErrorResponse(BaseModel):
    ok: bool = False
    error: ErrorBody
    meta: ResponseMeta
