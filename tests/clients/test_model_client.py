import asyncio
from types import SimpleNamespace
from typing import Any

import litellm
import pytest

from app.clients import model_client

_QUESTION = "泵异响怎么办"


def _timeout() -> litellm.Timeout:
    return litellm.Timeout(message="t", model="ollama_chat/x", llm_provider="ollama")


def _patch(monkeypatch: pytest.MonkeyPatch, fake: Any) -> None:
    monkeypatch.setattr(
        model_client,
        "get_settings",
        lambda: SimpleNamespace(model_name="ollama_chat/x", model_api_base="http://h:11434", model_timeout_s=1.0),
    )
    monkeypatch.setattr(model_client.litellm, "acompletion", fake)


def test_call_model_passes_ollama_params(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: dict[str, Any] = {}

    async def fake(**kwargs: Any) -> Any:
        seen.update(kwargs)
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="ok"))])

    _patch(monkeypatch, fake)
    assert asyncio.run(model_client.call_model(_QUESTION)) == "ok"
    assert seen["model"] == "ollama_chat/x"
    assert seen["api_base"] == "http://h:11434"
    assert seen["timeout"] == 1.0


def test_call_model_retries_then_raises_timeout(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    calls = 0

    async def always_timeout(**kwargs: Any) -> Any:
        nonlocal calls
        calls += 1
        raise _timeout()

    _patch(monkeypatch, always_timeout)
    with pytest.raises(TimeoutError) as exc_info:
        asyncio.run(model_client.call_model(_QUESTION))
    assert calls == 1 + model_client.MAX_RETRIES
    assert isinstance(exc_info.value.__cause__, litellm.Timeout)
    assert _QUESTION not in caplog.text  # 重试日志只记提问长度,不记原文


def test_call_model_recovers_after_one_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = 0

    async def timeout_once(**kwargs: Any) -> Any:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise _timeout()
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="ok"))])

    _patch(monkeypatch, timeout_once)
    assert asyncio.run(model_client.call_model(_QUESTION)) == "ok"
    assert calls == 2
