import asyncio

from app.core import get_settings, logger

MAX_RETRIES = 2
_FAKE_LATENCY_S = 0.05  # 模拟模型推理延迟;Day 8 接真模型时删掉


async def call_model(question: str) -> str:
    timeout = get_settings().model_timeout_s
    last_exc: Exception | None = None
    for attempt in range(1 + MAX_RETRIES):
        try:
            return await asyncio.wait_for(_fake_infer(question), timeout=timeout)
        except TimeoutError as e:
            last_exc = e
            if attempt == MAX_RETRIES:
                break
            logger.warning("模型调用超时,第 %d 次重试 question_len=%d", attempt + 1, len(question))
    raise TimeoutError(f"模型调用超时,已重试 {MAX_RETRIES} 次") from last_exc


async def _fake_infer(question: str) -> str:
    await asyncio.sleep(_FAKE_LATENCY_S)
    return "this is a mock model response"
