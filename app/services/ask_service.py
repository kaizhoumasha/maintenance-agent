from collections.abc import Callable

import httpx2

from app.clients.model_client import call_model
from app.core import AppError, ErrorCode
from app.schemas import AskRequest, AskResponse


def ask_service(req: AskRequest, call_model_fn: Callable[[str], str] = call_model) -> AskResponse:
    try:
        answer = call_model_fn(req.question)
    except (TimeoutError, httpx2.TimeoutException) as exc:
        raise AppError(code=ErrorCode.MODEL_TIMEOUT, message="模型超时", detail=str(exc)) from exc
    except httpx2.HTTPError as exc:
        # detail 只给异常类型名,避免把上游地址等内部信息返回给客户端
        raise AppError(
            code=ErrorCode.UPSTREAM_ERROR, message="上游异常", detail=type(exc).__name__
        ) from exc
    
    return AskResponse(answer=answer)

