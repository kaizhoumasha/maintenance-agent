from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from .errors import HTTP_STATUS, AppError, ErrorCode, ErrorResponse
from .logger import logger
from .request_context import get_trace_id

# 未列出的 HTTP 状态码统一按 INVALID_REQUEST 处理
_HTTP_ERROR_CODE = {
    404: ErrorCode.NOT_FOUND,
    405: ErrorCode.METHOD_NOT_ALLOWED,
}


def _error_response(
    status: int, code: ErrorCode, message: str, detail: str | None = None
) -> JSONResponse:
    """
    构建统一的错误响应。

    Args:
        status: HTTP 状态码。
        code: 错误码，用于客户端识别错误类型。
        message: 错误消息，面向用户的描述。
        detail: 可选的错误详情，提供更具体的错误信息（如参数校验失败的具体字段）。

    Returns:
        JSONResponse: 包含统一格式错误响应的 JSON 响应对象，带有 X-Trace-Id 响应头。
    """
    trace_id = get_trace_id()
    body = ErrorResponse(trace_id=trace_id, code=code, message=message, detail=detail)
    # 必须在这里设置响应头:Exception handler 由最外层的 ServerErrorMiddleware 调用,
    # 响应不经过 trace_id_middleware。其余 handler 会经过中间件,重复设置无害(值相同)。
    return JSONResponse(
        status_code=status,
        content=body.model_dump(mode="json"),
        headers={"X-Trace-Id": trace_id},
    )


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """
    处理应用自定义业务异常。

    Args:
        request: FastAPI 请求对象。
        exc: 应用自定义异常，包含业务错误码、错误消息和可选详情。

    Returns:
        JSONResponse: 格式化的错误响应，4xx 错误仅记录警告日志，5xx 错误记录完整堆栈。
    """
    status = HTTP_STATUS[exc.code]
    # 4xx 是调用方的问题,不记堆栈,避免日志噪音
    logger.warning("%s: %s", exc.code, exc.message, exc_info=exc if status >= 500 else None)
    return _error_response(status, exc.code, exc.message, exc.detail)


async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    处理请求参数校验异常。

    Args:
        request: FastAPI 请求对象。
        exc: 请求校验异常，包含所有校验失败的字段及其错误信息。

    Returns:
        JSONResponse: 参数错误响应，detail 字段包含所有校验失败的具体位置和原因。
    """
    detail = "; ".join(f"{'.'.join(map(str, e['loc']))}: {e['msg']}" for e in exc.errors())
    code = ErrorCode.INVALID_REQUEST
    return _error_response(HTTP_STATUS[code], code, "请求参数错误", detail)


async def http_error_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """
    处理 HTTP 异常（来自 Starlette 的 HTTPException）。

    Args:
        request: FastAPI 请求对象。
        exc: HTTP 异常，包含 HTTP 状态码和可选的详情信息。

    Returns:
        JSONResponse: 错误响应，将 404/405 映射为对应错误码，其余状态码统一按 INVALID_REQUEST 处理。
    """
    code = _HTTP_ERROR_CODE.get(exc.status_code, ErrorCode.INVALID_REQUEST)
    return _error_response(exc.status_code, code, str(exc.detail))


async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    处理所有未被捕获的异常（兜底异常处理器）。

    Args:
        request: FastAPI 请求对象。
        exc: 未处理的异常对象。

    Returns:
        JSONResponse: 统一的内部错误响应，异常详情仅记录到日志，不返回给客户端。
    """
    # 异常详情只进日志,不返回给客户端
    logger.exception("unhandled error", exc_info=exc)
    return _error_response(
        HTTP_STATUS[ErrorCode.INTERNAL_ERROR], ErrorCode.INTERNAL_ERROR, "系统内部错误，请稍后重试"
    )


def register_exception_handlers(app: FastAPI) -> None:
    """
    注册全局异常处理器，将各类异常映射到统一的错误响应格式。

    Args:
        app: FastAPI 应用实例，用于注册异常处理器。

    Returns:
        None
    """
    app.add_exception_handler(AppError, app_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, validation_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(StarletteHTTPException, http_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, unhandled_error_handler)
