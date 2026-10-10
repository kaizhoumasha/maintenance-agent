import pytest

from pydantic import ValidationError
from app.models import AskRequest, AskResponse

def test_ask_request_ok() -> None:
    req = AskRequest(question="泵异响怎么办")
    assert req.question == "泵异响怎么办"
    assert req.device_id is None

def test_ask_request_mission_question() -> None:
    with pytest.raises(ValidationError) as exc_info:
        AskRequest()
    assert exc_info.value.errors()[0]["loc"] == ("question",)
