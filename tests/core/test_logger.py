import logging
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_logs_carry_trace_id(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.INFO):
        r = client.post("/ask", json={"question": "泵异响怎么办"})
    trace_id = r.headers["X-Trace-Id"]
    app_logs = [rec for rec in caplog.records if rec.name == "maintenance-agent"]
    assert app_logs
    assert all(getattr(rec, "trace_id", None) == trace_id for rec in app_logs)


def _access_logs(caplog: pytest.LogCaptureFixture, prefix: str) -> list[logging.LogRecord]:
    return [
        rec
        for rec in caplog.records
        if rec.name == "maintenance-agent" and rec.getMessage().startswith(prefix)
    ]


def test_access_log_has_trace_id_status_and_no_query(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.INFO):
        r = client.get("/health?token=secret")
    (rec,) = _access_logs(caplog, "GET /health")
    assert rec.getMessage().startswith("GET /health -> 200 ")
    assert getattr(rec, "trace_id", None) == r.headers["X-Trace-Id"]
    # 查询串可能带敏感信息,访问日志只记路径(caplog.text 还含测试客户端 httpx2 自己的日志,不能用)
    assert "secret" not in rec.getMessage()


def test_access_log_records_unhandled_error_as_500(caplog: pytest.LogCaptureFixture) -> None:
    error_client = TestClient(app, raise_server_exceptions=False)
    with (
        patch("app.main.ask_service", side_effect=RuntimeError("boom")),
        caplog.at_level(logging.INFO),
    ):
        r = error_client.post("/ask", json={"question": "x"})
    (rec,) = _access_logs(caplog, "POST /ask")
    assert rec.getMessage().startswith("POST /ask -> 500 ")
    assert getattr(rec, "trace_id", None) == r.headers["X-Trace-Id"]


def test_uvicorn_access_log_disabled() -> None:
    # 访问日志改由 trace_id_middleware 记录;uvicorn 自带的没有 trace_id,且会重复
    assert logging.getLogger("uvicorn.access").disabled
