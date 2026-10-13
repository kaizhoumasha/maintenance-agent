from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core import (
    HTTP_STATUS,
    AppError,
    ErrorCode,
    ErrorResponse,
    get_trace_id,
    logger,
    setup_logging,
)
from app.middlewares import trace_id_middleware
from app.schemas import AskRequest, AskResponse
from app.services import ask_service

app = FastAPI(title="maintenance-agent")
app.middleware("http")(trace_id_middleware)

def _error_response(
    status: int, code: ErrorCode, message: str, detail: str | None = None
) -> JSONResponse:
    trace_id = get_trace_id()
    body = ErrorResponse(trace_id=trace_id, code=code, message=message, detail=detail)
    # 这里也要带响应头:兜底 handler 的响应不会经过 trace_id_middleware
    return JSONResponse(
        status_code=status,
        content=body.model_dump(mode="json"),
        headers={"X-Trace-Id": trace_id},
    )


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    logger.warning("%s: %s", exc.code, exc.message, exc_info=exc)
    return _error_response(HTTP_STATUS[exc.code], exc.code, exc.message, exc.detail)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    detail = "; ".join(f"{'.'.join(map(str, e['loc']))}: {e['msg']}" for e in exc.errors())
    code = ErrorCode.INVALID_REQUEST
    return _error_response(HTTP_STATUS[code], code, "请求参数错误", detail)


@app.exception_handler(StarletteHTTPException)
async def http_error_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    return _error_response(exc.status_code, ErrorCode.INVALID_REQUEST, str(exc.detail))


@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    # 异常详情只进日志,不返回给客户端
    logger.exception("unhandled error", exc_info=exc)
    return _error_response(
        HTTP_STATUS[ErrorCode.INTERNAL_ERROR], ErrorCode.INTERNAL_ERROR, "系统内部错误，请稍后重试"
    )


setup_logging()

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

# 同步 def:ask_service 是阻塞调用,交给线程池,避免卡住事件循环
@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest) -> AskResponse:
    logger.info("receive request: question_len=%d device_id=%s", len(req.question), req.device_id)
    return ask_service(req)
