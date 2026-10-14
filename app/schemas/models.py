from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class AskRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    question: str = Field(min_length=1, max_length=2000)
    device_id: str | None = None

class StepItem(BaseModel):
    description: str = Field(min_length=1)
    basis: str = Field(min_length=1)  # 依据溯源：手册章节/报警码

class RiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class AskResponse(BaseModel):
    answer: str                          # 摘要（一句话）
    steps: list[StepItem] = []           # 排查步骤
    risk_level: RiskLevel = RiskLevel.LOW
    needs_human_review: bool = False     # 是否需人工确认
    confidence: float = 0.0
