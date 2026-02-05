"""
速率限制中间件

使用slowapi实现API速率限制，防止滥用和保护系统资源。
支持不同端点的差异化限制规则。
"""
import logging
from typing import Callable

from fastapi import Request, status
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.config import settings
from app.core.security import ACCESS_TOKEN_TYPE, verify_token
from app.utils.client_ip import get_client_ip

logger = logging.getLogger(__name__)


def get_user_identifier(request: Request) -> str:
    """
    获取用户标识符用于速率限制

    优先使用已认证用户的ID，否则使用IP地址

    Args:
        request: FastAPI请求对象

    Returns:
        用户标识符字符串
    """
    # 尝试从请求状态中获取用户ID（如果已认证）
    user = getattr(request.state, "user", None)
    if user and hasattr(user, "id"):
        return f"user:{user.id}"

    headers = getattr(request, "headers", None)
    auth_header = headers.get("Authorization") if headers else None
    if isinstance(auth_header, str) and auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1].strip()
        if token:
            try:
                payload = verify_token(token, token_type=ACCESS_TOKEN_TYPE)
                if payload and payload.get("sub"):
                    return f"user:{int(payload['sub'])}"
            except Exception:
                pass

    # 否则使用IP地址
    client_ip = get_client_ip(request)
    if client_ip:
        return client_ip
    return get_remote_address(request)


# 创建Limiter实例
limiter = Limiter(
    key_func=get_user_identifier,
    default_limits=[f"{settings.rate_limit.rate_limit_per_minute}/minute"],
    storage_uri=settings.redis.redis_url,
    strategy="fixed-window",
    headers_enabled=False,
)


def get_rate_limit_string(limit_type: str) -> str:
    """
    根据限制类型获取速率限制字符串

    Args:
        limit_type: 限制类型 (login, api, llm)

    Returns:
        速率限制字符串，格式如 "5/minute"
    """
    if limit_type == "login":
        return f"{settings.rate_limit.rate_limit_login_per_minute}/minute"
    elif limit_type == "llm":
        return f"{settings.rate_limit.rate_limit_llm_per_minute}/minute"
    else:  # default api
        return f"{settings.rate_limit.rate_limit_per_minute}/minute"


# 预定义的速率限制装饰器
def rate_limit_login() -> Callable:
    """
    登录接口速率限制装饰器

    Returns:
        装饰器函数
    """
    limit_string = get_rate_limit_string("login")
    return limiter.limit(limit_string)


def rate_limit_api() -> Callable:
    """
    普通API接口速率限制装饰器

    Returns:
        装饰器函数
    """
    limit_string = get_rate_limit_string("api")
    return limiter.limit(limit_string)


def rate_limit_llm() -> Callable:
    """
    LLM调用接口速率限制装饰器

    Returns:
        装饰器函数
    """
    limit_string = get_rate_limit_string("llm")
    return limiter.limit(limit_string)


def rate_limit_custom(limit: str) -> Callable:
    """
    自定义速率限制装饰器

    Args:
        limit: 速率限制字符串，如 "10/minute", "100/hour"

    Returns:
        装饰器函数
    """
    return limiter.limit(limit)


async def rate_limit_exceeded_handler(
    request: Request, exc: RateLimitExceeded
) -> JSONResponse:
    """
    速率限制超出处理器

    Args:
        request: FastAPI请求对象
        exc: 速率限制异常

    Returns:
        错误响应字典
    """
    request_id = getattr(request.state, "request_id", None)
    user_identifier = get_user_identifier(request)

    # 记录速率限制事件
    logger.warning(
        f"Rate limit exceeded: {user_identifier} "
        f"[request_id={request_id}, path={request.url.path}]"
    )

    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "error_code": "4003",
            "message": "请求过于频繁，请稍后再试",
            "status_code": status.HTTP_429_TOO_MANY_REQUESTS,
            "details": {"retry_after": exc.detail},
            "request_id": request_id,
        },
    )


def register_rate_limiter(app):
    """
    注册速率限制器到FastAPI应用

    Args:
        app: FastAPI应用实例
    """
    # 将limiter状态添加到应用
    app.state.limiter = limiter

    # 注册速率限制异常处理器
    app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

    logger.info(
        f"速率限制器已注册 - "
        f"登录: {settings.rate_limit.rate_limit_login_per_minute}/min, "
        f"API: {settings.rate_limit.rate_limit_per_minute}/min, "
        f"LLM: {settings.rate_limit.rate_limit_llm_per_minute}/min"
    )


# 导出常用功能
__all__ = [
    "limiter",
    "rate_limit_login",
    "rate_limit_api",
    "rate_limit_llm",
    "rate_limit_custom",
    "rate_limit_exceeded_handler",
    "register_rate_limiter",
    "get_user_identifier",
]
