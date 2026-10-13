from unittest.mock import patch

import pytest
from fastapi import Response
from fastapi.testclient import TestClient

from app.core import HTTP_STATUS, AppError, ErrorCode
from app.main import app

# raise_server_exceptions=False: 让未处理异常走兜底 handler,而不是在测试里直接抛出
client = TestClient(app, raise_server_exceptions=False)


def _assert_error(r: Response, status: int, code: ErrorCode) -> dict:
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
    _assert_error(r, 404, ErrorCode.NOT_FOUND)


def test_method_not_allowed_http() -> None:
    r = client.get("/ask")
    _assert_error(r, 405, ErrorCode.METHOD_NOT_ALLOWED)


@pytest.mark.parametrize(
    ("code", "has_stack"),
    [(ErrorCode.INVALID_REQUEST, False), (ErrorCode.UPSTREAM_ERROR, True)],
)
def test_app_error_stack_only_for_5xx(
    code: ErrorCode, has_stack: bool, caplog: pytest.LogCaptureFixture
) -> None:
    with patch("app.main.ask_service", side_effect=AppError(code=code, message="m")):
        client.post("/ask", json={"question": "x"})
    record = next(r for r in caplog.records if r.levelname == "WARNING")
    assert bool(record.exc_info) is has_stack


def test_http_status_unique() -> None:
    # handlers.py 按状态码反查错误码,状态码重复会让反查结果不确定
    assert len(set(HTTP_STATUS.values())) == len(HTTP_STATUS)
