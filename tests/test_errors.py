from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.core import AppError, ErrorCode
from app.main import app

# raise_server_exceptions=False: 让未处理异常走兜底 handler,而不是在测试里直接抛出
client = TestClient(app, raise_server_exceptions=False)


def _assert_error(r, status: int, code: ErrorCode) -> dict:
    assert r.status_code == status
    body = r.json()
    assert set(body) == {"trace_id", "code", "message", "detail"}
    assert body["code"] == code
    assert body["trace_id"] != "-"
    assert r.headers["X-Trace-Id"] == body["trace_id"]
    return body


@pytest.mark.parametrize(
    ("code", "status"),
    [(ErrorCode.UPSTREAM_ERROR, 502), (ErrorCode.MODEL_TIMEOUT, 504)],
)
def test_ask_app_error_http(code: ErrorCode, status: int) -> None:
    with patch("app.main.ask_service", side_effect=AppError(code=code, message="m")):
        r = client.post("/ask", json={"question": "泵异响怎么办"})
    _assert_error(r, status, code)


def test_ask_unhandled_error_http() -> None:
    with patch("app.main.ask_service", side_effect=RuntimeError("secret-password=abc")):
        r = client.post("/ask", json={"question": "泵异响怎么办"})
    body = _assert_error(r, 500, ErrorCode.INTERNAL_ERROR)
    assert body["detail"] is None
    assert "secret" not in r.text  # 内部异常信息不能返回给客户端


@pytest.mark.parametrize("payload", [{}, {"question": ""}, {"question": "   "}, {"question": "x" * 2001}])
def test_ask_invalid_request_http(payload: dict) -> None:
    r = client.post("/ask", json=payload)
    body = _assert_error(r, 400, ErrorCode.INVALID_REQUEST)
    assert "question" in body["detail"]


def test_unknown_route_http() -> None:
    r = client.get("/nope")
    _assert_error(r, 404, ErrorCode.INVALID_REQUEST)
