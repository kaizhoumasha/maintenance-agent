"""Trace ID 中间件:为每个请求生成 trace_id,写入上下文,并通过 X-Trace-Id 响应头返回。"""
import uuid
from collections.abc import Awaitable, Callable

from fastapi import Request, Response

from app.core.request_context import set_trace_id


async def trace_id_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    trace_id = uuid.uuid4().hex
    # 刻意不 reset:未处理异常的兜底 handler 在本函数退出之后才运行,仍要读到 trace_id。
    # uvicorn 每个请求一个独立 task,上下文互不串。
    set_trace_id(trace_id)
    response = await call_next(request)
    response.headers["X-Trace-Id"] = trace_id
    return response
