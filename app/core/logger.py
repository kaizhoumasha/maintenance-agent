import logging

from app.core.request_context import get_trace_id


class TraceIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.trace_id = get_trace_id()
        return True

_done = False
def setup_logging() -> None:
    global _done
    if _done:
        return

    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter("[%(trace_id)s] [%(asctime)s] %(levelname)s %(name)s: %(message)s")
    )
    handler.addFilter(TraceIdFilter())
    root = logging.getLogger()
    root.addHandler(handler)
    root.setLevel(logging.INFO)
    # 访问日志改由 trace_id_middleware 记录(带 trace_id);uvicorn 自带的没有 trace_id,且会重复
    logging.getLogger("uvicorn.access").disabled = True
    _done = True


logger = logging.getLogger("maintenance-agent")
