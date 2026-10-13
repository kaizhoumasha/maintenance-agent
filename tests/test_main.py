import inspect

from fastapi.testclient import TestClient

from app.main import app, ask

client = TestClient(app)


def test_ask_ok_http() -> None:
    r = client.post("/ask", json={"question": "泵异响怎么办"})
    assert r.status_code == 200
    assert r.json()["answer"]


def test_trace_id_unique_per_request() -> None:
    ids = {client.get("/health").headers["X-Trace-Id"] for _ in range(3)}
    assert len(ids) == 3


def test_ask_route_is_sync() -> None:
    assert inspect.iscoroutinefunction(ask)
