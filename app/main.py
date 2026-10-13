import sys

from fastapi import FastAPI
from pydantic import ValidationError

from app.core import (
    Settings,
    get_settings,
    logger,
    register_exception_handlers,
    setup_logging,
)
from app.middlewares import trace_id_middleware
from app.schemas import AskRequest, AskResponse
from app.services import ask_service

app = FastAPI(title="maintenance-agent")
app.middleware("http")(trace_id_middleware)
register_exception_handlers(app)

setup_logging()

def _load_settings() -> Settings:
    try:
        return get_settings()
    except ValidationError as e:
        missing = sorted({str(err["loc"][0]) for err in e.errors() if err["type"] == "missing"})
        print(f"启动失败,缺少必填配置: {', '.join(missing)}", file=sys.stderr)
        raise SystemExit(1)


settings = _load_settings()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


# 同步 def:ask_service 是阻塞调用,交给线程池,避免卡住事件循环
@app.post("/ask", response_model=AskResponse)
async def ask(req: AskRequest) -> AskResponse:
    logger.info("receive request: question_len=%d device_id=%s", len(req.question), req.device_id)
    return await ask_service(req)
