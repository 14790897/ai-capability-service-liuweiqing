from fastapi.testclient import TestClient

from app.main import app
from app.services import capabilities as capabilities_service

client = TestClient(app)


def test_health_check() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_text_summary_success(monkeypatch) -> None:
    monkeypatch.setattr(
        capabilities_service,
        "_call_model",
        lambda *args, **kwargs: "FastAPI is productive and provides validation with API docs.",
    )

    response = client.post(
        "/v1/capabilities/run",
        json={
            "capability": "text_summary",
            "input": {
                "text": "FastAPI is productive. It provides validation and API docs. This service exposes unified capabilities.",
                "max_length": 60,
            },
            "request_id": "summary-test-1",
        },
    )

    payload = response.json()
    assert response.status_code == 200
    assert payload["ok"] is True
    assert payload["meta"]["request_id"] == "summary-test-1"
    assert payload["meta"]["capability"] == "text_summary"
    assert len(payload["data"]["result"]) <= 60


def test_text_keywords_success(monkeypatch) -> None:
    monkeypatch.setattr(
        capabilities_service,
        "_call_model",
        lambda *args, **kwargs: '["apis", "service", "delivery"]',
    )

    response = client.post(
        "/v1/capabilities/run",
        json={
            "capability": "text_keywords",
            "input": {
                "text": "Simple APIs improve delivery speed and service quality. APIs help service teams move faster.",
                "top_k": 3,
            },
        },
    )

    payload = response.json()
    assert response.status_code == 200
    assert payload["ok"] is True
    assert len(payload["data"]["result"]) == 3


def test_unsupported_capability_returns_stable_error() -> None:
    response = client.post(
        "/v1/capabilities/run",
        json={
            "capability": "image_generation",
            "input": {"prompt": "hello"},
        },
    )

    payload = response.json()
    assert response.status_code == 404
    assert payload["ok"] is False
    assert payload["error"]["code"] == "UNSUPPORTED_CAPABILITY"


def test_invalid_input_returns_validation_error() -> None:
    response = client.post(
        "/v1/capabilities/run",
        json={
            "capability": "text_summary",
            "input": {
                "text": "abc",
                "max_length": 1,
            },
        },
    )

    payload = response.json()
    assert response.status_code == 400
    assert payload["ok"] is False
    assert payload["error"]["code"] == "INVALID_INPUT"