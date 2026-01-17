"""
中间件模块

提供各种中间件功能，包括错误处理、速率限制、请求ID生成等。
"""

from .error_handler import (
    AppException,
    ErrorCode,
    app_exception_handler,
    http_exception_handler,
    validation_exception_handler,
    general_exception_handler,
    register_exception_handlers,
)

from .rate_limiter import (
    limiter,
    rate_limit_login,
    rate_limit_api,
    rate_limit_llm,
    rate_limit_custom,
    rate_limit_exceeded_handler,
    register_rate_limiter,
    get_user_identifier,
)

from .request_id import (
    RequestIDMiddleware,
    register_request_id_middleware,
)

__all__ = [
    # Error handling
    "AppException",
    "ErrorCode",
    "app_exception_handler",
    "http_exception_handler",
    "validation_exception_handler",
    "general_exception_handler",
    "register_exception_handlers",
    # Rate limiting
    "limiter",
    "rate_limit_login",
    "rate_limit_api",
    "rate_limit_llm",
    "rate_limit_custom",
    "rate_limit_exceeded_handler",
    "register_rate_limiter",
    "get_user_identifier",
    # Request ID
    "RequestIDMiddleware",
    "register_request_id_middleware",
]

