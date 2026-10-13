import asyncio
from types import SimpleNamespace

import pytest

from app.clients import model_client

_QUESTION = "泵异响怎么办"


def _fast_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(model_client, "get_settings", lambda: SimpleNamespace(model_timeout_s=0.01))


def test_call_model_retries_then_raises_timeout(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    calls = 0

    async def always_slow(question: str) -> str:
        nonlocal calls
        calls += 1
        await asyncio.sleep(1)
        return "never"

    _fast_timeout(monkeypatch)
    monkeypatch.setattr(model_client, "_fake_infer", always_slow)
    with pytest.raises(TimeoutError) as exc_info:
        asyncio.run(model_client.call_model(_QUESTION))
    assert calls == 1 + model_client.MAX_RETRIES
    assert isinstance(exc_info.value.__cause__, TimeoutError)
    assert _QUESTION not in caplog.text  # 重试日志只记提问长度,不记原文


def test_call_model_recovers_after_one_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = 0

    async def slow_once(question: str) -> str:
        nonlocal calls
        calls += 1
        if calls == 1:
            await asyncio.sleep(1)
        return "ok"

    _fast_timeout(monkeypatch)
    monkeypatch.setattr(model_client, "_fake_infer", slow_once)
    assert asyncio.run(model_client.call_model(_QUESTION)) == "ok"
    assert calls == 2
