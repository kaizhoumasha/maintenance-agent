import pytest

from pydantic import ValidationError
from app.models import AskRequest, AskResponse

def test_ask_request_ok() -> None:
    req = AskRequest(question="泵异响怎么办")
    assert req.question == "泵异响怎么办"
    assert req.device_id is None

def test_ask_request_missing_question() -> None:
    with pytest.raises(ValidationError) as exc_info:
        AskRequest()
    assert exc_info.value.errors()[0]["loc"] == ("question",)

def test_ask_response_defaults() -> None:
    resp = AskResponse(answer="检查皮带张紧度")
    assert resp.confidence == 0.0
