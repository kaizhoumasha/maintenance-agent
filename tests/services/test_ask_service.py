import asyncio
import json

import httpx2
import litellm
import pytest

from app.core import AppError, ErrorCode
from app.schemas import AskRequest, AskResponse, RiskLevel
from app.services import ask_service


def _json_response(**overrides: object) -> str:
    base = {
        "answer": "检查皮带张紧度",
        "steps": [{"description": "停机检查皮带", "basis": "手册 3.2 节"}],
        "risk_level": "low",
        "needs_human_review": False,
        "confidence": 0.9,
    }
    base.update(overrides)
    return json.dumps(base, ensure_ascii=False)


async def _ok_json(question: str) -> str:
    return _json_response()

async def _raise_timeout(question: str) -> str:
    raise TimeoutError("模拟上游超时")

async def _raise_upstream(question: str) -> str:
    raise AppError(code=ErrorCode.UPSTREAM_ERROR, message="上游异常")


def test_ask_service_ok() -> None:
    req = AskRequest(question="测试问题")
    resp: AskResponse = asyncio.run(ask_service(req, _ok_json))

    assert resp.steps[0].description == "停机检查皮带"
    assert resp.steps[0].basis == "手册 3.2 节"
    assert resp.risk_level == RiskLevel.LOW
    assert resp.needs_human_review is False

def test_ask_service_timeout() -> None:
    req = AskRequest(question="测试问题")
    with pytest.raises(AppError) as exc_info:
        asyncio.run(ask_service(req, _raise_timeout))
    assert exc_info.value.code == ErrorCode.MODEL_TIMEOUT
    assert exc_info.value.message == "模型超时"

def test_ask_service_upstream() -> None:
    req = AskRequest(question="测试问题")
    with pytest.raises(AppError) as exc_info:
        asyncio.run(ask_service(req, _raise_upstream))
    assert exc_info.value.code == ErrorCode.UPSTREAM_ERROR
    assert exc_info.value.message == "上游异常"


def test_ask_service_retries_on_invalid_json() -> None:
    calls = 0

    async def flaky(question: str) -> str:
        nonlocal calls
        calls += 1
        if calls == 1:
            return "这根本不是 JSON"  # 第一次脏
        return _json_response()     # 第二次好

    resp = asyncio.run(ask_service(AskRequest(question="泵异响怎么办"), flaky))
    assert calls == 2
    assert resp.answer == "检查皮带张紧度"


def test_ask_service_escalates_after_two_invalid() -> None:
    async def always_dirty(question: str) -> str:
        return "这根本不是 JSON"

    with pytest.raises(AppError) as exc_info:
        asyncio.run(ask_service(AskRequest(question="泵异响怎么办"), always_dirty))
    assert "转人工" in exc_info.value.message


@pytest.mark.parametrize(
    ("exc", "code"),
    [
        (httpx2.ReadTimeout("t"), ErrorCode.MODEL_TIMEOUT),
        (httpx2.ConnectError("c"), ErrorCode.UPSTREAM_ERROR),
        (
            litellm.APIConnectionError(message="conn refused", llm_provider="ollama", model="x"),
            ErrorCode.UPSTREAM_ERROR,
        ),
        (
            litellm.RateLimitError(message="429", llm_provider="ollama", model="x"),
            ErrorCode.UPSTREAM_ERROR,
        ),
    ],
)
def test_ask_service_maps_provider_errors(exc: Exception, code: ErrorCode) -> None:
    async def boom(question: str) -> str:
        raise exc

    with pytest.raises(AppError) as exc_info:
        asyncio.run(ask_service(AskRequest(question="测试问题"), boom))
    assert exc_info.value.code == code
    assert exc_info.value.__cause__ is exc
