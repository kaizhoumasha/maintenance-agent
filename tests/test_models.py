import pytest
from pydantic import ValidationError

from app.schemas import AskRequest, AskResponse


def test_ask_request_ok() -> None:
    req = AskRequest(question="泵异响怎么办")
    assert req.question == "泵异响怎么办"
    assert req.device_id is None

def test_ask_request_missing_question() -> None:
    with pytest.raises(ValidationError) as exc_info:
        AskRequest()  # pyright: ignore[reportCallIssue] -- 故意缺 question,验证校验报错。
    assert exc_info.value.errors()[0]["loc"] == ("question",)

def test_ask_response_defaults() -> None:
    resp = AskResponse(answer="检查皮带张紧度")
    assert resp.confidence == 0.0


@pytest.mark.parametrize("q", ["", "   ", "x" * 2001])
def test_ask_request_rejects_bad_question(q: str) -> None:
    with pytest.raises(ValidationError):
        AskRequest(question=q)
