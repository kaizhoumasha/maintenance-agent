"""
错误处理模块

提供统一的错误码定义、HTTP状态码映射、错误响应模型和自定义异常类。
"""

from enum import StrEnum

from pydantic import BaseModel


class ErrorCode(StrEnum):
    """
    错误码枚举类

    定义了系统中可能使用的所有错误码，用于标识不同类型的错误情况。

    Attributes:
        INVALID_REQUEST: 无效请求
        NOT_FOUND: 资源未找到
        METHOD_NOT_ALLOWED: 请求方法不允许
        MODEL_TIMEOUT: 模型调用超时
        UPSTREAM_ERROR: 上游服务错误
        INTERNAL_ERROR: 内部错误
    """
    INVALID_REQUEST = "INVALID_REQUEST"
    NOT_FOUND = "NOT_FOUND"
    METHOD_NOT_ALLOWED = "METHOD_NOT_ALLOWED"
    MODEL_TIMEOUT = "MODEL_TIMEOUT"
    UPSTREAM_ERROR = "UPSTREAM_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"


# 错误码到HTTP状态码的映射表
HTTP_STATUS: dict[ErrorCode, int] = {
    ErrorCode.INVALID_REQUEST: 400,
    ErrorCode.NOT_FOUND: 404,
    ErrorCode.METHOD_NOT_ALLOWED: 405,
    ErrorCode.UPSTREAM_ERROR: 502,
    ErrorCode.MODEL_TIMEOUT: 504,
    ErrorCode.INTERNAL_ERROR: 500,
}


class ErrorResponse(BaseModel):
    """
    错误响应模型

    用于标准化API错误响应的数据结构。

    Attributes:
        trace_id: 请求追踪ID，用于日志关联和问题排查
        code: 错误码，对应ErrorCode枚举值
        message: 错误信息，对用户友好的错误描述
        detail: 错误详情，可选的额外错误信息（如调试信息）
    """
    trace_id: str
    code: ErrorCode
    message: str
    detail: str | None


class AppError(Exception):
    """
    应用自定义异常类

    用于在应用内部抛出带有错误码和详细信息的异常。

    Attributes:
        code: 错误码，标识错误类型
        message: 错误信息，描述错误原因
        detail: 错误详情，可选的额外错误信息

    Args:
        code: 错误码，使用ErrorCode枚举值
        message: 错误信息字符串
        detail: 可选的错误详情，默认为None
    """
    code: ErrorCode
    message: str
    detail: str | None

    def __init__(self, code: ErrorCode, message: str, detail: str | None = None) -> None:
        """
        初始化AppError实例

        Args:
            code: 错误码，使用ErrorCode枚举值
            message: 错误信息字符串
            detail: 可选的错误详情，默认为None
        """
        super().__init__(message)
        self.code = code
        self.message = message
        self.detail = detail
