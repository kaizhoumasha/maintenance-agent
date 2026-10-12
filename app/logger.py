import logging

from app.middlewares.trace_id_middleware import get_trace_id


class TraceIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.trace_id = get_trace_id()  # type: ignore[attr-defined]
        return True

_done = False

def setup_logging() -> None:
    global _done
    if _done:
        return

    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter("%(asctime)s [%(trace_id)s] %(levelname)s %(name)s: %(message)s")
    )
    handler.addFilter(TraceIdFilter())
    root = logging.getLogger()
    root.addHandler(handler)
    root.setLevel(logging.INFO)
    _done = True


logger = logging.getLogger("maintenance-agent")
