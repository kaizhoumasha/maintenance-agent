from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.exceptions.errors import HTTP_STATUS, AppError, ErrorCode, ErrorResponse
from app.logger import logger, setup_logging
from app.middlewares.trace_id_middleware import get_trace_id, trace_id_middleware
from app.models import AskRequest, AskResponse

app = FastAPI(title="maintenance-agent")
app.middleware("http")(trace_id_middleware)

@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    body = ErrorResponse(
        trace_id=get_trace_id(),
        code=exc.code,
        message=exc.message,
        detail=exc.detail,
    )
    return JSONResponse(
        status_code=HTTP_STATUS[exc.code],
        content=body.model_dump(),
    )


@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    body = ErrorResponse(
        trace_id=get_trace_id(),
        code=ErrorCode.INTERNAL_ERROR,
        message="系统内部错误，请稍后重试",
        detail=f"{type(exc).__name__}: {exc}",
    )
    return JSONResponse(status_code=500, content=body.model_dump())


setup_logging()

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

@app.post("/ask")
async def ask(req: AskRequest) -> AskResponse:
    logger.info("receive request: %s", req.json())
    raise AppError(code=ErrorCode.UPSTREAM_ERROR, message="上游异常",)