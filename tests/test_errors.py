import logging
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.core import AppError, ErrorCode
from app.main import app

client = TestClient(app)

def test_ask_upstream_error_http() -> None:
    with patch(
        "app.main.ask_service",
        side_effect=AppError(code=ErrorCode.UPSTREAM_ERROR, message="上游异常"),
    ):
        r = client.post("/ask", json={"question": "泵异响怎么办"})
    assert r.status_code == 502
    body = r.json()
    assert set(body) == {"trace_id", "code", "message", "detail"}
    assert body["code"] == "UPSTREAM_ERROR"
    assert r.headers["X-Trace-Id"] == body["trace_id"]


def test_ask_model_timeout_http() -> None:
    with patch(
        "app.main.ask_service",
        side_effect=AppError(code=ErrorCode.MODEL_TIMEOUT, message="模型超时"),
    ):
        r = client.post("/ask", json={"question": "泵异响怎么办"})
    assert r.status_code == 504
    assert r.headers["X-Trace-Id"] == r.json()["trace_id"]
