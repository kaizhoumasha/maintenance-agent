import pytest
from pydantic import ValidationError

from app.core import Settings


def test_settings_missing_required(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MODEL_NAME", raising=False)
    with pytest.raises(ValidationError) as exc_info:
        Settings()
    assert "model_name" in str(exc_info.value)

def test_settings_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MODEL_NAME", "test-model")
    monkeypatch.delenv("MODEL_TIMEOUT_S", raising=False)
    monkeypatch.delenv("LOG_LEVEL", raising=False)
    s = Settings()
    assert s.model_name == "test-model"
    assert s.model_timeout_s == 30.0
    assert s.log_level == "INFO"
