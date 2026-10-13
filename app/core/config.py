from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_name: str
    model_timeout_s: float = 30.0
    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    """获取全局配置（单例模式）"""
    return Settings()  # pyright: ignore[reportCallIssue] -- 必填配置由 BaseSettings 从环境变量注入。


# 创建配置实例
settings = get_settings()
