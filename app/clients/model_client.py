import litellm

from app.core import get_settings, logger

MAX_RETRIES = 2


async def call_model(question: str) -> str:
    settings = get_settings()
    last_exc: litellm.Timeout | None = None
    for attempt in range(1 + MAX_RETRIES):
        try:
            resp = await litellm.acompletion(
                model=settings.model_name,
                api_base=settings.model_api_base,
                messages=[{"role": "user", "content": question}],
                timeout=settings.model_timeout_s,
            )
            return resp.choices[0].message.content or ""
        except litellm.Timeout as e:
            last_exc = e
            logger.warning("模型调用超时,第 %d 次尝试 question_len=%d", attempt + 1, len(question))
    raise TimeoutError(f"模型调用超时,已重试 {MAX_RETRIES} 次") from last_exc
