"""
Trace ID 中间件模块

提供请求追踪功能,为每个请求生成唯一的 trace_id 并在响应头中返回
        trace_id_var.reset(token)

三个细节：
try/finally 里 reset(token) 不能省。 ContextVar 的 set 会返回 token，请求结束必须 reset，否则 trace_id 会泄漏到处理下一个请求的同一个上下文里——并发一上来就会串号。
default="-" 是安全网。 万一有请求没走 middleware（比如测试里直接调函数），get_trace_id() 不会崩，而是返回 "-"，日志里一眼能看出这条 trace 丢了。
响应头里回写 X-Trace-Id。 这样客户端（以后前端或测试脚本）拿到 trace_id，出问题直接上报，grep 日志就行——这就是验收时"报一个 trace_id，1 分钟还原"的完整链路。
"""
import uuid
from collections.abc import Awaitable, Callable
from contextvars import ContextVar

from fastapi import Request, Response

# 使用 ContextVar 存储 trace_id,支持异步上下文隔离
trace_id_var: ContextVar[str] = ContextVar("trace_id", default="-")


def get_trace_id() -> str:
    """
    获取当前请求上下文的 trace_id
    
    Returns:
        str: 当前请求的 trace_id,如果未设置则返回 "-"
    """
    return trace_id_var.get()


async def trace_id_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    """
    FastAPI 中间件:为每个请求生成唯一的 trace_id 并添加到响应头
    
    Args:
        request: FastAPI 请求对象
        call_next: 下一个中间件或路由处理函数
        
    Returns:
        Response: 添加了 X-Trace-Id 响应头的响应对象
    """
    # 生成唯一的 trace_id (使用 UUID4 的十六进制字符串)
    trace_id = uuid.uuid4().hex
    # 将 trace_id 设置到当前上下文中
    token = trace_id_var.set(trace_id)
    try:
        # 调用下一个中间件或路由处理函数
        response = await call_next(request)
    finally:
        # 确保在请求处理完成后重置上下文变量
        trace_id_var.reset(token)
    # 在响应头中添加 trace_id,便于客户端追踪
    response.headers["X-Trace-Id"] = trace_id
    return response
