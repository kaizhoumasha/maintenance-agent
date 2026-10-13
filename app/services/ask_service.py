from collections.abc import Callable

from app.clients.model_client import call_model
from app.core import AppError, ErrorCode
from app.schemas import AskRequest, AskResponse


def ask_service(req: AskRequest, call_model_fn: Callable[[str], str] = call_model) -> AskResponse:
    try:
        answer = call_model_fn(req.question)
    except TimeoutError as toe:
        raise AppError(code=ErrorCode.MODEL_TIMEOUT, message="模型超时", detail=str(toe))
    
    return AskResponse(answer=answer)

