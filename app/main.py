from __future__ import annotations

import logging
from time import perf_counter
from uuid import uuid4

from dotenv import load_dotenv
from fastapi import Body, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.errors import CapabilityError
from app.schemas import CapabilityRequest, ErrorResponse, ResponseMeta, SuccessResponse
from app.services.capabilities import execute_capability

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("ai-capability-service")

load_dotenv()

app = FastAPI(
    title="AI Capability Service",
    version="1.0.0",
    description="A minimal unified capability service for AI-style backend calls.",
)


def _build_meta(request_id: str, capability: str, started_at: float) -> ResponseMeta:
    elapsed_ms = int((perf_counter() - started_at) * 1000)
    return ResponseMeta(
        request_id=request_id,
        capability=capability,
        elapsed_ms=elapsed_ms,
    )


@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    started_at = getattr(request.state, "started_at", perf_counter())
    request_id = getattr(request.state, "request_id", str(uuid4()))
    capability = getattr(request.state, "capability", "unknown")
    meta = _build_meta(request_id, capability, started_at)
    body = ErrorResponse(
        error={
            "code": "INVALID_REQUEST",
            "message": "Request body validation failed.",
            "details": {"validation_errors": exc.errors()},
        },
        meta=meta,
    )
    return JSONResponse(status_code=422, content=body.model_dump())


@app.exception_handler(CapabilityError)
async def capability_exception_handler(request: Request, exc: CapabilityError) -> JSONResponse:
    started_at = getattr(request.state, "started_at", perf_counter())
    request_id = getattr(request.state, "request_id", str(uuid4()))
    capability = getattr(request.state, "capability", "unknown")
    meta = _build_meta(request_id, capability, started_at)
    body = ErrorResponse(
        error={
            "code": exc.code,
            "message": exc.message,
            "details": exc.details,
        },
        meta=meta,
    )
    return JSONResponse(status_code=exc.status_code, content=body.model_dump())


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/v1/capabilities/run", response_model=SuccessResponse)
async def run_capability(
    request: Request,
    request_body: CapabilityRequest = Body(
        ...,
        openapi_examples={
            "text_summary": {
                "summary": "Text Summary Example",
                "description": "Summarize a paragraph with max output length.",
                "value": {
                    "capability": "text_summary",
                    "input": {
                        "text": "FastAPI is a modern Python web framework. It is designed for high productivity and reliable APIs. This assignment only needs a minimal backend service.",
                        "max_length": 80,
                    },
                    "request_id": "demo-summary-001",
                },
            },
            "text_keywords": {
                "summary": "Keyword Extraction Example",
                "description": "Extract top-k keywords from input text.",
                "value": {
                    "capability": "text_keywords",
                    "input": {
                        "text": "FastAPI makes building APIs simple. Simple APIs improve delivery speed and service quality.",
                        "top_k": 3,
                    },
                    "request_id": "demo-keywords-001",
                },
            },
        },
    ),
) -> SuccessResponse:
    started_at = perf_counter()
    request.state.started_at = started_at

    request_id = request_body.request_id or str(uuid4())
    request.state.request_id = request_id
    request.state.capability = request_body.capability

    result = execute_capability(request_body.capability, request_body.input)
    meta = _build_meta(request_id, request_body.capability, started_at)

    logger.info(
        "Capability executed",
        extra={
            "request_id": request_id,
            "capability": request_body.capability,
            "elapsed_ms": meta.elapsed_ms,
        },
    )

    return SuccessResponse(data=result, meta=meta)
