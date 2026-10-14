from collections.abc import Callable, Coroutine
from typing import Any

import httpx2
import openai
from pydantic import ValidationError

from app.clients.model_client import call_model
from app.core import AppError, ErrorCode, logger
from app.schemas import AskRequest, AskResponse


async def ask_service(req: AskRequest, call_model_fn: Callable[[str], Coroutine[Any, Any, str]] = call_model) -> AskResponse:
    try:
        last_error: ValidationError | None = None
        for attempt in range(2):  # 首次 + 重试一次
            raw = await call_model_fn(req.question)
            try:
                return AskResponse.model_validate_json(raw)
            except ValidationError as e:
                last_error = e
                logger.warning("模型输出格式校验失败,（已重试 %d 次）: %s", attempt, e.errors())
        raise AppError(code=ErrorCode.UPSTREAM_ERROR, message="模型输出格式异常，请转人工处理") from last_error

    except (TimeoutError, httpx2.TimeoutException) as exc:
        raise AppError(code=ErrorCode.MODEL_TIMEOUT, message="模型超时", detail=str(exc)) from exc
    except (httpx2.HTTPError, openai.APIError) as exc:
        # detail 只给异常类型名,避免把上游地址等内部信息返回给客户端
        raise AppError(
            code=ErrorCode.UPSTREAM_ERROR, message="上游异常", detail=type(exc).__name__
        ) from exc
