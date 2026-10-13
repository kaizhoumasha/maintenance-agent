from enum import StrEnum

from pydantic import BaseModel


class ErrorCode(StrEnum):
    INVALID_REQUEST = "INVALID_REQUEST"
    MODEL_TIMEOUT = "MODEL_TIMEOUT"
    UPSTREAM_ERROR = "UPSTREAM_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"


HTTP_STATUS: dict[ErrorCode, int] = {
    ErrorCode.INVALID_REQUEST: 400,
    ErrorCode.UPSTREAM_ERROR: 502,
    ErrorCode.MODEL_TIMEOUT: 504,
    ErrorCode.INTERNAL_ERROR: 500,
}


class ErrorResponse(BaseModel):
    trace_id: str
    code: ErrorCode
    message: str
    detail: str | None


class AppError(Exception):
    code: ErrorCode
    message: str
    detail: str | None
    def __init__(self, code: ErrorCode, message: str, detail: str | None = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.detail = detail
