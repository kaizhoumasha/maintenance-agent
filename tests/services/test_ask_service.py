import asyncio

import httpx2
import pytest

from app.core import AppError, ErrorCode
from app.schemas import AskRequest, AskResponse
from app.services import ask_service


async def _ok(question: str) -> str:
    return "检查皮带张紧度"

async def _raise_timeout(question: str) -> str:
    raise TimeoutError("模拟上游超时")

async def _raise_upstream(question: str) -> str:
    raise AppError(code=ErrorCode.UPSTREAM_ERROR, message="上游异常")


def test_ask_service_ok() -> None:
    req = AskRequest(question="测试问题")
    res: AskResponse = asyncio.run(ask_service(req, _ok))
    assert res.answer == "检查皮带张紧度"
    assert res.confidence == 0.0

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


@pytest.mark.parametrize(
    ("exc", "code"),
    [
        (httpx2.ReadTimeout("t"), ErrorCode.MODEL_TIMEOUT),
        (httpx2.ConnectError("c"), ErrorCode.UPSTREAM_ERROR),
    ],
)
def test_ask_service_maps_httpx_errors(exc: Exception, code: ErrorCode) -> None:
    def boom(question: str) -> str:
        raise exc

    with pytest.raises(AppError) as exc_info:
        asyncio.run(ask_service(AskRequest(question="测试问题"), boom))
    assert exc_info.value.code == code
    assert exc_info.value.__cause__ is exc
