import litellm

from app.core import get_settings, logger

MAX_RETRIES = 2

SYSTEM_PROMPT = """
你是一个助手，你需要根据用户输入的文本，生成一个针对该文本的答案。
请确保你的答案是简洁的，准确且无错误。
请不要包含任何额外的信息，只返回答案。

返回的格式为 JSON
"""

async def call_model(question: str) -> str:
    settings = get_settings()
    last_exc: litellm.Timeout | None = None
    for attempt in range(1 + MAX_RETRIES):
        try:
            resp = await litellm.acompletion(
                model=settings.model_name,
                api_base=settings.model_api_base,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},  # 里面写死 JSON 格式要求
                    {"role": "user", "content": question},
                ],
                response_format={"type": "json_object"},
                timeout=settings.model_timeout_s,
            )
            return resp.choices[0].message.content or ""
        except litellm.Timeout as e:
            last_exc = e
            logger.warning("模型调用超时,第 %d 次尝试 question_len=%d", attempt + 1, len(question))
    raise TimeoutError(f"模型调用超时,已重试 {MAX_RETRIES} 次") from last_exc
