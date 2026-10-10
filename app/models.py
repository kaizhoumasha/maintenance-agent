from pydantic import BaseModel

class AskRequest(BaseModel):

    question: str
    device_id: str | None = None

class AskResponse(BaseModel):

    answer: str
    confidence: float = 0.0
