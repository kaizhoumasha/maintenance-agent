import logging

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_ask_upstream_error_shape() -> None:
    r = client.post("/ask", json={"question": "泵异响怎么办"})
    if r.status_code != 200:
        body = r.json()
        assert set(body) == {"trace_id", "code", "message", "detail"}
        assert body["code"] == "UPSTREAM_ERROR"
        assert r.headers["X-Trace-Id"] == body["trace_id"]


def test_trace_id_in_logs(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.INFO):
        r = client.post("/ask", json={"question": "泵异响怎么办"})
    
    if r.status_code != 200:
        trace_id = r.json()["trace_id"]
        assert trace_id != "-"
        hits = [rec for rec in caplog.records if getattr(rec, "trace_id", None) == trace_id]
        assert len(hits) >= 1
