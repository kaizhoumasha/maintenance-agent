import pytest
from pydantic import ValidationError

from app.core import Settings


def test_settings_missing_required(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MODEL_NAME", raising=False)
    with pytest.raises(ValidationError) as exc_info:
        Settings()  # pyright: ignore[reportCallIssue] -- 故意不传必填字段,验证缺失时报错。
    assert "model_name" in str(exc_info.value)

def test_settings_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MODEL_NAME", "test-model")
    monkeypatch.delenv("MODEL_TIMEOUT_S", raising=False)
    monkeypatch.delenv("LOG_LEVEL", raising=False)
    s = Settings()  # pyright: ignore[reportCallIssue] -- 必填的 model_name 由 monkeypatch 注入环境变量。
    assert s.model_name == "test-model"
    assert s.model_timeout_s == 30.0
    assert s.log_level == "INFO"
