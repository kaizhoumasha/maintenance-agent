from pydantic import BaseModel, ConfigDict, Field


class AskRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    question: str = Field(min_length=1, max_length=2000)
    device_id: str | None = None

class AskResponse(BaseModel):

    answer: str
    confidence: float = 0.0
