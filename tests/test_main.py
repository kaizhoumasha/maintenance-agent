import inspect
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.core import get_settings
from app.main import _load_settings, app, ask
from app.schemas import AskResponse

client = TestClient(app)


def test_ask_ok_http() -> None:
    fake = AskResponse(answer="ok", confidence=0.9)
    with patch("app.main.ask_service", new=AsyncMock(return_value=fake)):
        r = client.post("/ask", json={"question": "泵异响怎么办"})
    assert r.status_code == 200
    assert r.json()["answer"] == "ok"


def test_trace_id_unique_per_request() -> None:
    ids = {client.get("/health").headers["X-Trace-Id"] for _ in range(3)}
    assert len(ids) == 3


def test_ask_route_is_async() -> None:
    assert inspect.iscoroutinefunction(ask)


def test_load_settings_exits_when_required_missing(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.delenv("MODEL_NAME", raising=False)
    get_settings.cache_clear()  # 已缓存的 Settings 会掩盖缺失
    try:
        with pytest.raises(SystemExit) as exc_info:
            _load_settings()
    finally:
        get_settings.cache_clear()
    assert exc_info.value.code == 1
    assert "model_name" in capsys.readouterr().err
