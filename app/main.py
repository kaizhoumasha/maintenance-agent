from fastapi import FastAPI

from app.core import logger, register_exception_handlers, setup_logging
from app.middlewares import trace_id_middleware
from app.schemas import AskRequest, AskResponse
from app.services import ask_service

app = FastAPI(title="maintenance-agent")
app.middleware("http")(trace_id_middleware)
register_exception_handlers(app)

setup_logging()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


# 同步 def:ask_service 是阻塞调用,交给线程池,避免卡住事件循环
@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest) -> AskResponse:
    logger.info("receive request: question_len=%d device_id=%s", len(req.question), req.device_id)
    return ask_service(req)
